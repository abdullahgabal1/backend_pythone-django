"""
Inquiries — Admin Configuration
================================
Admin site registration for Inquiry model.
"""
from django.contrib import admin
from apps.inquiries.models import Inquiry


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "phone",
        "inquiry_type",
        "property",
        "status",
        "preferred_contact_method",
        "agent_notified",
        "created_at",
    )
    list_filter = (
        "status",
        "inquiry_type",
        "preferred_contact_method",
        "agent_notified",
        "created_at",
    )
    search_fields = ("name", "phone", "message", "property__title")
    list_select_related = ("property", "user")
    readonly_fields = ("created_at", "updated_at")
