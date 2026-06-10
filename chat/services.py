"""Service layer: bridge between Django views and the RAG pipeline."""

from __future__ import annotations

import logging
from typing import Any

from .models import ChatMessage, ChatSession, RecommendedQuestion, RetrievedSource

logger = logging.getLogger(__name__)


def ask_question(
    session: ChatSession,
    user_message: str,
    llm_config: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Process a user question through the RAG pipeline.

    Args:
        session: The active ChatSession.
        user_message: The user's question text.
        llm_config: Optional dict with provider/model/api_key overrides.

    Returns:
        Dict with keys: answer, sources, recommendations, assistant_message.
    """
    # Save user message
    user_msg = ChatMessage.objects.create(
        session=session, role="user", content=user_message
    )

    # Build conversation history from previous messages
    history: list[dict[str, str]] = []
    for msg in session.messages.order_by("created_at").exclude(pk=user_msg.pk):
        history.append({"role": msg.role, "content": msg.content})

    # Run RAG pipeline
    try:
        from rag.graph import get_graph

        graph = get_graph()
        invoke_state: dict[str, Any] = {
            "question": user_message,
            "history": history,
        }
        if llm_config:
            invoke_state["llm_config"] = llm_config
        result = graph.invoke(invoke_state)

        answer = result.get("answer", "I'm not sure how to answer that.")
        cited_sources = result.get("cited_sources", [])
        recommendations = result.get("recommendations", [])
        detected_game = result.get("detected_game", "")
    except Exception as exc:
        logger.error("RAG pipeline error: %s", exc)
        answer = (
            "I encountered an error processing your question. "
            "Please ensure the vector index has been built and the LLM is configured."
        )
        cited_sources = []
        recommendations = []
        detected_game = ""

    # Save assistant message
    assistant_msg = ChatMessage.objects.create(
        session=session, role="assistant", content=answer
    )

    # Save sources
    source_objects = []
    for src in cited_sources:
        source_objects.append(
            RetrievedSource.objects.create(
                message=assistant_msg,
                title=src.get("title", ""),
                url=src.get("url", ""),
                game=src.get("game", ""),
                category=src.get("category", ""),
                snippet=src.get("snippet", ""),
                relevance_score=src.get("score", 0.0),
            )
        )

    # Save recommendations
    rec_objects = []
    for rec in recommendations:
        rec_objects.append(
            RecommendedQuestion.objects.create(message=assistant_msg, text=rec)
        )

    # Auto-title session if it's the first exchange
    if session.messages.count() <= 2 and session.title == "New Chat":
        title = user_message[:60]
        if len(user_message) > 60:
            title += "..."
        if detected_game:
            title = f"[{detected_game}] {title}"
        session.title = title[:255]
        session.save()

    return {
        "answer": answer,
        "sources": cited_sources,
        "recommendations": recommendations,
        "assistant_message": assistant_msg,
    }
