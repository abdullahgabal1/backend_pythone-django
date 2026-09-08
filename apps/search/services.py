"""
Search — Services
==================
Filter engine implementing the complete search contract from the frontend.
"""
from decimal import Decimal, InvalidOperation
from typing import Any, Optional
from django.db.models import Q, QuerySet

from apps.properties.models import Property
from apps.search.ranking import apply_ordering

PROPERTY_TYPE_MAP = {
    # Arabic Plural Aliases
    "شقق": "apartment",
    "فلل": "villa",
    "شاليهات": "chalet",
    "مكاتب": "office",
    # Arabic Singular
    "شقة": "apartment",
    "فيلا": "villa",
    "تاون هاوس": "townhouse",
    "بنتهاوس": "penthouse",
    "شاليه": "chalet",
    "دوبلكس": "duplex",
    "مكتب": "office",
    # English
    "apartment": "apartment",
    "villa": "villa",
    "townhouse": "townhouse",
    "penthouse": "penthouse",
    "chalet": "chalet",
    "duplex": "duplex",
    "office": "office",
}

COMPLETION_STATUS_MAP = {
    "ready": "ready",
    "جاهز للتسليم": "ready",
    "جاهز": "ready",
    "off_plan": "off_plan",
    "off-plan": "off_plan",
    "تحت الإنشاء": "off_plan",
}

FURNISHING_MAP = {
    "furnished": "furnished",
    "مفروش": "furnished",
    "semi_furnished": "semi_furnished",
    "semi-furnished": "semi_furnished",
    "نصف مفروش": "semi_furnished",
    "unfurnished": "unfurnished",
    "غير مفروش": "unfurnished",
}

PAYMENT_MAP = {
    "cash": "cash",
    "نقداً": "cash",
    "نقد": "cash",
    "installment": "installment",
    "تقسيط": "installment",
    "mortgage": "mortgage",
    "رهن عقاري": "mortgage",
    "تمويل عقاري": "mortgage",
}


def search_properties(
    filters: Optional[dict[str, Any]] = None,
    ordering: Optional[str] = None,
) -> QuerySet[Property]:
    """
    Search and filter properties matching the full frontend filter contract.
    """
    queryset = (
        Property.objects.select_related("agent")
        .prefetch_related("images", "amenities")
        .all()
    )

    if not filters:
        return apply_ordering(queryset, ordering=ordering, filters={})

    # 1. Location (icontains)
    location = filters.get("location")
    if location and str(location).strip():
        queryset = queryset.filter(location__icontains=str(location).strip())

    # 2. Property Types (comma-separated, IN with alias map)
    property_types = filters.get("propertyTypes") or filters.get("property_types")
    if property_types:
        raw_types = [t.strip().lower() for t in str(property_types).split(",") if t.strip()]
        mapped_types = set()
        for t in raw_types:
            mapped = PROPERTY_TYPE_MAP.get(t) or PROPERTY_TYPE_MAP.get(t.lower())
            if mapped:
                mapped_types.add(mapped)
        if mapped_types:
            queryset = queryset.filter(property_type__in=mapped_types)

    # 3. Bedrooms ("ستوديو" -> 0, "7+" -> >=7, exact numbers)
    bedrooms = filters.get("bedrooms")
    if bedrooms:
        bed_tokens = [b.strip() for b in str(bedrooms).split(",") if b.strip()]
        bed_q = Q()
        exact_beds = []
        for token in bed_tokens:
            token_lower = token.lower()
            if token in ("ستوديو", "studio", "0"):
                bed_q |= Q(beds=0)
            elif token in ("7+", ">=7"):
                bed_q |= Q(beds__gte=7)
            elif token.isdigit():
                exact_beds.append(int(token))
        if exact_beds:
            bed_q |= Q(beds__in=exact_beds)
        if bed_q:
            queryset = queryset.filter(bed_q)

    # 4. Bathrooms ("7+" -> >=7, exact numbers)
    bathrooms = filters.get("bathrooms")
    if bathrooms:
        bath_tokens = [b.strip() for b in str(bathrooms).split(",") if b.strip()]
        bath_q = Q()
        exact_baths = []
        for token in bath_tokens:
            if token in ("7+", ">=7"):
                bath_q |= Q(baths__gte=7)
            elif token.isdigit():
                exact_baths.append(int(token))
        if exact_baths:
            bath_q |= Q(baths__in=exact_baths)
        if bath_q:
            queryset = queryset.filter(bath_q)

    # 5. Price range
    min_price = filters.get("minPrice")
    if min_price is not None and str(min_price).strip() != "":
        try:
            queryset = queryset.filter(price__gte=Decimal(str(min_price)))
        except (InvalidOperation, ValueError):
            pass

    max_price = filters.get("maxPrice")
    if max_price is not None and str(max_price).strip() != "":
        try:
            queryset = queryset.filter(price__lte=Decimal(str(max_price)))
        except (InvalidOperation, ValueError):
            pass

    # 6. Area range
    min_area = filters.get("minArea")
    if min_area is not None and str(min_area).strip() != "":
        try:
            queryset = queryset.filter(area_sqm__gte=int(str(min_area)))
        except ValueError:
            pass

    max_area = filters.get("maxArea")
    if max_area is not None and str(max_area).strip() != "":
        try:
            queryset = queryset.filter(area_sqm__lte=int(str(max_area)))
        except ValueError:
            pass

    # 7. Completion Status
    completion_status = filters.get("completionStatus") or filters.get("completion_status")
    if completion_status and str(completion_status).strip():
        raw_status = str(completion_status).strip().lower()
        mapped_status = COMPLETION_STATUS_MAP.get(raw_status, raw_status)
        queryset = queryset.filter(completion_status=mapped_status)

    # 8. Furnishing (comma-separated IN)
    furnishing = filters.get("furnishing")
    if furnishing:
        raw_furn = [f.strip().lower() for f in str(furnishing).split(",") if f.strip()]
        mapped_furn = {FURNISHING_MAP.get(f, f) for f in raw_furn}
        if mapped_furn:
            queryset = queryset.filter(furnishing__in=mapped_furn)

    # 9. Amenities (comma-separated, AND logic: property must have ALL)
    amenities = filters.get("amenities")
    if amenities:
        amenity_names = [a.strip() for a in str(amenities).split(",") if a.strip()]
        for amenity in amenity_names:
            queryset = queryset.filter(amenities__name__iexact=amenity)

    # 10. Payment Method (parameter name is 'payment' from frontend)
    payment = filters.get("payment") or filters.get("paymentMethod") or filters.get("payment_method")
    if payment:
        raw_pay = [p.strip().lower() for p in str(payment).split(",") if p.strip()]
        mapped_pay = {PAYMENT_MAP.get(p, p) for p in raw_pay}
        if mapped_pay:
            queryset = queryset.filter(payment_method__in=mapped_pay)

    # Ordering / Sorting (delegated to ranking.py)
    sort_by = ordering or filters.get("sortBy") or filters.get("ordering")
    return apply_ordering(queryset, ordering=sort_by, filters=filters)
