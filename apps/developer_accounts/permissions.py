"""
Developer Accounts — Permissions
==================================
Custom permission classes for the developer dashboard realm.
"""
from rest_framework.permissions import BasePermission

from apps.developer_accounts.models import DeveloperUser


class IsDeveloperAuthenticated(BasePermission):
    """
    Only allows access to authenticated DeveloperUser instances.
    Works with DRF TokenAuthentication where the user is a DeveloperUser.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and isinstance(request.user, DeveloperUser)
            and request.user.is_active
        )


class HasDeveloperPermission(BasePermission):
    """
    Checks that the DeveloperUser has a specific permission codename.
    Primary account owners automatically pass all permission checks.

    Usage: set `required_permission = "manage_team"` on the view.
    """

    def has_permission(self, request, view):
        if not isinstance(request.user, DeveloperUser):
            return False

        required = getattr(view, "required_permission", None)
        if not required:
            return True

        return request.user.has_perm(required)
