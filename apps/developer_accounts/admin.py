"""
Developer Accounts — Admin
============================
Admin registration for DeveloperAccount, DeveloperUser, and Permission.
"""
from django.contrib import admin

from apps.developer_accounts.models import DeveloperAccount, DeveloperUser, Permission


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ["codename", "name"]
    search_fields = ["codename", "name"]


@admin.register(DeveloperAccount)
class DeveloperAccountAdmin(admin.ModelAdmin):
    list_display = ["id", "company_name", "created_at"]
    search_fields = ["company_name"]


@admin.register(DeveloperUser)
class DeveloperUserAdmin(admin.ModelAdmin):
    list_display = ["email", "first_name", "last_name", "account", "is_primary", "status"]
    list_filter = ["status", "is_primary", "account"]
    search_fields = ["email", "first_name", "last_name"]
    filter_horizontal = ["permissions"]
