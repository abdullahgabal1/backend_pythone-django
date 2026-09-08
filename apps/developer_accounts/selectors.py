"""
Developer Accounts — Selectors
================================
Query functions for developer team members.
"""
from django.db.models import QuerySet

from apps.developer_accounts.models import DeveloperAccount, DeveloperUser


def get_team_members(account: DeveloperAccount) -> QuerySet[DeveloperUser]:
    """Get all team members belonging to the given account."""
    return (
        DeveloperUser.objects.filter(account=account)
        .prefetch_related("permissions")
        .order_by("-is_primary", "-created_at")
    )
