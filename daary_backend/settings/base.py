"""
Daary AI Backend — Base Settings
=================================
Shared settings for all environments (dev, prod, test).
Environment-specific files import everything from here and override as needed.
"""
import os
from datetime import timedelta
from pathlib import Path

import environ

# ─── Paths ────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ─── Environment ──────────────────────────────────────────────────
env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    CORS_ALLOWED_ORIGINS=(list, ["http://localhost:5173"]),
    CSRF_TRUSTED_ORIGINS=(list, []),
    LOG_LEVEL=(str, "INFO"),
    JWT_ACCESS_TOKEN_LIFETIME_MINUTES=(int, 15),
    JWT_REFRESH_TOKEN_LIFETIME_DAYS=(int, 7),
    SMS_BACKEND=(str, "console"),
)

# Read .env file if it exists
env_file = BASE_DIR / ".env"
if env_file.is_file():
    environ.Env.read_env(str(env_file))

# ─── Core ─────────────────────────────────────────────────────────
SECRET_KEY = env("SECRET_KEY", default="insecure-dev-key-change-me")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# ─── Application Definition ──────────────────────────────────────
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework.authtoken",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_celery_beat",
    "drf_spectacular",
]

LOCAL_APPS = [
    "apps.users",
    "apps.authentication",
    "apps.properties",
    "apps.search",
    "apps.ai",
    "apps.favorites",
    "apps.inquiries",
    "apps.developer_accounts",
    "apps.locations",
    "apps.projects",
    "apps.marketing",
    "apps.dashboard",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ─── Custom User Model ───────────────────────────────────────────
AUTH_USER_MODEL = "users.User"

# ─── Middleware ───────────────────────────────────────────────────
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# ─── URL & WSGI ──────────────────────────────────────────────────
ROOT_URLCONF = "daary_backend.urls"
WSGI_APPLICATION = "daary_backend.wsgi.application"

# ─── Templates ────────────────────────────────────────────────────
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

# ─── Database ─────────────────────────────────────────────────────
DATABASES = {
    "default": env.db("DATABASE_URL", default="sqlite:///db.sqlite3"),
}

# ─── Password Validation ─────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ─── Internationalization ────────────────────────────────────────
LANGUAGE_CODE = "ar"
TIME_ZONE = "Africa/Cairo"
USE_I18N = True
USE_TZ = True

# ─── Static Files ────────────────────────────────────────────────
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# ─── Media Files ─────────────────────────────────────────────────
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ─── Default PK ──────────────────────────────────────────────────
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ─── Django REST Framework ───────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.AllowAny",
    ),
    "DEFAULT_RENDERER_CLASSES": (
        "apps.common.renderers.ApiRenderer",
    ),
    "DEFAULT_PAGINATION_CLASS": "apps.common.pagination.StandardPagination",
    "PAGE_SIZE": 20,
    "EXCEPTION_HANDLER": "apps.common.exceptions.custom_exception_handler",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "otp": "10/minute",
        "anon": "60/minute",
        "platform_inquiry": "5/hour",
    },
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# ─── Simple JWT ──────────────────────────────────────────────────
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=env("JWT_ACCESS_TOKEN_LIFETIME_MINUTES"),
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=env("JWT_REFRESH_TOKEN_LIFETIME_DAYS"),
    ),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# ─── CORS ─────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = env("CORS_ALLOWED_ORIGINS")
CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS")
CORS_ALLOW_CREDENTIALS = True

# ─── Security ────────────────────────────────────────────────────
SECURE_SSL_REDIRECT = env("SECURE_SSL_REDIRECT", default=False)
SECURE_HSTS_SECONDS = env("SECURE_HSTS_SECONDS", default=0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False)
SECURE_HSTS_PRELOAD = env("SECURE_HSTS_PRELOAD", default=False)
SESSION_COOKIE_SECURE = env("SESSION_COOKIE_SECURE", default=False)
CSRF_COOKIE_SECURE = env("CSRF_COOKIE_SECURE", default=False)
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# Docker-friendly structured logger names; each category can be routed separately later.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "tagged": {"format": "[{levelname}] [{name}] {message}", "style": "{"},
    },
    "handlers": {
        "application": {"class": "logging.StreamHandler", "formatter": "tagged"},
        "security": {"class": "logging.StreamHandler", "formatter": "tagged"},
        "auth": {"class": "logging.StreamHandler", "formatter": "tagged"},
        "api": {"class": "logging.StreamHandler", "formatter": "tagged"},
        "error": {"class": "logging.StreamHandler", "formatter": "tagged"},
        "audit": {"class": "logging.StreamHandler", "formatter": "tagged"},
    },
    "loggers": {
        "apps": {"handlers": ["application"], "level": env("LOG_LEVEL"), "propagate": False},
        "apps.security": {"handlers": ["security"], "level": env("LOG_LEVEL"), "propagate": False},
        "apps.authentication": {"handlers": ["auth"], "level": env("LOG_LEVEL"), "propagate": False},
        "apps.api": {"handlers": ["api"], "level": env("LOG_LEVEL"), "propagate": False},
        "audit": {"handlers": ["audit"], "level": env("LOG_LEVEL"), "propagate": False},
        "django.request": {"handlers": ["error"], "level": "ERROR", "propagate": False},
        "django.security": {"handlers": ["security"], "level": "WARNING", "propagate": False},
    },
}

# ─── Celery ──────────────────────────────────────────────────────
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
NOTIFICATION_WEBHOOK_URL = env("NOTIFICATION_WEBHOOK_URL", default="")

# ─── drf-spectacular (OpenAPI / Swagger / ReDoc) ─────────────────
SPECTACULAR_SETTINGS = {
    "TITLE": "Daary AI Backend API",
    "DESCRIPTION": "API documentation for the Daary real estate platform.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# ─── SMS Configuration ───────────────────────────────────────────
SMS_BACKEND = env("SMS_BACKEND")  # 'console' | 'twilio' | 'cequens'
SMS_TWILIO_ACCOUNT_SID = env("SMS_TWILIO_ACCOUNT_SID", default="")
SMS_TWILIO_AUTH_TOKEN = env("SMS_TWILIO_AUTH_TOKEN", default="")
SMS_TWILIO_FROM_NUMBER = env("SMS_TWILIO_FROM_NUMBER", default="")

# ─── Akedly OTP Provider ────────────────────────────────────────
# Credentials from https://app.akedly.io — never hardcode in source.
AKEDLY_API_KEY = env("AKEDLY_API_KEY", default="")
AKEDLY_PIPELINE_ID = env("AKEDLY_PIPELINE_ID", default="")

# ─── AI Provider ─────────────────────────────────────────────────
AI_PROVIDER = env("AI_PROVIDER", default="openai")
AI_API_KEY = env("AI_API_KEY", default="")

# ─── OTP Settings ────────────────────────────────────────────────
OTP_LENGTH = 4
OTP_TTL_SECONDS = 300  # 5 minutes
OTP_MAX_ATTEMPTS = 3
OTP_RESEND_COOLDOWN_SECONDS = 60

# ─── AWS S3 Storage (production file uploads) ───────────────────
AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID", default="")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY", default="")
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME", default="")
AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", default="me-south-1")
AWS_S3_CUSTOM_DOMAIN = env("AWS_S3_CUSTOM_DOMAIN", default="")
AWS_DEFAULT_ACL = "public-read"
AWS_S3_FILE_OVERWRITE = False
