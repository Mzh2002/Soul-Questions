"""Pytest configuration for Soul Questions tests."""

import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "souls_rag.settings")
django.setup()
