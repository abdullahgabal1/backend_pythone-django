"""
Inquiries — Models
===================
Models for buyer inquiries, viewing requests, and qualified consultation leads.
"""
from django.conf import settings
from django.db import models

from apps.common.models import TimestampedModel
from apps.common.validators import validate_egyptian_phone
from apps.properties.models import Property


class InquiryType(models.TextChoices):
    MESSAGE = "message", "رسالة"
    VIEWING = "viewing", "طلب معاينة"
    CALL = "call", "طلب اتصال"
    WHATSAPP = "whatsapp", "واتساب"
    CONSULTATION_LEAD = "consultation_lead", "استشارة عقارية ذكية"


class InquiryStatus(models.TextChoices):
    PENDING = "pending", "قيد الانتظار"
    CONTACTED = "contacted", "تم التواصل"
    COMPLETED = "completed", "مكتمل"
    CANCELLED = "cancelled", "ملغي"


class ContactMethod(models.TextChoices):
    WHATSAPP = "whatsapp", "واتساب"
    PHONE = "phone", "اتصال هاتفي"
    EMAIL = "email", "بريد إلكتروني"


class Inquiry(TimestampedModel):
    property = models.ForeignKey(
        Property,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="inquiries",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="inquiries",
    )
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20, validators=[validate_egyptian_phone])
    message = models.TextField(blank=True, default="")
    inquiry_type = models.CharField(
        max_length=25,
        choices=InquiryType.choices,
        default=InquiryType.MESSAGE,
    )
    status = models.CharField(
        max_length=20,
        choices=InquiryStatus.choices,
        default=InquiryStatus.PENDING,
    )
    preferred_contact_method = models.CharField(
        max_length=20,
        choices=ContactMethod.choices,
        default=ContactMethod.WHATSAPP,
    )
    preferred_time = models.DateTimeField(null=True, blank=True)
    
    # Lead-specific fields (Developer Dashboard)
    rating = models.CharField(
        max_length=20,
        choices=[("excellent", "ممتاز"), ("good", "جيد"), ("average", "متوسط"), ("bad", "سيء")],
        null=True,
        blank=True,
    )
    source = models.CharField(
        max_length=25,
        choices=[("ai_suggestion", "اقتراح ذكاء اصطناعي"), ("favorite", "المفضلة"), ("contact", "تواصل مباشر"), ("manual", "يدوي")],
        default="contact",
    )
    requirement_summary = models.TextField(blank=True, default="")
    
    agent_notified = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "inquiries"
        indexes = [
            models.Index(fields=["property", "created_at"]),
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        prop_title = self.property.title if self.property else "استشارة عامة"
        return f"{self.name} ({self.get_inquiry_type_display()}) - {prop_title}"
