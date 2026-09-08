"""
Properties — Services
======================
Business logic for property catalog operations.
"""
from django.core.cache import cache
from django.db import models
from apps.properties.models import Property


def increment_view_count(property: Property, request) -> None:
    """
    Increment property view count at most once per client (IP/session/user)
    within a short TTL window (5 minutes) to prevent refresh spamming.
    """
    client_id = "unknown"
    if request:
        if getattr(request, "user", None) and request.user.is_authenticated:
            client_id = f"user_{request.user.id}"
        elif hasattr(request, "session") and request.session.session_key:
            client_id = f"session_{request.session.session_key}"
        elif hasattr(request, "META"):
            x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
            if x_forwarded_for:
                client_id = f"ip_{x_forwarded_for.split(',')[0].strip()}"
            else:
                client_id = f"ip_{request.META.get('REMOTE_ADDR', 'unknown')}"

    cache_key = f"viewed_prop_{property.pk}_{client_id}"

    if not cache.get(cache_key):
        Property.objects.filter(pk=property.pk).update(view_count=models.F("view_count") + 1)
        property.refresh_from_db(fields=["view_count"])
        cache.set(cache_key, 1, timeout=300)
