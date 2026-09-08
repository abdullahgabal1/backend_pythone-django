"""
Common — Custom Permissions
=============================
Reusable permission classes for views.
"""
from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """
    Object-level permission: only allows the object's owner to access it.
    Expects the object to have a `user` or `user_id` attribute.
    """

    def has_object_permission(self, request, view, obj):
        owner = getattr(obj, "user", None)
        if owner is None:
            owner = getattr(obj, "user_id", None)
            if owner is not None:
                return request.user.pk == owner
            return False
        return request.user == owner
