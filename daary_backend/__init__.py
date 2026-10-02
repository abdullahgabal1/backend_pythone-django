"""
Daary AI Backend — Package Init
==================================
Ensures the Celery app is loaded when Django starts.
"""
from .celery import app as celery_app

__all__ = ["celery_app"]

# Monkey-patch Django 5.0.x for Python 3.14 compatibility with Admin templates
# Resolves the 'super' object has no attribute 'dicts' issue in admin views.
try:
    import django.template.context

    def _patched_copy(self):
        duplicate = object.__new__(type(self))
        if hasattr(self, '__dict__'):
            duplicate.__dict__ = self.__dict__.copy()
        duplicate.dicts = self.dicts[:]
        return duplicate

    django.template.context.BaseContext.__copy__ = _patched_copy
except Exception:
    pass
