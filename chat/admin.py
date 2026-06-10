from django.contrib import admin

from .models import ChatMessage, ChatSession, RecommendedQuestion, RetrievedSource

admin.site.register(ChatSession)
admin.site.register(ChatMessage)
admin.site.register(RetrievedSource)
admin.site.register(RecommendedQuestion)
