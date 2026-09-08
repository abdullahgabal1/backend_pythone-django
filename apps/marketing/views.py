import csv
from django.http import HttpResponse
from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from apps.marketing.models import MarketingLead
from apps.marketing.serializers import MarketingLeadCreateSerializer
from apps.developer_accounts.authentication import DeveloperTokenAuthentication
from apps.developer_accounts.permissions import IsDeveloperAuthenticated, HasDeveloperPermission
from apps.common.pagination import StandardPagination


class MarketingLeadCreateView(generics.CreateAPIView):
    """
    Public webhook/endpoint for ingesting leads from ad campaigns.
    POST /api/v1/contact/lead/
    """
    queryset = MarketingLead.objects.all()
    serializer_class = MarketingLeadCreateSerializer
    permission_classes = [AllowAny]


class DeveloperLeadListView(generics.ListAPIView):
    """
    List marketing leads for the authenticated developer's account.
    GET /api/v1/developer/leads/
    """
    authentication_classes = [DeveloperTokenAuthentication]
    permission_classes = [IsDeveloperAuthenticated]
    serializer_class = MarketingLeadCreateSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        qs = MarketingLead.objects.filter(project__account=self.request.user.account).select_related("project")
        
        project_id = self.request.query_params.get("project_id")
        if project_id:
            qs = qs.filter(project_id=project_id)
            
        source = self.request.query_params.get("source")
        if source:
            qs = qs.filter(source=source)
            
        return qs.order_by("-created_at")


class DeveloperLeadExportView(APIView):
    """
    Export marketing leads as CSV.
    GET /api/v1/developer/leads/export/
    """
    authentication_classes = [DeveloperTokenAuthentication]
    permission_classes = [IsDeveloperAuthenticated, HasDeveloperPermission]
    required_permission = "export_excel"

    def get(self, request):
        qs = MarketingLead.objects.filter(project__account=request.user.account).select_related("project").order_by("-created_at")
        
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="leads_export.csv"'
        
        # Use utf-8-sig to ensure Excel opens Arabic characters correctly
        response.write(b'\xef\xbb\xbf')
        
        writer = csv.writer(response)
        writer.writerow(["Name", "Phone", "Source", "Campaign", "Project", "Processed", "Date"])
        
        for lead in qs:
            writer.writerow([
                lead.name,
                lead.phone,
                lead.get_source_display(),
                lead.campaign_name,
                lead.project.name if lead.project else "",
                "Yes" if lead.processed else "No",
                lead.created_at.strftime("%Y-%m-%d %H:%M:%S")
            ])
            
        return response
