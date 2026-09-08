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
def calculate_location_medians():
    """
    Calculate and log the average price per location.
    Runs periodically via Celery Beat (e.g. nightly).
    Results are cached for dashboard consumption.
    """
    from django.core.cache import cache

    logger.info("Starting location median calculation...")

    locations = (
        Property.objects.filter(view_count__gte=0)  # all active
        .values("location")
        .annotate(avg_price=Avg("price"))
        .order_by("-avg_price")
    )

    medians = {}
    for loc in locations:
        if loc["location"]:
            medians[loc["location"]] = float(loc["avg_price"])

    # Cache for 25 hours (the task runs daily)
    cache.set("location_price_medians", medians, timeout=90000)

    logger.info("Finished location median calculation. %d locations processed.", len(medians))
    return medians
