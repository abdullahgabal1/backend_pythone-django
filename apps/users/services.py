"""
Users — Business Logic Services
=================================
Write operations for user management.
"""
from apps.users.models import User


def update_user_profile(user: User, **fields) -> User:
    """
    Update mutable fields on a user profile.
    Only 'name' and 'birthday' are updatable.
    Phone is the account identifier and cannot be changed.
    """
    allowed_fields = {"name", "birthday"}

    for field, value in fields.items():
        if field in allowed_fields and value is not None:
            setattr(user, field, value)

    user.full_clean()
    user.save(update_fields=[f for f in fields if f in allowed_fields])
    return user
