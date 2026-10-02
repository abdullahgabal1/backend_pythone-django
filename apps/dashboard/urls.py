from django.urls import path
from apps.dashboard.views import DashboardOverviewView
from apps.marketing.views import (
    DeveloperLeadDetailView,
    DeveloperLeadExportView,
    DeveloperLeadListView,
)

urlpatterns = [
    path("dashboard/overview/", DashboardOverviewView.as_view(), name="dashboard-overview"),
    path("leads/", DeveloperLeadListView.as_view(), name="developer-leads-list"),
    path("leads/<int:pk>/", DeveloperLeadDetailView.as_view(), name="developer-lead-detail"),
    path("leads/export/", DeveloperLeadExportView.as_view(), name="developer-leads-export"),
]
