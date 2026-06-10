"""URL patterns for the chat app."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("new/", views.new_session, name="new_session"),
    path("session/<int:session_id>/", views.chat_session, name="chat_session"),
    path(
        "session/<int:session_id>/send/",
        views.send_message,
        name="send_message",
    ),
    path(
        "session/<int:session_id>/rename/",
        views.rename_session,
        name="rename_session",
    ),
    path(
        "session/<int:session_id>/delete/",
        views.delete_session,
        name="delete_session",
    ),
    path("settings/save/", views.save_settings, name="save_settings"),
    path("settings/", views.get_settings, name="get_settings"),
]
