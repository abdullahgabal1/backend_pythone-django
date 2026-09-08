"""
Search — Ranking & Relevance Scoring
=====================================
Ordering and Weighted Relevance Scoring Algorithm for property search results.
"""
import hashlib
import math
import statistics
from decimal import Decimal
from typing import Any, Optional

from django.core.cache import cache
from django.db.models import Case, QuerySet, When
from django.utils import timezone

from apps.properties.models import Property


def _get_segment_median_price(location: str, property_type: str) -> Optional[float]:
    """
    Get or compute median price for (location, property_type) segment.
    Cached for 1 hour.
    """
    loc_clean = (location or "all").strip().lower()
    pt_clean = (property_type or "all").strip().lower()
    key_hash = hashlib.md5(f"{loc_clean}_{pt_clean}".encode("utf-8")).hexdigest()
    cache_key = f"median_price_{key_hash}"
    cached_val = cache.get(cache_key)
    if cached_val is not None:
        return cached_val

    qs = Property.objects.all()
    if location:
        qs = qs.filter(location__icontains=location.strip())
    if property_type:
        qs = qs.filter(property_type=property_type)

    prices = list(qs.values_list("price", flat=True)[:500])
    if not prices:
        return None

    median_val = float(statistics.median([float(p) for p in prices]))
    cache.set(cache_key, median_val, timeout=3600)
    return median_val


def compute_relevance_score(
    property_obj: Property,
    filters: Optional[dict[str, Any]] = None,
    now: Optional[timezone.datetime] = None,
) -> float:
    """
    Weighted Relevance Scoring:
    score = 0.3 * recency + 0.2 * completeness + 0.3 * price_competitiveness + 0.2 * filter_match
    """
    if now is None:
        now = timezone.now()

    # 1. Recency (exponential decay based on age in days)
    age_days = max(0.0, (now - property_obj.created_at).total_seconds() / 86400.0)
    recency = math.exp(-age_days / 30.0)

    # 2. Completeness (images, agent, description length)
    has_images = 1.0 if getattr(property_obj, "images_count", None) or property_obj.images.exists() else 0.0
    has_agent = 1.0 if property_obj.agent_id else 0.0
    desc_len = len(property_obj.description.strip()) if property_obj.description else 0
    desc_score = min(1.0, desc_len / 150.0)
    completeness = 0.4 * has_images + 0.3 * has_agent + 0.3 * desc_score

    # 3. Price competitiveness (proximity to segment median)
    median_price = _get_segment_median_price(property_obj.location, property_obj.property_type)
    if median_price and median_price > 0:
        price_diff = abs(float(property_obj.price) - median_price)
        price_competitiveness = max(0.0, 1.0 - (price_diff / median_price))
    else:
        price_competitiveness = 0.5

    # 4. Filter match (evaluates optional feature matches)
    match_points = 0.0
    total_points = 1.0  # Base point
    if property_obj.is_featured:
        match_points += 0.5
    if property_obj.parking > 0:
        match_points += 0.5

    filters = filters or {}
    amenities_filter = filters.get("amenities")
    if amenities_filter:
        total_points += 1.0
        prop_amenities = set(property_obj.amenities.values_list("name", flat=True))
        req_amenities = [a.strip() for a in amenities_filter.split(",") if a.strip()]
        if req_amenities:
            match_points += len(set(req_amenities).intersection(prop_amenities)) / len(req_amenities)

    filter_match = min(1.0, match_points / max(1.0, total_points))

    score = (
        0.3 * recency
        + 0.2 * completeness
        + 0.3 * price_competitiveness
        + 0.2 * filter_match
    )
    return round(score, 4)


def apply_ordering(
    queryset: QuerySet[Property],
    ordering: Optional[str] = None,
    filters: Optional[dict[str, Any]] = None,
) -> QuerySet[Property]:
    """
    Applies sorting to queryset.
    Supports:
    - 'date-desc' / 'newest': newest first
    - 'price-asc': cheapest first
    - 'price-desc': most expensive first
    - 'area-desc': largest area first
    - 'relevance': Weighted Relevance Scoring Algorithm
    """
    if not ordering:
        ordering = "date-desc"

    order_clean = ordering.strip().lower()

    if order_clean in ("date-desc", "newest"):
        return queryset.order_by("-created_at")
    elif order_clean in ("price-asc", "cheapest"):
        return queryset.order_by("price", "-created_at")
    elif order_clean in ("price-desc", "expensive"):
        return queryset.order_by("-price", "-created_at")
    elif order_clean in ("area-desc", "largest"):
        return queryset.order_by("-area_sqm", "-created_at")
    elif order_clean == "relevance":
        props = list(queryset.prefetch_related("images", "amenities").select_related("agent"))
        if not props:
            return queryset

        now = timezone.now()
        scored_props = [
            (p, compute_relevance_score(p, filters=filters, now=now))
            for p in props
        ]
        # Sort descending by score, tie-break on created_at
        scored_props.sort(key=lambda item: (item[1], item[0].created_at), reverse=True)
        sorted_ids = [p.id for p, _ in scored_props]

        preserved_order = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(sorted_ids)])
        return queryset.filter(id__in=sorted_ids).order_by(preserved_order)

    return queryset.order_by("-created_at")
