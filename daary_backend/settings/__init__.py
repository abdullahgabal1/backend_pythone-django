"""
Settings package initializer.

Loads the correct settings module based on the DJANGO_ENV environment variable.
Defaults to 'dev' when not set.
"""
import os
import importlib

env = os.environ.get("DJANGO_ENV", "dev")

# Import the environment-specific settings module into this namespace
_module = importlib.import_module(f"daary_backend.settings.{env}")
globals().update({k: v for k, v in vars(_module).items() if not k.startswith("_")})
