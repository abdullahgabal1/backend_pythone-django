"""
Properties — Admin Configuration
=================================
Admin site registration for Agent, Amenity, Property, and PropertyImage.
"""
from django.contrib import admin
from apps.properties.models import Agent, Amenity, Property, PropertyImage


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1
    fields = ("image", "order", "is_cover")


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    inlines = [PropertyImageInline]
    list_display = (
        "title",
        "property_type",
        "price",
        "location",
        "completion_status",
        "furnishing",
        "payment_method",
        "is_featured",
        "view_count",
        "created_at",
    )
    list_filter = (
        "property_type",
        "completion_status",
        "furnishing",
        "payment_method",
        "is_featured",
    )
    search_fields = ("title", "location", "description")
    filter_horizontal = ("amenities",)
    readonly_fields = ("view_count", "created_at", "updated_at")


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "created_at")
    search_fields = ("name", "phone")


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ("property", "image", "order", "is_cover", "created_at")
    list_filter = ("is_cover",)
