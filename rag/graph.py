"""LangGraph RAG workflow for Soul Questions.

Graph nodes:
  1. query_understanding  — detect game, category, decide if rewrite needed
  2. query_rewrite        — rewrite for better retrieval (conditional)
  3. retrieve             — vector search
  4. rerank               — keyword + semantic reranking
  5. generate_answer      — LLM answer with citations
  6. format_citations     — extract cited sources
  7. recommend_followups  — suggest next questions
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from .citations import extract_cited_sources, format_context_for_prompt
from .prompts import CONTEXT_TEMPLATE, QUERY_REWRITE_PROMPT, SYSTEM_PROMPT
from .reranker import rerank
from .retriever import Retriever

logger = logging.getLogger(__name__)

# Game-detection patterns
GAME_PATTERNS: dict[str, list[str]] = {
    "Dark Souls": ["dark souls 1", "dark souls", "ds1", "lordran"],
    "Dark Souls 2": ["dark souls 2", "ds2", "drangleic", "scholar of the first sin"],
    "Dark Souls 3": ["dark souls 3", "ds3", "lothric", "ringed city"],
    "Elden Ring": ["elden ring", "lands between", "tarnished", "erdtree"],
    "Elden Ring: Nightreign": ["nightreign", "elden ring nightreign"],
    "Bloodborne": ["bloodborne", "yharnam", "hunter"],
    "Sekiro": ["sekiro", "ashina", "shinobi"],
    "Demon's Souls": ["demon's souls", "demons souls", "boletaria"],
}


class GraphState(TypedDict, total=False):
    """State passed through the LangGraph pipeline."""

    question: str
    history: list[dict]
    detected_game: str
    detected_category: str
    needs_rewrite: bool
    search_query: str
    retrieved_chunks: list[dict]
    reranked_chunks: list[dict]
    context: str
    answer: str
    cited_sources: list[dict]
    recommendations: list[str]
    llm_config: dict[str, str]


def _get_llm(config: dict[str, str] | None = None) -> Any:
    """Instantiate LLM from user config or environment defaults."""
    provider = (config or {}).get("provider") or os.getenv("LLM_PROVIDER", "openai")
    model = (config or {}).get("model") or os.getenv("LLM_MODEL", "gpt-4o-mini")
    api_key = (config or {}).get("api_key") or os.getenv("OPENAI_API_KEY", "")

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model,
            temperature=0.3,
            api_key=api_key,
        )
    elif provider == "ollama":
        from langchain_community.chat_models import ChatOllama

        return ChatOllama(
            model=model,
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        )
    raise ValueError(f"Unknown LLM provider: {provider}")


# ---------------------------------------------------------------------------
# Graph nodes
# ---------------------------------------------------------------------------


def query_understanding(state: GraphState) -> GraphState:
    """Detect game context and whether query rewrite is needed."""
    question = state["question"].lower()
    history = state.get("history", [])

    detected_game = ""
    for game, patterns in GAME_PATTERNS.items():
        for pattern in patterns:
            if pattern in question:
                detected_game = game
                break
        if detected_game:
            break

    # If no game detected, check recent history
    if not detected_game and history:
        for msg in reversed(history[-6:]):
            text = msg.get("content", "").lower()
            for game, patterns in GAME_PATTERNS.items():
                if any(p in text for p in patterns):
                    detected_game = game
                    break
            if detected_game:
                break

    # Decide if rewrite is needed based on conversation context
    needs_rewrite = bool(history) and len(question.split()) < 15

    return {
        **state,
        "detected_game": detected_game,
        "needs_rewrite": needs_rewrite,
        "search_query": state["question"],
    }


def query_rewrite(state: GraphState) -> GraphState:
    """Rewrite the query for better retrieval using conversation context."""
    history = state.get("history", [])
    if not history:
        return state

    history_text = "\n".join(
        f"{m['role']}: {m['content']}" for m in history[-6:]
    )

    try:
        llm = _get_llm(state.get("llm_config"))
        prompt = QUERY_REWRITE_PROMPT.format(
            history=history_text, question=state["question"]
        )
        response = llm.invoke(prompt)
        rewritten = response.content if hasattr(response, "content") else str(response)
        rewritten = rewritten.strip()
        if rewritten and len(rewritten) > 5:
            return {**state, "search_query": rewritten}
    except Exception as exc:
        logger.warning("Query rewrite failed: %s", exc)

    return state


def retrieve(state: GraphState) -> GraphState:
    """Retrieve relevant chunks from the vector store."""
    retriever = Retriever()
    game_filter = state.get("detected_game") or None
    chunks = retriever.retrieve(
        state["search_query"], top_k=10, game_filter=game_filter
    )
    return {**state, "retrieved_chunks": chunks}


def rerank_node(state: GraphState) -> GraphState:
    """Rerank retrieved chunks."""
    chunks = state.get("retrieved_chunks", [])
    reranked = rerank(state["search_query"], chunks, top_k=5)
    return {**state, "reranked_chunks": reranked}


def generate_answer(state: GraphState) -> GraphState:
    """Generate the final answer using retrieved context."""
    chunks = state.get("reranked_chunks", [])
    context_str = format_context_for_prompt(chunks)

    history = state.get("history", [])
    history_text = "\n".join(
        f"{m['role']}: {m['content']}" for m in history[-6:]
    ) if history else "(No previous messages)"

    user_prompt = CONTEXT_TEMPLATE.format(
        context=context_str,
        history=history_text,
        question=state["question"],
    )

    try:
        llm = _get_llm(state.get("llm_config"))
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
        response = llm.invoke(messages)
        answer = response.content if hasattr(response, "content") else str(response)
    except Exception as exc:
        logger.error("LLM generation failed: %s", exc)
        answer = (
            "I'm sorry, I encountered an error generating a response. "
            "Please check that your LLM provider is configured correctly."
        )

    return {**state, "answer": answer, "context": context_str}


def format_citations(state: GraphState) -> GraphState:
    """Extract cited sources from the answer."""
    chunks = state.get("reranked_chunks", [])
    answer = state.get("answer", "")
    cited = extract_cited_sources(answer, chunks)
    return {**state, "cited_sources": cited}


def recommend_followups(state: GraphState) -> GraphState:
    """Generate recommended follow-up questions."""
    from .recommendations import generate_recommendations

    recs = generate_recommendations(
        question=state["question"],
        answer=state.get("answer", ""),
        game=state.get("detected_game", ""),
        llm_config=state.get("llm_config"),
    )
    return {**state, "recommendations": recs}


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------


def should_rewrite(state: GraphState) -> str:
    """Decide whether to rewrite the query."""
    if state.get("needs_rewrite", False):
        return "rewrite"
    return "skip"


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------


def build_graph() -> StateGraph:
    """Build the LangGraph RAG pipeline."""
    graph = StateGraph(GraphState)

    graph.add_node("query_understanding", query_understanding)
    graph.add_node("query_rewrite", query_rewrite)
    graph.add_node("retrieve", retrieve)
    graph.add_node("rerank", rerank_node)
    graph.add_node("generate_answer", generate_answer)
    graph.add_node("format_citations", format_citations)
    graph.add_node("recommend_followups", recommend_followups)

    graph.set_entry_point("query_understanding")

    graph.add_conditional_edges(
        "query_understanding",
        should_rewrite,
        {"rewrite": "query_rewrite", "skip": "retrieve"},
    )
    graph.add_edge("query_rewrite", "retrieve")
    graph.add_edge("retrieve", "rerank")
    graph.add_edge("rerank", "generate_answer")
    graph.add_edge("generate_answer", "format_citations")
    graph.add_edge("format_citations", "recommend_followups")
    graph.add_edge("recommend_followups", END)

    return graph.compile()


# Singleton for reuse
_compiled_graph = None


def get_graph():
    """Return a compiled graph instance (cached)."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph
