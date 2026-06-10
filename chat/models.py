"""Database models for Soul Questions chat sessions."""

from django.db import models


class ChatSession(models.Model):
    """A conversation session between the user and the assistant."""

    title = models.CharField(max_length=255, default="New Chat")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return f"{self.title} ({self.id})"


class ChatMessage(models.Model):
    """A single message in a chat session."""

    ROLE_CHOICES = [
        ("user", "User"),
        ("assistant", "Assistant"),
    ]

    session = models.ForeignKey(
        ChatSession, on_delete=models.CASCADE, related_name="messages"
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"[{self.role}] {self.content[:80]}"


class RetrievedSource(models.Model):
    """A source document retrieved for a particular assistant message."""

    message = models.ForeignKey(
        ChatMessage, on_delete=models.CASCADE, related_name="sources"
    )
    title = models.CharField(max_length=500, blank=True, default="")
    url = models.URLField(max_length=1000, blank=True, default="")
    game = models.CharField(max_length=100, blank=True, default="")
    category = models.CharField(max_length=100, blank=True, default="")
    snippet = models.TextField(blank=True, default="")
    relevance_score = models.FloatField(default=0.0)

    class Meta:
        ordering = ["-relevance_score"]

    def __str__(self) -> str:
        return f"{self.title} ({self.game})"


class RecommendedQuestion(models.Model):
    """A follow-up question recommended after an assistant response."""

    message = models.ForeignKey(
        ChatMessage, on_delete=models.CASCADE, related_name="recommendations"
    )
    text = models.CharField(max_length=500)

    def __str__(self) -> str:
        return self.text
