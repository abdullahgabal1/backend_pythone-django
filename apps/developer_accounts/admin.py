"""
Developer Accounts — Admin
============================
Admin registration for DeveloperAccount, DeveloperUser, Permission, and AuthToken.
"""
from django.contrib import admin

from apps.developer_accounts.models import (
    DeveloperAccount,
    DeveloperAuthToken,
    DeveloperUser,
    Permission,
)


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ["codename", "name"]
    search_fields = ["codename", "name"]


@admin.register(DeveloperAccount)
class DeveloperAccountAdmin(admin.ModelAdmin):
    list_display = ["id", "company_name", "member_count", "created_at"]
    search_fields = ["company_name"]

    @admin.display(description="Members")
    def member_count(self, obj):
        return obj.members.count()


@admin.register(DeveloperUser)
class DeveloperUserAdmin(admin.ModelAdmin):
    list_display = [
        "email",
        "first_name",
        "last_name",
        "account",
        "is_primary",
        "status",
        "permissions_list",
    ]
    list_filter = ["status", "is_primary", "account"]
    search_fields = ["email", "first_name", "last_name"]
    filter_horizontal = ["permissions"]
    readonly_fields = ["created_at", "updated_at"]

    @admin.display(description="Permissions")
    def permissions_list(self, obj):
        perms = obj.permissions.all()
        if not perms:
            return "—"
        return ", ".join(p.codename for p in perms)


@admin.register(DeveloperAuthToken)
class DeveloperAuthTokenAdmin(admin.ModelAdmin):
    list_display = ["user", "key_short", "created"]
    search_fields = ["user__email"]
    readonly_fields = ["key", "created"]

    @admin.display(description="Token (short)")
    def key_short(self, obj):
        return f"{obj.key[:12]}..."

