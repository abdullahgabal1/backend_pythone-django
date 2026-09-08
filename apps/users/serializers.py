"""
Users — Serializers
=====================
Serializers for user profile reading and updating.
"""
from rest_framework import serializers

from apps.users.models import User
from apps.common.validators import validate_egyptian_phone, validate_birthday


class UserProfileSerializer(serializers.ModelSerializer):
    """Read-only serializer for the current user's profile."""

    class Meta:
        model = User
        fields = ("id", "phone", "name", "birthday", "role", "created_at")
        read_only_fields = fields


class UserUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating mutable profile fields.
    Phone is NOT updatable — it's the account identifier.
    """

    name = serializers.CharField(max_length=100, required=False)
    birthday = serializers.DateField(required=False, validators=[validate_birthday])

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError("يجب تقديم حقل واحد على الأقل للتحديث.")
        return attrs
