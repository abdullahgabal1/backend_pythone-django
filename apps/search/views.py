"""
Search — Views
===============
API endpoint for searching and filtering properties.
"""
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.pagination import StandardPagination
from apps.properties.serializers import PropertyListSerializer
from apps.search.services import search_properties


class PropertySearchView(APIView):
    """
    Search and filter properties according to the complete buyer frontend filter contract.
    GET /api/v1/search/
    """
    permission_classes = [AllowAny]

    def get(self, request):
        filters = request.query_params.dict()
        sort_by = filters.get("sortBy") or filters.get("ordering")

        queryset = search_properties(filters=filters, ordering=sort_by)

        paginator = StandardPagination()
        paginator.max_page_size = 50

        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = PropertyListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = PropertyListSerializer(queryset, many=True)
        return Response(serializer.data)
