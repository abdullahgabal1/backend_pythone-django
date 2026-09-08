"""
Search — URL Configuration
===========================
Routes for property search endpoint.
"""
from django.urls import path
from apps.search.views import PropertySearchView

urlpatterns = [
    path("", PropertySearchView.as_view(), name="property-search"),
]
