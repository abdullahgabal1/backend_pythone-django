"""
Users — Selectors (Query Helpers)
===================================
Read-only database queries for the users app.
"""
from apps.users.models import User


def get_user_by_phone(phone: str) -> User | None:
    """Look up a user by phone number. Returns None if not found."""
    try:
        return User.objects.get(phone=phone)
    except User.DoesNotExist:
        return None


def get_user_by_id(user_id: int) -> User | None:
    """Look up a user by primary key. Returns None if not found."""
    try:
        return User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return None
