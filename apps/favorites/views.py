"""
Favorites — Views
==================
API views for listing and toggling favorite properties.
"""
from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.pagination import StandardPagination
from apps.favorites.models import Favorite
from apps.favorites.serializers import FavoriteSerializer
from apps.favorites.services import toggle_favorite
from apps.properties.selectors import get_property_by_id


class FavoriteListView(generics.ListAPIView):
    """
    List all favorited properties for the authenticated user.
    GET /api/v1/favorites/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = FavoriteSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        return (
            Favorite.objects.filter(user=self.request.user)
            .select_related("property", "property__agent")
            .prefetch_related("property__images")
        )


class FavoriteToggleView(APIView):
    """
    Toggle a property in the authenticated user's favorites.
    POST /api/v1/favorites/<pk>/toggle/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk: int):
        property_obj = get_property_by_id(pk)
        if not property_obj:
            raise NotFound("Property not found.")

        result = toggle_favorite(request.user, property_obj)
        return Response(result, status=status.HTTP_200_OK)
