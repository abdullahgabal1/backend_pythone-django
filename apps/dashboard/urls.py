from django.urls import path
from apps.dashboard.views import DashboardOverviewView
from apps.marketing.views import DeveloperLeadListView, DeveloperLeadExportView

urlpatterns = [
    path("dashboard/overview/", DashboardOverviewView.as_view(), name="dashboard-overview"),
    path("leads/", DeveloperLeadListView.as_view(), name="developer-leads-list"),
    path("leads/export/", DeveloperLeadExportView.as_view(), name="developer-leads-export"),
]
