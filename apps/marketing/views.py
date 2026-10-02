import csv
from django.db.models import Q
from django.http import HttpResponse
from rest_framework import generics, status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.pagination import StandardPagination
from apps.developer_accounts.authentication import DeveloperTokenAuthentication
from apps.developer_accounts.permissions import HasDeveloperPermission, IsDeveloperAuthenticated
from apps.inquiries.models import Inquiry
from apps.inquiries.serializers import (
    DeveloperLeadSerializer,
    DeveloperLeadUpdateSerializer,
)
from apps.inquiries.services import update_lead
from apps.marketing.models import MarketingLead
from apps.marketing.serializers import MarketingLeadCreateSerializer


class MarketingLeadCreateView(generics.CreateAPIView):
    """
    Public webhook/endpoint for ingesting leads from ad campaigns.
    POST /api/v1/contact/lead/
    """
    queryset = MarketingLead.objects.all()
    serializer_class = MarketingLeadCreateSerializer
    permission_classes = [AllowAny]


class DeveloperLeadListView(APIView):
    """
    List leads for the authenticated developer's account.
    Supports querying buyer property/project inquiries (default) or ad marketing leads (?type=marketing).
    GET /api/v1/developer/leads/
    """
    authentication_classes = [DeveloperTokenAuthentication]
    permission_classes = [IsDeveloperAuthenticated, HasDeveloperPermission]
    required_permission = "view_leads"

    def get(self, request):
        lead_type = request.query_params.get("type")
        account = request.user.account
        project_id = request.query_params.get("project_id")
        source = request.query_params.get("source")
        rating = request.query_params.get("rating")
        lead_status = request.query_params.get("status")

        if lead_type == "marketing":
            qs = MarketingLead.objects.filter(project__account=account).select_related("project")
            if project_id:
                qs = qs.filter(project_id=project_id)
            if source:
                qs = qs.filter(source=source)
            paginator = StandardPagination()
            page = paginator.paginate_queryset(qs.order_by("-created_at"), request)
            serializer = MarketingLeadCreateSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        else:
            qs = Inquiry.objects.filter(
                Q(property__project__account=account) | Q(project__account=account)
            ).select_related("property", "project", "property__project")

            if project_id:
                qs = qs.filter(Q(property__project_id=project_id) | Q(project_id=project_id))
            if source:
                qs = qs.filter(source=source)
            if rating:
                qs = qs.filter(rating=rating)
            if lead_status:
                qs = qs.filter(status=lead_status)

            paginator = StandardPagination()
            page = paginator.paginate_queryset(qs.order_by("-created_at"), request)
            serializer = DeveloperLeadSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)


class DeveloperLeadDetailView(APIView):
    """
    Retrieve or update (status/rating) a specific buyer lead.
    GET /api/v1/developer/leads/<id>/
    PATCH /api/v1/developer/leads/<id>/
    """
    authentication_classes = [DeveloperTokenAuthentication]
    permission_classes = [IsDeveloperAuthenticated, HasDeveloperPermission]
    required_permission = "view_leads"

    def _get_lead(self, pk, account):
        lead = (
            Inquiry.objects.filter(
                Q(property__project__account=account) | Q(project__account=account)
            )
            .select_related("property", "project", "property__project")
            .filter(pk=pk)
            .first()
        )
        if not lead:
            raise NotFound("العميل غير موجود.")
        return lead

    def get(self, request, pk: int):
        lead = self._get_lead(pk, request.user.account)
        serializer = DeveloperLeadSerializer(lead)
        return Response(serializer.data)

    def patch(self, request, pk: int):
        if not request.user.has_perm("rate_leads"):
            raise PermissionDenied("ليس لديك صلاحية لتقييم وتحديث العملاء.")

        lead = self._get_lead(pk, request.user.account)
        serializer = DeveloperLeadUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        updated_lead = update_lead(
            lead,
            status=serializer.validated_data.get("status"),
            rating=serializer.validated_data.get("rating"),
        )
        return Response(DeveloperLeadSerializer(updated_lead).data)


class DeveloperLeadExportView(APIView):
    """
    Export all leads (marketing campaigns and buyer inquiries) as CSV.
    GET /api/v1/developer/leads/export/
    """
    authentication_classes = [DeveloperTokenAuthentication]
    permission_classes = [IsDeveloperAuthenticated, HasDeveloperPermission]
    required_permission = "export_excel"

    def get(self, request):
        account = request.user.account
        marketing_qs = MarketingLead.objects.filter(project__account=account).select_related("project").order_by("-created_at")
        inquiry_qs = (
            Inquiry.objects.filter(
                Q(property__project__account=account) | Q(project__account=account)
            )
            .select_related("property", "project", "property__project")
            .order_by("-created_at")
        )

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="leads_export.csv"'
        response.write(b'\xef\xbb\xbf')

        writer = csv.writer(response)
        writer.writerow(["Type", "Name", "Phone", "Source", "Project", "Property", "Status", "Rating", "Date"])

        for lead in marketing_qs:
            writer.writerow([
                "Marketing",
                lead.name,
                lead.phone,
                lead.get_source_display(),
                lead.project.name if lead.project else "",
                "",
                "Processed" if lead.processed else "New",
                "",
                lead.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            ])

        for inq in inquiry_qs:
            project_name = inq.project.name if inq.project else (inq.property.project.name if inq.property and inq.property.project else "")
            writer.writerow([
                "Inquiry",
                inq.name,
                inq.phone,
                inq.get_source_display(),
                project_name,
                inq.property.title if inq.property else "",
                inq.get_status_display(),
                inq.get_rating_display() if inq.rating else "",
                inq.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            ])

        return response
