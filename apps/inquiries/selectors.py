"""
Inquiries — Selectors
======================
Query functions for retrieving inquiries.
"""
from typing import Optional
from django.db.models import QuerySet
from apps.inquiries.models import Inquiry


def get_user_inquiries(user) -> QuerySet[Inquiry]:
    """
    Get all inquiries submitted by the specified authenticated user.
    """
    return (
        Inquiry.objects.filter(user=user)
        .select_related("property", "property__agent")
        .prefetch_related("property__images")
        .order_by("-created_at")
    )


def get_inquiry_by_id(pk: int, user=None) -> Optional[Inquiry]:
    """
    Retrieve a single inquiry by ID, optionally verifying ownership.
    """
    qs = (
        Inquiry.objects.select_related("property", "property__agent")
        .prefetch_related("property__images")
    )
    if user and not user.is_staff:
        qs = qs.filter(user=user)

    return qs.filter(pk=pk).first()

