"""
Inquiries — Serializers
========================
Serializers for creating and viewing buyer inquiries and viewing requests.
"""
from rest_framework import serializers
from apps.inquiries.models import ContactMethod, Inquiry, InquiryType
from apps.properties.serializers import PropertyListSerializer


class InquiryCreateSerializer(serializers.Serializer):
    property_id = serializers.IntegerField(required=False, allow_null=True)
    project_id = serializers.IntegerField(required=False, allow_null=True)
    name = serializers.CharField(max_length=150)
    phone = serializers.CharField(max_length=20)
    message = serializers.CharField(required=False, allow_blank=True, default="")
    inquiry_type = serializers.ChoiceField(
        choices=InquiryType.choices,
        default=InquiryType.MESSAGE,
    )
    preferred_contact_method = serializers.ChoiceField(
        choices=ContactMethod.choices,
        default=ContactMethod.WHATSAPP,
    )
    preferred_time = serializers.DateTimeField(required=False, allow_null=True)


class InquiryListSerializer(serializers.ModelSerializer):
    property = PropertyListSerializer(read_only=True)

    class Meta:
        model = Inquiry
        fields = [
            "id",
            "property",
            "project",
            "name",
            "phone",
            "inquiry_type",
            "status",
            "preferred_contact_method",
            "preferred_time",
            "agent_notified",
            "created_at",
        ]


class InquiryDetailSerializer(serializers.ModelSerializer):
    property = PropertyListSerializer(read_only=True)

    class Meta:
        model = Inquiry
        fields = [
            "id",
            "property",
            "project",
            "name",
            "phone",
            "message",
            "inquiry_type",
            "status",
            "preferred_contact_method",
            "preferred_time",
            "agent_notified",
            "created_at",
            "updated_at",
        ]


class DeveloperLeadUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=[("pending", "قيد الانتظار"), ("contacted", "تم التواصل"), ("completed", "مكتمل"), ("cancelled", "ملغي")],
        required=False,
    )
    rating = serializers.ChoiceField(
        choices=[("excellent", "ممتاز"), ("good", "جيد"), ("average", "متوسط"), ("bad", "سيء")],
        required=False,
    )


class DeveloperLeadSerializer(serializers.ModelSerializer):
    property_title = serializers.CharField(source="property.title", read_only=True, default=None)
    project_name = serializers.SerializerMethodField()

    class Meta:
        model = Inquiry
        fields = [
            "id",
            "name",
            "phone",
            "message",
            "inquiry_type",
            "status",
            "rating",
            "source",
            "requirement_summary",
            "property",
            "property_title",
            "project",
            "project_name",
            "agent_notified",
            "created_at",
            "updated_at",
        ]

    def get_project_name(self, obj):
        if obj.project:
            return obj.project.name
        if obj.property and obj.property.project:
            return obj.property.project.name
        return None
