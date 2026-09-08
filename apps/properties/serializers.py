"""
Properties — Serializers
=========================
Serializers for property catalog (Agent, PropertyImage, PropertyList, PropertyDetail).
"""
from rest_framework import serializers
from apps.properties.models import Agent, Amenity, Property, PropertyImage


class AgentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agent
        fields = ["id", "name", "phone", "image"]


class PropertyImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyImage
        fields = ["id", "image", "order", "is_cover"]


class PropertyListSerializer(serializers.ModelSerializer):
    cover_image = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = [
            "id",
            "title",
            "location",
            "price",
            "price_suffix",
            "area_sqm",
            "beds",
            "baths",
            "property_type",
            "completion_status",
            "cover_image",
            "is_featured",
            "created_at",
        ]

    def get_cover_image(self, obj: Property) -> str | None:
        # Check prefetched images cache first to avoid extra queries
        prefetched = getattr(obj, "_prefetched_objects_cache", {})
        images = prefetched.get("images")
        if images is not None:
            cover = next((img for img in images if img.is_cover), None)
            if not cover and len(images) > 0:
                cover = sorted(images, key=lambda img: img.order)[0]
            return cover.image if cover else None

        cover = obj.images.filter(is_cover=True).first() or obj.images.order_by("order").first()
        return cover.image if cover else None


class PropertyDetailSerializer(serializers.ModelSerializer):
    agent = AgentSerializer(read_only=True)
    images = PropertyImageSerializer(many=True, read_only=True)
    amenities = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="name",
    )

    class Meta:
        model = Property
        fields = [
            "id",
            "title",
            "description",
            "location",
            "price",
            "price_suffix",
            "area_sqm",
            "beds",
            "baths",
            "property_type",
            "completion_status",
            "furnishing",
            "payment_method",
            "parking",
            "agent",
            "amenities",
            "images",
            "is_featured",
            "view_count",
            "created_at",
            "updated_at",
        ]
