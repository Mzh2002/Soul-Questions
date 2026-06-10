"""Django settings for Soul Questions."""

import os
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, True),
    DJANGO_ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    CSRF_TRUSTED_ORIGINS=(list, []),
    DATABASE_URL=(str, ""),
    LLM_PROVIDER=(str, "openai"),
    LLM_MODEL=(str, "gpt-4o-mini"),
    EMBEDDING_PROVIDER=(str, "sentence-transformers"),
    EMBEDDING_MODEL=(str, "all-MiniLM-L6-v2"),
    VECTOR_STORE=(str, "chroma"),
    DATA_RAW_DIR=(str, "data/raw"),
    DATA_PROCESSED_DIR=(str, "data/processed"),
    DATA_CHUNKS_DIR=(str, "data/chunks"),
    VECTORSTORE_DIR=(str, "data/vectorstore"),
)

env_file = BASE_DIR / ".env"
if env_file.exists():
    env.read_env(str(env_file))

SECRET_KEY = env("DJANGO_SECRET_KEY", default="insecure-dev-key-change-me")
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "chat",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "souls_rag.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "souls_rag.wsgi.application"

_db_url = env("DATABASE_URL")
if _db_url:
    DATABASES = {"default": env.db()}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage.CompressedManifestStaticFilesStorage"
            if not DEBUG
            else "django.contrib.staticfiles.storage.StaticFilesStorage"
        ),
    },
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Soul Questions Config ---
LLM_PROVIDER = env("LLM_PROVIDER")
LLM_MODEL = env("LLM_MODEL")
OPENAI_API_KEY = env("OPENAI_API_KEY", default="")

EMBEDDING_PROVIDER = env("EMBEDDING_PROVIDER")
EMBEDDING_MODEL = env("EMBEDDING_MODEL")
VECTOR_STORE = env("VECTOR_STORE")

DATA_RAW_DIR = BASE_DIR / env("DATA_RAW_DIR")
DATA_PROCESSED_DIR = BASE_DIR / env("DATA_PROCESSED_DIR")
DATA_CHUNKS_DIR = BASE_DIR / env("DATA_CHUNKS_DIR")
VECTORSTORE_DIR = BASE_DIR / env("VECTORSTORE_DIR")
