"""Views for the Soul Questions chat application."""

from __future__ import annotations

import json

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from .models import ChatMessage, ChatSession, RecommendedQuestion, RetrievedSource
from .services import ask_question

ALLOWED_MODELS = {
    "gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo", "o3-mini",
}

DEFAULT_SETTINGS = {
    "llm_model": "gpt-4o-mini",
    "api_key": "",
}


def index(request):
    """Landing page — redirect to most recent session or create new."""
    session = ChatSession.objects.first()
    if session:
        return redirect("chat_session", session_id=session.pk)
    return redirect("new_session")


def new_session(request):
    """Create a new chat session and redirect to it."""
    session = ChatSession.objects.create()
    return redirect("chat_session", session_id=session.pk)


def chat_session(request, session_id: int):
    """Render the chat interface for a session."""
    session = get_object_or_404(ChatSession, pk=session_id)
    sessions = ChatSession.objects.all()[:50]

    messages = session.messages.order_by("created_at")
    message_data = []
    for msg in messages:
        sources = list(
            msg.sources.values("title", "url", "game", "category", "snippet")
        ) if msg.role == "assistant" else []
        recommendations = list(
            msg.recommendations.values_list("text", flat=True)
        ) if msg.role == "assistant" else []
        message_data.append({
            "id": msg.pk,
            "role": msg.role,
            "content": msg.content,
            "sources": sources,
            "recommendations": recommendations,
        })

    return render(request, "chat/index.html", {
        "session": session,
        "sessions": sessions,
        "messages": message_data,
    })


@require_POST
def send_message(request, session_id: int):
    """Handle a new user message via AJAX."""
    session = get_object_or_404(ChatSession, pk=session_id)

    try:
        body = json.loads(request.body)
        user_message = body.get("message", "").strip()
    except (json.JSONDecodeError, AttributeError):
        user_message = request.POST.get("message", "").strip()

    if not user_message:
        return JsonResponse({"error": "Empty message"}, status=400)

    # Pass user's LLM settings if configured
    user_settings = request.session.get("llm_settings", {})
    llm_config = None
    if user_settings.get("api_key"):
        llm_config = {
            "model": user_settings.get("llm_model", "gpt-4o-mini"),
            "api_key": user_settings["api_key"],
        }

    result = ask_question(session, user_message, llm_config=llm_config)

    return JsonResponse({
        "answer": result["answer"],
        "sources": result["sources"],
        "recommendations": result["recommendations"],
        "session_title": session.title,
    })


@require_POST
def rename_session(request, session_id: int):
    """Rename a chat session."""
    session = get_object_or_404(ChatSession, pk=session_id)
    try:
        body = json.loads(request.body)
        new_title = body.get("title", "").strip()
    except (json.JSONDecodeError, AttributeError):
        new_title = request.POST.get("title", "").strip()

    if new_title:
        session.title = new_title[:255]
        session.save()
        return JsonResponse({"title": session.title})
    return JsonResponse({"error": "Empty title"}, status=400)


@require_POST
def delete_session(request, session_id: int):
    """Delete a chat session."""
    session = get_object_or_404(ChatSession, pk=session_id)
    session.delete()
    return JsonResponse({"deleted": True})


@require_POST
def save_settings(request):
    """Save user LLM settings to the Django session."""
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    model = body.get("llm_model", "gpt-4o-mini")
    if model not in ALLOWED_MODELS:
        return JsonResponse({"error": f"Model '{model}' is not allowed"}, status=400)

    existing = request.session.get("llm_settings", {})
    settings = {
        "llm_model": model,
        "api_key": body.get("api_key", existing.get("api_key", "")) if "api_key" in body else existing.get("api_key", ""),
    }
    request.session["llm_settings"] = settings
    return JsonResponse({"saved": True})


def get_settings(request):
    """Return current user LLM settings (API key masked)."""
    settings = request.session.get("llm_settings", DEFAULT_SETTINGS)
    api_key = settings.get("api_key", "")
    masked = ""
    if api_key:
        masked = api_key[:4] + "*" * max(0, len(api_key) - 8) + api_key[-4:] if len(api_key) > 8 else "****"
    return JsonResponse({
        "llm_model": settings.get("llm_model", "gpt-4o-mini"),
        "api_key_set": bool(api_key),
        "api_key_masked": masked,
    })
