"""
Favorites — Services
=====================
Business logic for managing favorites.
"""
from typing import Any
from apps.favorites.models import Favorite
from apps.properties.models import Property


def toggle_favorite(user, property: Property) -> dict[str, Any]:
    """
    Toggle a property in the user's favorites list.
    Returns:
        {"action": "added" | "removed", "is_favorited": bool}
    """
    favorite = Favorite.objects.filter(user=user, property=property).first()
    if favorite:
        favorite.delete()
        return {"action": "removed", "is_favorited": False}
    else:
        Favorite.objects.create(user=user, property=property)
        return {"action": "added", "is_favorited": True}
