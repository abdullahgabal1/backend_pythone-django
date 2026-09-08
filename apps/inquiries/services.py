"""
Inquiries — Services
=====================
Business logic for inquiry creation, anti-spam validation, and notification triggers.
"""
from typing import Any
from django.core.cache import cache
from rest_framework.exceptions import ValidationError

from apps.common.validators import validate_egyptian_phone
from apps.inquiries.models import ContactMethod, Inquiry, InquiryType
from apps.inquiries.tasks import send_inquiry_notification
from apps.properties.models import Property


def create_inquiry(data: dict[str, Any], user=None, client_ip: str | None = None) -> Inquiry:
    """
    Create a new inquiry or consultation lead with anti-spam rate limiting.
    """
    raw_phone = str(data.get("phone", "")).strip()
    try:
        clean_phone = validate_egyptian_phone(raw_phone)
    except Exception as exc:
        raise ValidationError({"phone": str(exc)})

    property_id = data.get("property_id") or data.get("property")
    property_obj = None
    if property_id:
        try:
            property_obj = Property.objects.get(pk=property_id)
        except Property.DoesNotExist:
            raise ValidationError({"property": "العقار المحدد غير موجود."})

    # Anti-spam cooldown: prevent rapid duplicate inquiries for the same property
    prop_key = property_obj.id if property_obj else "general"
    cooldown_key = f"inquiry_cooldown_{clean_phone}_{prop_key}"

    if cache.get(cooldown_key):
        raise ValidationError(
            {"detail": "لقد قمت بإرسال استفسار مؤخراً لهذا العقار. يرجى الانتظار بضع دقائق قبل إرسال طلب جديد."}
        )

    inquiry = Inquiry.objects.create(
        property=property_obj,
        user=user if (user and user.is_authenticated) else None,
        name=str(data.get("name", "")).strip(),
        phone=clean_phone,
        message=str(data.get("message", "")).strip(),
        inquiry_type=data.get("inquiry_type", InquiryType.MESSAGE),
        preferred_contact_method=data.get("preferred_contact_method", ContactMethod.WHATSAPP),
        preferred_time=data.get("preferred_time"),
    )

    # Set cooldown: 300 seconds (5 minutes)
    cache.set(cooldown_key, 1, timeout=300)

    # Trigger async notification via Celery
    send_inquiry_notification.delay(inquiry.id)
    inquiry.refresh_from_db(fields=["agent_notified"])

    return inquiry


def update_lead(inquiry: Inquiry, status: str = None, rating: str = None) -> Inquiry:
    """Update a lead's status and rating from the Developer Dashboard."""
    if status:
        inquiry.status = status
    if rating:
        inquiry.rating = rating
    if status or rating:
        inquiry.save(update_fields=["status", "rating"] if status and rating else ["status"] if status else ["rating"])
    return inquiry

