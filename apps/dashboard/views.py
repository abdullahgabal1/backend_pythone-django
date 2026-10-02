"""
Dashboard — Views
===================
Overview stats for the developer dashboard.
"""
from rest_framework import generics
from rest_framework.response import Response

from apps.dashboard.serializers import DashboardOverviewSerializer
from apps.dashboard.services import get_dashboard_stats
from apps.developer_accounts.authentication import DeveloperTokenAuthentication
from apps.developer_accounts.permissions import HasDeveloperPermission, IsDeveloperAuthenticated


class DashboardOverviewView(generics.GenericAPIView):
    """
    GET /api/v1/developer/dashboard/overview/
    """
    authentication_classes = [DeveloperTokenAuthentication]
    permission_classes = [IsDeveloperAuthenticated, HasDeveloperPermission]
    required_permission = "view_leads"
    serializer_class = DashboardOverviewSerializer

    def get(self, request):
        stats = get_dashboard_stats(request.user.account)
        serializer = self.get_serializer(stats)
        return Response(serializer.data)
