"""
Inquiries — Background Tasks & Notifications
=============================================
Notification dispatch for property agents and consultants.
Uses Celery shared_task with retry policy for transient failures.
"""
import logging

import requests
from celery import shared_task
from django.conf import settings

from apps.inquiries.models import Inquiry

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(requests.exceptions.RequestException,),
    max_retries=3,
    default_retry_delay=60,
    retry_backoff=True,
    retry_backoff_max=600,
)
def send_inquiry_notification(self, inquiry_id: int) -> bool:
    """
    Send an instant alert message to the property's agent or sales team.
    Retries up to 3 times with exponential backoff on transient failures.
    """
    try:
        inquiry = Inquiry.objects.select_related("property", "property__agent").get(pk=inquiry_id)
    except Inquiry.DoesNotExist:
        logger.warning("Inquiry %s does not exist for notification", inquiry_id)
        return False

    agent_phone = None
    agent_name = "فريق المبيعات"
    prop_title = "استشارة عامة"

    if inquiry.property:
        prop_title = inquiry.property.title
        if inquiry.property.agent:
            agent_phone = inquiry.property.agent.phone
            agent_name = inquiry.property.agent.name

    notification_text = (
        f"📢 إشعار جديد لـ {agent_name}:\n"
        f"العميل: {inquiry.name} ({inquiry.phone})\n"
        f"نوع الطلب: {inquiry.get_inquiry_type_display()}\n"
        f"طريقة التواصل المفضلة: {inquiry.get_preferred_contact_method_display()}\n"
        f"العقار: {prop_title}\n"
    )
    if inquiry.message:
        notification_text += f"الرسالة: {inquiry.message}\n"
    if inquiry.preferred_time:
        notification_text += f"الموعد المفضل: {inquiry.preferred_time.strftime('%Y-%m-%d %H:%M')}\n"

    logger.info("Agent Notification Dispatched:\n%s", notification_text)

    webhook_url = getattr(settings, "NOTIFICATION_WEBHOOK_URL", "")
    if webhook_url:
        response = requests.post(
            webhook_url,
            json={"phone": agent_phone, "message": notification_text},
            timeout=10,
        )
        response.raise_for_status()

    # Mark as notified
    Inquiry.objects.filter(pk=inquiry.id).update(agent_notified=True)
    return True
