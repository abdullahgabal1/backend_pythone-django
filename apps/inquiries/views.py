"""
Inquiries — Views
==================
API views for creating property inquiries and viewing buyer inquiry history.
"""
from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.pagination import StandardPagination
from apps.inquiries.selectors import get_inquiry_by_id, get_user_inquiries
from apps.inquiries.serializers import (
    InquiryCreateSerializer,
    InquiryDetailSerializer,
    InquiryListSerializer,
)
from apps.inquiries.services import create_inquiry


class InquiryCreateView(APIView):
    """
    Submit an inquiry or viewing request on a property.
    POST /api/v1/inquiries/
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = InquiryCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        client_ip = request.META.get("HTTP_X_FORWARDED_FOR")
        if client_ip:
            client_ip = client_ip.split(",")[0].strip()
        else:
            client_ip = request.META.get("REMOTE_ADDR")

        inquiry = create_inquiry(
            data=serializer.validated_data,
            user=request.user,
            client_ip=client_ip,
        )

        response_serializer = InquiryDetailSerializer(inquiry)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class MyInquiriesListView(generics.ListAPIView):
    """
    List all inquiries submitted by the authenticated buyer.
    GET /api/v1/inquiries/my/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = InquiryListSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        return get_user_inquiries(self.request.user)


class InquiryDetailView(APIView):
    """
    Get detailed information for a specific inquiry owned by the user.
    GET /api/v1/inquiries/<pk>/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk: int):
        inquiry = get_inquiry_by_id(pk, user=request.user)
        if not inquiry:
            raise NotFound("Inquiry not found.")

        serializer = InquiryDetailSerializer(inquiry)
        return Response(serializer.data, status=status.HTTP_200_OK)
