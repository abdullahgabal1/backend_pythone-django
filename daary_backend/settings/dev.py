"""
Daary AI Backend — Development Settings
========================================
Inherits from base.py with development-friendly overrides.
"""
from .base import *  # noqa: F401, F403

DEBUG = True

# Use SQLite for quick local development if DATABASE_URL is not set
DATABASES = {
    "default": env.db("DATABASE_URL", default="sqlite:///" + str(BASE_DIR / "db.sqlite3")),
}

# Relax CORS for local frontend dev server
CORS_ALLOW_ALL_ORIGINS = True

# Print emails/SMS to console during development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
SMS_BACKEND = "console"

# Shorter token lifetimes for faster testing cycles
SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"] = timedelta(minutes=60)  # noqa: F405
