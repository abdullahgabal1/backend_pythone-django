"""
Properties — URL Configuration
===============================
Routes for property list and detail views.
"""
from django.urls import path
from apps.properties.views import PropertyDetailView, PropertyListView

urlpatterns = [
    path("", PropertyListView.as_view(), name="property-list"),
    path("<int:pk>/", PropertyDetailView.as_view(), name="property-detail"),
]
