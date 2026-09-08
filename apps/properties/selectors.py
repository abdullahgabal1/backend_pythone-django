"""
Properties — Selectors
=======================
Database query functions for properties catalog.
"""
from typing import Any, Optional
from django.db.models import QuerySet
from apps.properties.models import Property


def get_property_by_id(pk: int) -> Optional[Property]:
    """
    Fetch a single property by its primary key with prefetched relationships.
    """
    try:
        return (
            Property.objects.select_related("agent")
            .prefetch_related("images", "amenities")
            .get(pk=pk)
        )
    except Property.DoesNotExist:
        return None


def get_properties_queryset(filters: Optional[dict[str, Any]] = None) -> QuerySet[Property]:
    """
    Returns a filtered queryset of properties.
    Supports basic filtering:
    - location: icontains
    - property_type: exact
    - completion_status: exact
    - furnishing: exact
    - payment_method: exact
    - is_featured: boolean
    - ordering: 'newest', 'oldest', etc.
    """
    queryset = (
        Property.objects.select_related("agent")
        .prefetch_related("images")
        .all()
    )

    if not filters:
        return queryset

    location = filters.get("location")
    if location:
        queryset = queryset.filter(location__icontains=location.strip())

    property_type = filters.get("property_type")
    if property_type:
        queryset = queryset.filter(property_type=property_type)

    completion_status = filters.get("completion_status")
    if completion_status:
        queryset = queryset.filter(completion_status=completion_status)

    furnishing = filters.get("furnishing")
    if furnishing:
        queryset = queryset.filter(furnishing=furnishing)

    payment_method = filters.get("payment_method")
    if payment_method:
        queryset = queryset.filter(payment_method=payment_method)

    is_featured = filters.get("is_featured")
    if is_featured is not None:
        if isinstance(is_featured, str):
            is_featured_bool = is_featured.lower() in ("true", "1", "yes")
        else:
            is_featured_bool = bool(is_featured)
        queryset = queryset.filter(is_featured=is_featured_bool)

    ordering = filters.get("ordering")
    if ordering:
        if ordering in ("newest", "-created_at"):
            queryset = queryset.order_by("-created_at")
        elif ordering in ("oldest", "created_at"):
            queryset = queryset.order_by("created_at")
        elif ordering in ("price_asc", "price-asc"):
            queryset = queryset.order_by("price")
        elif ordering in ("price_desc", "price-desc"):
            queryset = queryset.order_by("-price")
        elif ordering in ("area_desc", "area-desc"):
            queryset = queryset.order_by("-area_sqm")

    return queryset
