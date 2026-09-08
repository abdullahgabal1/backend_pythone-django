from django.urls import path
from apps.locations.views import LocationListView

urlpatterns = [
    path("", LocationListView.as_view(), name="location-list"),
]
