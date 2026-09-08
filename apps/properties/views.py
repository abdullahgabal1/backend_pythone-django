"""
Properties — Views
===================
API views for browsing and viewing properties.
"""
from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.pagination import StandardPagination
from apps.properties.selectors import get_properties_queryset, get_property_by_id
from apps.properties.serializers import PropertyDetailSerializer, PropertyListSerializer
from apps.properties.services import increment_view_count


class PropertyListView(generics.ListAPIView):
    """
    List properties with basic filtering and pagination.
    Supports ?is_featured=true, ?ordering=newest, etc.
    """
    permission_classes = [AllowAny]
    serializer_class = PropertyListSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        params = self.request.query_params
        filters = {
            "location": params.get("location"),
            "property_type": params.get("property_type"),
            "completion_status": params.get("completion_status"),
            "furnishing": params.get("furnishing"),
            "payment_method": params.get("payment_method"),
            "is_featured": params.get("is_featured"),
            "ordering": params.get("ordering"),
        }
        return get_properties_queryset(filters)


class PropertyDetailView(APIView):
    """
    Property detail view. Increments view_count with client-level deduplication.
    """
    permission_classes = [AllowAny]

    def get(self, request, pk: int):
        property_obj = get_property_by_id(pk)
        if not property_obj:
            raise NotFound("Property not found.")

        increment_view_count(property_obj, request)
        serializer = PropertyDetailSerializer(property_obj)
        return Response(serializer.data, status=status.HTTP_200_OK)
