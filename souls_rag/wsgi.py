"""WSGI config for Soul Questions."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "souls_rag.settings")
application = get_wsgi_application()
