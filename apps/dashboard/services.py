"""
Dashboard — Services
======================
Aggregation logic for developer dashboard statistics.
"""
from datetime import timedelta

from django.core.cache import cache
from django.db.models import Count
from django.utils import timezone

from apps.developer_accounts.models import DeveloperAccount
from apps.marketing.models import MarketingLead
from apps.projects.models import Project


def get_dashboard_stats(account: DeveloperAccount) -> dict:
    """
    Aggregated stats for the dashboard overview.
    """
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)

    # ── Projects ──
    projects = Project.objects.filter(account=account)
    total_projects = projects.count()
    active_projects = projects.filter(status="active").count()

    # ── Marketing Leads ──
    marketing_leads = MarketingLead.objects.filter(project__account=account)
    total_marketing = marketing_leads.count()
    marketing_last_30 = marketing_leads.filter(created_at__gte=thirty_days_ago).count()

    # Leads by source
    leads_by_source = dict(
        marketing_leads
        .values_list("source")
        .annotate(cnt=Count("id"))
        .order_by("-cnt")
    )

    # ── Top Projects by marketing leads ──
    top_projects = (
        projects
        .annotate(lead_count=Count("marketing_leads"))
        .order_by("-lead_count")[:5]
    )

    # ── Location price medians from cache ──
    location_medians = cache.get("location_price_medians", {})

    return {
        "projects": {
            "total": total_projects,
            "active": active_projects,
            "top_by_leads": [
                {"id": p.id, "name": p.name, "lead_count": p.lead_count}
                for p in top_projects
            ],
        },
        "leads": {
            "total": total_marketing,
            "last_30_days": marketing_last_30,
            "by_source": leads_by_source,
        },
        "location_medians": location_medians,
    }
