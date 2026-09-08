"""
Developer Accounts — Services
================================
Business logic for developer authentication, account updates, and team management.
"""
from typing import Any

from django.db import transaction
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed, ValidationError

from apps.developer_accounts.models import (
    DeveloperAccount,
    DeveloperUser,
    DeveloperUserStatus,
    Permission,
)


def authenticate_developer(email: str, password: str) -> tuple[DeveloperUser, str]:
    """
    Authenticate a developer by email+password and return (user, token_key).
    """
    try:
        user = DeveloperUser.objects.get(email=email)
    except DeveloperUser.DoesNotExist:
        raise AuthenticationFailed("بيانات الدخول غير صحيحة.")

    if not user.check_password(password):
        raise AuthenticationFailed("بيانات الدخول غير صحيحة.")

    if user.status != DeveloperUserStatus.ACTIVE:
        raise AuthenticationFailed("هذا الحساب غير نشط. تواصل مع مدير الحساب.")

    token, _ = Token.objects.get_or_create(user_id=user.pk)
    return user, token.key


def update_developer_account(user: DeveloperUser, data: dict[str, Any]) -> DeveloperUser:
    """Update developer user profile fields."""
    if "first_name" in data:
        user.first_name = data["first_name"]
    if "last_name" in data:
        user.last_name = data["last_name"]
    if "email" in data:
        if DeveloperUser.objects.filter(email=data["email"]).exclude(pk=user.pk).exists():
            raise ValidationError({"email": "هذا البريد الإلكتروني مستخدم بالفعل."})
        user.email = data["email"]
    if "avatar" in data:
        user.avatar = data["avatar"]

    # Password change
    new_password = data.get("new_password")
    current_password = data.get("current_password")
    if new_password:
        if not user.check_password(current_password):
            raise ValidationError({"current_password": "كلمة المرور الحالية غير صحيحة."})
        user.set_password(new_password)

    user.save()
    return user


@transaction.atomic
def invite_team_member(account: DeveloperAccount, data: dict[str, Any]) -> DeveloperUser:
    """
    Create a new team member under the given account.
    """
    email = data["email"]
    if DeveloperUser.objects.filter(email=email).exists():
        raise ValidationError({"email": "هذا البريد الإلكتروني مستخدم بالفعل."})

    user = DeveloperUser.objects.create_user(
        email=email,
        password=data["password"],
        first_name=data["first_name"],
        last_name=data["last_name"],
        account=account,
        is_primary=False,
    )

    # Assign permissions
    permission_ids = data.get("permission_ids", [])
    if permission_ids:
        permissions = Permission.objects.filter(id__in=permission_ids)
        user.permissions.set(permissions)

    return user


def update_team_member(member: DeveloperUser, data: dict[str, Any]) -> DeveloperUser:
    """Update a team member's info, permissions, or status."""
    if "first_name" in data:
        member.first_name = data["first_name"]
    if "last_name" in data:
        member.last_name = data["last_name"]
    if "status" in data:
        member.status = data["status"]

    member.save()

    if "permission_ids" in data:
        permissions = Permission.objects.filter(id__in=data["permission_ids"])
        member.permissions.set(permissions)

    return member


def deactivate_team_member(member: DeveloperUser) -> None:
    """Deactivate (soft-delete) a team member."""
    member.status = DeveloperUserStatus.INACTIVE
    member.save(update_fields=["status"])


def delete_developer_account(user: DeveloperUser) -> None:
    """Delete the entire developer account and all associated data."""
    if not user.is_primary:
        raise ValidationError({"detail": "فقط المالك الأساسي يمكنه حذف الحساب."})
    account = user.account
    account.delete()  # CASCADE will handle members
