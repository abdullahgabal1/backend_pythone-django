"""
Projects — Serializers
========================
Serializers for project CRUD.
"""
from rest_framework import serializers
from apps.locations.serializers import LocationSerializer
from apps.projects.models import Project, ProjectImage

class ProjectImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectImage
        fields = ["id", "image", "order"]

class ProjectListSerializer(serializers.ModelSerializer):
    location = LocationSerializer(read_only=True)
    
    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "project_type",
            "location",
            "price_per_meter",
            "status",
            "main_image",
            "created_at",
        ]

class ProjectDetailSerializer(serializers.ModelSerializer):
    location = LocationSerializer(read_only=True)
    gallery = ProjectImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "project_type",
            "location",
            "price_per_meter",
            "description",
            "status",
            "main_image",
            "document",
            "gallery",
            "created_at",
            "updated_at",
        ]

class ProjectWriteSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    project_type = serializers.ChoiceField(choices=[("residential", "سكني"), ("commercial", "تجاري"), ("medical", "طبي")])
    location_id = serializers.IntegerField()
    price_per_meter = serializers.DecimalField(max_digits=12, decimal_places=2)
    description = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(choices=[("active", "نشط"), ("inactive", "غير نشط")], required=False)
