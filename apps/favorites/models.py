"""
Favorites — Models
===================
User saved properties.
"""
from django.conf import settings
from django.db import models

from apps.common.models import TimestampedModel
from apps.properties.models import Property


class Favorite(TimestampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorites",
    )
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name="favorited_by",
    )

    class Meta:
        unique_together = [("user", "property")]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - {self.property.title}"
