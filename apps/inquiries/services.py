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

    project_id = data.get("project_id") or data.get("project")
    project_obj = property_obj.project if (property_obj and property_obj.project) else None
    if project_id and not project_obj:
        from apps.projects.models import Project
        try:
            project_obj = Project.objects.get(pk=project_id)
        except Project.DoesNotExist:
            raise ValidationError({"project": "المشروع المحدد غير موجود."})

    # Anti-spam cooldown: prevent rapid duplicate inquiries for the same property
    prop_key = property_obj.id if property_obj else (f"proj_{project_obj.id}" if project_obj else "general")
    cooldown_key = f"inquiry_cooldown_{clean_phone}_{prop_key}"

    if cache.get(cooldown_key):
        raise ValidationError(
            {"detail": "لقد قمت بإرسال استفسار مؤخراً لهذا العقار. يرجى الانتظار بضع دقائق قبل إرسال طلب جديد."}
        )

    inquiry = Inquiry.objects.create(
        property=property_obj,
        project=project_obj,
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
    update_fields = []
    if status is not None:
        inquiry.status = status
        update_fields.append("status")
    if rating is not None:
        inquiry.rating = rating
        update_fields.append("rating")
    if update_fields:
        inquiry.save(update_fields=update_fields)
    return inquiry

