"""
Locations — Models
====================
Hierarchical location lookup for dashboard dropdowns (e.g., governorate > area > compound).
"""
from django.db import models

class Location(models.Model):
    name = models.CharField(max_length=150)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
    )

    class Meta:
        ordering = ["name"]
        unique_together = ["name", "parent"]

    def __str__(self):
        if self.parent:
            return f"{self.name} - {self.parent.name}"
        return self.name
