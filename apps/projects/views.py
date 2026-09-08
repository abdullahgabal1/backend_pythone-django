"""
Projects — Views
==================
API views for developer project CRUD.
"""
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.pagination import StandardPagination
from apps.developer_accounts.authentication import DeveloperTokenAuthentication
from apps.developer_accounts.permissions import HasDeveloperPermission, IsDeveloperAuthenticated
from apps.projects.selectors import get_project_by_id, get_projects_queryset
from apps.projects.serializers import (
    ProjectDetailSerializer,
    ProjectListSerializer,
    ProjectWriteSerializer,
)
from apps.projects.services import create_project, delete_project, update_project

class ProjectListCreateView(APIView):
    """
    List or create projects for the authenticated developer's account.
    GET /api/v1/developer/projects/
    POST /api/v1/developer/projects/
    """
    authentication_classes = [DeveloperTokenAuthentication]
    permission_classes = [IsDeveloperAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        filters = {
            "status": request.query_params.get("status"),
            "project_type": request.query_params.get("project_type"),
            "search": request.query_params.get("search"),
        }
        projects = get_projects_queryset(request.user.account, filters)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(projects, request)
        serializer = ProjectListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        if not request.user.has_perm("manage_projects"):
            raise PermissionDenied("ليس لديك صلاحية لإدارة المشاريع.")
            
        serializer = ProjectWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        if "main_image" not in request.FILES:
            return Response({"main_image": ["الصورة الرئيسية مطلوبة."]}, status=status.HTTP_400_BAD_REQUEST)

        project = create_project(
            account=request.user.account,
            data=serializer.validated_data,
            files=request.FILES,
        )
        return Response(ProjectDetailSerializer(project).data, status=status.HTTP_201_CREATED)

class ProjectDetailView(APIView):
    """
    Get, update, or delete a specific project.
    GET/PUT/DELETE /api/v1/developer/projects/<id>/
    """
    authentication_classes = [DeveloperTokenAuthentication]
    permission_classes = [IsDeveloperAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def _get_project(self, pk, account):
        project = get_project_by_id(pk, account)
        if not project:
            raise NotFound("المشروع غير موجود.")
        return project

    def get(self, request, pk):
        project = self._get_project(pk, request.user.account)
        return Response(ProjectDetailSerializer(project).data)

    def put(self, request, pk):
        if not request.user.has_perm("manage_projects"):
            raise PermissionDenied("ليس لديك صلاحية لإدارة المشاريع.")
            
        project = self._get_project(pk, request.user.account)
        serializer = ProjectWriteSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        project = update_project(project, serializer.validated_data, request.FILES)
        return Response(ProjectDetailSerializer(project).data)

    def delete(self, request, pk):
        if not request.user.has_perm("manage_projects"):
            raise PermissionDenied("ليس لديك صلاحية لإدارة المشاريع.")
            
        project = self._get_project(pk, request.user.account)
        delete_project(project)
        return Response(status=status.HTTP_204_NO_CONTENT)

class ProjectStatsView(APIView):
    """
    Get quick stats for a specific project.
    GET /api/v1/developer/projects/<id>/stats/
    """
    authentication_classes = [DeveloperTokenAuthentication]
    permission_classes = [IsDeveloperAuthenticated]

    def get(self, request, pk):
        project = get_project_by_id(pk, request.user.account)
        if not project:
            raise NotFound("المشروع غير موجود.")

        from apps.marketing.models import MarketingLead
        stats = {
            "gallery_count": project.gallery.count(),
            "marketing_leads": MarketingLead.objects.filter(project=project).count(),
        }
        return Response(stats)

