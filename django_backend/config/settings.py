"""
Django settings for the Credit Card Payment System.

Configuration is environment-driven throughout so the same codebase runs
unchanged in docker-compose (MySQL) and in a local dev/test shell (you can
point DB_ENGINE at sqlite3 for a quick local test run without a MySQL
server — see README "Running tests without Docker").
"""

import os
import sys
from datetime import timedelta
from pathlib import Path

# True during `manage.py test` / pytest runs. Used below to turn off
# request throttling for the test run only — the throttle cache is
# process-global, so without this, unrelated test classes later in a long
# suite start getting real 429s from earlier tests' requests, which is a
# test-environment artifact, not a security property under test.
TESTING = "test" in sys.argv or os.environ.get("DJANGO_TESTING") == "True"

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-insecure-secret-key-change-me")
DEBUG = os.environ.get("DJANGO_DEBUG", "True") == "True"

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# Both dev servers, by default, so the browser doesn't get blocked by CORS
# during local development. Add your deployed frontend origin in production.
CORS_ALLOWED_ORIGINS = os.environ.get(
    "CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
).split(",")
CORS_ALLOW_CREDENTIALS = True

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    # Local apps
    "accounts",
    "cards",
    "transactions",
    "adminpanel",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

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

WSGI_APPLICATION = "config.wsgi.application"

# --- Database -----------------------------------------------------------
# Defaults match the docker-compose MySQL service. Override DB_ENGINE to
# "django.db.backends.sqlite3" for a quick local test run with no MySQL
# server available (see README).
DATABASES = {
    "default": {
        "ENGINE": os.environ.get("DB_ENGINE", "django.db.backends.mysql"),
        "NAME": os.environ.get("DB_NAME", "ccps_db"),
        "USER": os.environ.get("DB_USER", "ccps_user"),
        "PASSWORD": os.environ.get("DB_PASSWORD", "ccps_password"),
        "HOST": os.environ.get("DB_HOST", "mysql"),
        "PORT": os.environ.get("DB_PORT", "3306"),
        "OPTIONS": (
            {"init_command": "SET sql_mode='STRICT_TRANS_TABLES'"}
            if os.environ.get("DB_ENGINE", "django.db.backends.mysql") == "django.db.backends.mysql"
            else {}
        ),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- DRF / JWT ------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [] if TESTING else [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "20/minute",
        "user": "120/minute",
    },
}

# JWT_SHARED_SECRET is what FastAPI uses to verify these same tokens — see
# fastapi_backend/auth.py. Keeping it as its own env var (rather than
# reusing DJANGO_SECRET_KEY for everything) makes the trust boundary
# between the two services explicit and independently rotatable.
JWT_SHARED_SECRET = os.environ.get("JWT_SHARED_SECRET", "dev-insecure-jwt-shared-secret-change-me")

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.environ.get("ACCESS_TOKEN_LIFETIME_MIN", "30"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.environ.get("REFRESH_TOKEN_LIFETIME_DAYS", "7"))),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": JWT_SHARED_SECRET,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_CLAIM": "user_id",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Credit Card Payment System — Django API",
    "DESCRIPTION": "Auth, card management, transaction history, and admin endpoints.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# Demo admin seed (see accounts/management/commands/create_demo_admin.py).
# Change this immediately for anything beyond local evaluation.
DEMO_ADMIN_USERNAME = os.environ.get("DEMO_ADMIN_USERNAME", "admin")
DEMO_ADMIN_EMAIL = os.environ.get("DEMO_ADMIN_EMAIL", "admin@example.com")
DEMO_ADMIN_PASSWORD = os.environ.get("DEMO_ADMIN_PASSWORD", "StrongPass123!")
