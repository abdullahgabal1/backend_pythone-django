"""Scheduled cache maintenance for relevance ranking."""
import hashlib
import statistics

from celery import shared_task
from django.core.cache import cache

from apps.properties.models import Property


@shared_task
def refresh_price_medians() -> int:
    """Refresh the location/property-type median prices used by relevance ranking."""
    segments = Property.objects.values_list("location", "property_type").distinct()
    refreshed = 0
    for location, property_type in segments:
        prices = Property.objects.filter(
            location=location,
            property_type=property_type,
        ).values_list("price", flat=True)
        values = [float(price) for price in prices]
        if not values:
            continue
        cache_key = "median_price_" + hashlib.md5(
            f"{location.strip().lower()}_{property_type.strip().lower()}".encode("utf-8")
        ).hexdigest()
        cache.set(cache_key, statistics.median(values), timeout=90000)
        refreshed += 1
    return refreshed