"""
Favorites — Admin Configuration
================================
Admin site registration for Favorite model.
"""
from django.contrib import admin
from apps.favorites.models import Favorite


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "property", "created_at")
    search_fields = ("user__phone_number", "property__title")
    list_select_related = ("user", "property")
