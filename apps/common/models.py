"""
Common — Abstract Base Models
==============================
Reusable timestamp mixin for all concrete models.
"""
from django.db import models


class TimestampedModel(models.Model):
    """
    Abstract model providing created_at and updated_at timestamps.
    All concrete models should inherit from this.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]
