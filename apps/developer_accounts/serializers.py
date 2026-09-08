"""
Developer Accounts — Serializers
==================================
Serializers for login, account/profile management, and team member CRUD.
"""
from rest_framework import serializers

from apps.developer_accounts.models import DeveloperUser, Permission


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ["id", "codename", "name"]


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class DeveloperUserSerializer(serializers.ModelSerializer):
    """Read serializer for developer user with nested permissions."""

    permissions = PermissionSerializer(many=True, read_only=True)

    class Meta:
        model = DeveloperUser
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "avatar",
            "is_primary",
            "status",
            "permissions",
            "created_at",
        ]


class AccountUpdateSerializer(serializers.Serializer):
    """Update profile — name, email, avatar, or password."""

    first_name = serializers.CharField(max_length=100, required=False)
    last_name = serializers.CharField(max_length=100, required=False)
    email = serializers.EmailField(required=False)
    avatar = serializers.ImageField(required=False, allow_null=True)
    current_password = serializers.CharField(write_only=True, required=False)
    new_password = serializers.CharField(write_only=True, required=False, min_length=8)

    def validate(self, attrs):
        new_password = attrs.get("new_password")
        current_password = attrs.get("current_password")
        if new_password and not current_password:
            raise serializers.ValidationError(
                {"current_password": "كلمة المرور الحالية مطلوبة لتغيير كلمة المرور."}
            )
        return attrs


class TeamMemberCreateSerializer(serializers.Serializer):
    """Invite a new team member to the account."""

    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    password = serializers.CharField(write_only=True, min_length=8)
    permission_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=list,
    )


class TeamMemberSerializer(serializers.ModelSerializer):
    """Read serializer for team listing."""

    permissions = PermissionSerializer(many=True, read_only=True)

    class Meta:
        model = DeveloperUser
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "avatar",
            "is_primary",
            "status",
            "permissions",
            "created_at",
        ]


class TeamMemberUpdateSerializer(serializers.Serializer):
    """Update a team member's info or permissions."""

    first_name = serializers.CharField(max_length=100, required=False)
    last_name = serializers.CharField(max_length=100, required=False)
    permission_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
    )
    status = serializers.ChoiceField(
        choices=[("active", "Active"), ("inactive", "Inactive")],
        required=False,
    )
