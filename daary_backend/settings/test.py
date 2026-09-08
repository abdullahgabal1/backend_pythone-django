"""
Daary AI Backend — Test Settings
=================================
Inherits from base.py with speed-optimized overrides for pytest.
"""
from .base import *  # noqa: F401, F403

DEBUG = False

# Use in-memory SQLite for fast test execution
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    },
}

# Faster password hashing during tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Always use console SMS backend in tests
SMS_BACKEND = "console"
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Shorter token lifetimes
SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"] = timedelta(minutes=5)  # noqa: F405
SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"] = timedelta(days=1)  # noqa: F405

# Speed up tests by increasing rate limits
REST_FRAMEWORK = {
    **REST_FRAMEWORK,  # noqa: F405
    "DEFAULT_THROTTLE_RATES": {
        "anon": "1000/minute",
        "otp": "1000/minute",
        "platform_inquiry": "1000/hour",
    },
}

