from rest_framework import generics
from rest_framework.permissions import AllowAny
from apps.locations.models import Location
from apps.locations.serializers import LocationSerializer

class LocationListView(generics.ListAPIView):
    """
    List structural locations for developer dashboard.
    GET /api/v1/locations/
    """
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(name__icontains=search)
        parent_id = self.request.query_params.get("parent")
        if parent_id is not None:
            if parent_id.lower() == "none":
                qs = qs.filter(parent__isnull=True)
            else:
                qs = qs.filter(parent_id=parent_id)
        return qs
