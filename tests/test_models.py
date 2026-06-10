"""Tests for Django chat models."""

import pytest

from chat.models import ChatMessage, ChatSession, RecommendedQuestion, RetrievedSource


@pytest.mark.django_db
def test_create_session():
    session = ChatSession.objects.create(title="Test Session")
    assert session.pk is not None
    assert session.title == "Test Session"
    assert str(session) == f"Test Session ({session.pk})"


@pytest.mark.django_db
def test_create_messages():
    session = ChatSession.objects.create()
    user_msg = ChatMessage.objects.create(session=session, role="user", content="Hello")
    asst_msg = ChatMessage.objects.create(session=session, role="assistant", content="Hi there")
    assert session.messages.count() == 2
    assert user_msg.role == "user"
    assert asst_msg.role == "assistant"


@pytest.mark.django_db
def test_retrieved_source():
    session = ChatSession.objects.create()
    msg = ChatMessage.objects.create(session=session, role="assistant", content="answer")
    source = RetrievedSource.objects.create(
        message=msg,
        title="Sif",
        url="http://example.com/sif",
        game="Dark Souls",
        category="boss",
        snippet="Great Grey Wolf Sif",
        relevance_score=0.95,
    )
    assert msg.sources.count() == 1
    assert source.game == "Dark Souls"


@pytest.mark.django_db
def test_recommended_question():
    session = ChatSession.objects.create()
    msg = ChatMessage.objects.create(session=session, role="assistant", content="answer")
    rec = RecommendedQuestion.objects.create(message=msg, text="What about the lore?")
    assert msg.recommendations.count() == 1
    assert str(rec) == "What about the lore?"


@pytest.mark.django_db
def test_session_ordering():
    s1 = ChatSession.objects.create(title="First")
    s2 = ChatSession.objects.create(title="Second")
    sessions = list(ChatSession.objects.all())
    # Most recently updated first
    assert sessions[0].pk == s2.pk
