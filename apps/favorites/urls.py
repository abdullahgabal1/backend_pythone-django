"""
Favorites — URL Configuration
==============================
Routes for favorites list and toggle endpoints.
"""
from django.urls import path
from apps.favorites.views import FavoriteListView, FavoriteToggleView

urlpatterns = [
    path("", FavoriteListView.as_view(), name="favorite-list"),
    path("<int:pk>/toggle/", FavoriteToggleView.as_view(), name="favorite-toggle"),
]
