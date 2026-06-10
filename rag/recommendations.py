"""Generate follow-up question recommendations."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from .prompts import RECOMMENDATION_PROMPT

logger = logging.getLogger(__name__)


def get_llm(config: dict[str, str] | None = None) -> Any:
    """Instantiate the configured LLM client."""
    from langchain_openai import ChatOpenAI

    model = (config or {}).get("model") or os.getenv("LLM_MODEL", "gpt-4o-mini")
    api_key = (config or {}).get("api_key") or os.getenv("OPENAI_API_KEY", "")

    return ChatOpenAI(
        model=model,
        temperature=0.7,
        api_key=api_key,
    )


def generate_recommendations(
    question: str,
    answer: str,
    game: str = "",
    llm_config: dict[str, str] | None = None,
) -> list[str]:
    """Generate 3-5 follow-up question recommendations.

    Args:
        question: The user's current question.
        answer: The assistant's response.
        game: The detected game context.
        llm_config: Optional user-provided LLM configuration.

    Returns:
        List of recommended follow-up question strings.
    """
    try:
        llm = get_llm(llm_config)
        prompt = RECOMMENDATION_PROMPT.format(
            question=question,
            answer=answer[:1000],
            game=game or "General Souls-like games",
        )
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)

        # Parse JSON array from response
        # Handle cases where LLM wraps in markdown code block
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

        recommendations = json.loads(content)
        if isinstance(recommendations, list):
            return [str(q) for q in recommendations[:5]]
    except Exception as exc:
        logger.warning("Failed to generate recommendations: %s", exc)

    return _fallback_recommendations(question, game)


def _fallback_recommendations(question: str, game: str) -> list[str]:
    """Return generic follow-up questions when LLM generation fails."""
    game_label = game or "this game"
    return [
        f"What are the hardest bosses in {game_label}?",
        f"What are the best builds for beginners in {game_label}?",
        f"Can you explain the lore behind {game_label}?",
        "How does this compare to other Souls-like games?",
        "What items should I collect before this boss fight?",
    ]
