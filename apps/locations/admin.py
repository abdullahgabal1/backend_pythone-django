from django.contrib import admin
from apps.locations.models import Location

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ["name", "parent"]
    search_fields = ["name"]
