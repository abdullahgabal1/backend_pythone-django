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
