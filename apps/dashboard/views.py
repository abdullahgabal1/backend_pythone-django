"""
Dashboard — Views
===================
Overview stats for the developer dashboard.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.developer_accounts.authentication import DeveloperTokenAuthentication
from apps.developer_accounts.permissions import IsDeveloperAuthenticated
from apps.dashboard.services import get_dashboard_stats

class DashboardOverviewView(APIView):
    """
    GET /api/v1/developer/dashboard/overview/
    """
    authentication_classes = [DeveloperTokenAuthentication]
    permission_classes = [IsDeveloperAuthenticated]

    def get(self, request):
        stats = get_dashboard_stats(request.user.account)
        return Response(stats)
