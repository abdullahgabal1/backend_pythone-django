"""
Properties — Tasks
====================
Scheduled background tasks for properties app.
"""
import logging
from celery import shared_task
from django.db.models import Avg
from apps.properties.models import Property

logger = logging.getLogger(__name__)


@shared_task
def calculate_location_averages():
    """
    Calculate and cache the average price per location.
    Runs periodically via Celery Beat (e.g. nightly).
    Results are cached for dashboard consumption.

    NOTE: This computes averages, not medians. For actual median price
    calculations (used in relevance scoring), see
    apps.search.ranking._get_segment_median_price.
    """
    from django.core.cache import cache

    logger.info("Starting location average price calculation...")

    locations = (
        Property.objects
        .values("location")
        .annotate(avg_price=Avg("price"))
        .order_by("-avg_price")
    )

    averages = {}
    for loc in locations:
        if loc["location"]:
            averages[loc["location"]] = float(loc["avg_price"])

    # Cache for 25 hours (the task runs daily)
    cache.set("location_price_medians", averages, timeout=90000)

    logger.info("Finished location average calculation. %d locations processed.", len(averages))
    return averages
