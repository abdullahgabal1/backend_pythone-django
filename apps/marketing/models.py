"""
Marketing — Models
====================
Lead capture from marketing campaigns.
"""
from django.db import models
from apps.common.models import TimestampedModel

class LeadSource(models.TextChoices):
    FACEBOOK = "facebook", "Facebook Ads"
    INSTAGRAM = "instagram", "Instagram Ads"
    GOOGLE = "google", "Google Ads"
    TIKTOK = "tiktok", "TikTok Ads"
    DIRECT = "direct", "Direct/Organic"

class MarketingLead(TimestampedModel):
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    source = models.CharField(
        max_length=50,
        choices=LeadSource.choices,
        default=LeadSource.DIRECT,
    )
    campaign_name = models.CharField(max_length=150, blank=True, default="")
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="marketing_leads",
    )
    processed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["source", "processed"]),
            models.Index(fields=["phone"]),
        ]

    def __str__(self):
        return f"{self.name} - {self.phone} ({self.source})"
