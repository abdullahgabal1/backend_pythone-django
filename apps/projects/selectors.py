"""
Projects — Selectors
======================
Query functions for developer projects.
"""
from django.db.models import QuerySet
from apps.developer_accounts.models import DeveloperAccount
from apps.projects.models import Project

def get_project_by_id(pk: int, account: DeveloperAccount) -> Project | None:
    """Get a single project ensuring it belongs to the given account."""
    return Project.objects.filter(pk=pk, account=account).prefetch_related("gallery").first()

def get_projects_queryset(account: DeveloperAccount, filters: dict = None) -> QuerySet[Project]:
    """Get all projects for an account, with optional filtering."""
    qs = Project.objects.filter(account=account).select_related("location")
    if filters:
        if filters.get("status"):
            qs = qs.filter(status=filters["status"])
        if filters.get("project_type"):
            qs = qs.filter(project_type=filters["project_type"])
        if filters.get("search"):
            qs = qs.filter(name__icontains=filters["search"])
    return qs
