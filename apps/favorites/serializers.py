"""
Favorites — Serializers
========================
Serializers for user saved properties.
"""
from rest_framework import serializers
from apps.favorites.models import Favorite
from apps.properties.serializers import PropertyListSerializer


class FavoriteSerializer(serializers.ModelSerializer):
    property = PropertyListSerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = ["id", "property", "created_at"]
