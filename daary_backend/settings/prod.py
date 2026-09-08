"""
Daary AI Backend — Production Settings
========================================
Inherits from base.py with security-hardened overrides.
"""
from .base import *  # noqa: F401, F403

DEBUG = env("DEBUG", default=False)

# ─── Security Hardening ──────────────────────────────────────────
SECURE_SSL_REDIRECT = env("SECURE_SSL_REDIRECT", default=True)
SECURE_HSTS_SECONDS = env("SECURE_HSTS_SECONDS", default=31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True)
SECURE_HSTS_PRELOAD = env("SECURE_HSTS_PRELOAD", default=True)
SESSION_COOKIE_SECURE = env("SESSION_COOKIE_SECURE", default=True)
CSRF_COOKIE_SECURE = env("CSRF_COOKIE_SECURE", default=True)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# Database — must be set via DATABASE_URL in environment
DATABASES = {
    "default": env.db("DATABASE_URL"),
}

# Static files
STATIC_ROOT = BASE_DIR / "staticfiles"

# Tighten CORS to explicit origins only
CORS_ALLOW_ALL_ORIGINS = False

# ─── S3 File Storage (production) ────────────────────────────────
# Activate S3 for media uploads in production when bucket is configured
if env("AWS_STORAGE_BUCKET_NAME", default=""):
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
