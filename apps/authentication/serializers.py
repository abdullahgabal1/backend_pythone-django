"""
Authentication — Serializers
===============================
Request/response serializers for the 3-step Akedly OTP flow.
"""
import re

from rest_framework import serializers

from apps.common.validators import validate_egyptian_phone
from apps.users.serializers import UserProfileSerializer


# ─── Step 2: Send OTP ────────────────────────────────────────────


class PowSolutionSerializer(serializers.Serializer):
    """Nested serializer for the Proof-of-Work solution."""

    challengeToken = serializers.CharField(required=True)
    nonce = serializers.IntegerField(required=True)


class SendOtpSerializer(serializers.Serializer):
    """
    Validates the request body for sending an OTP.
    Server-side validation — never trust the frontend's own checks.
    """

    phone_number = serializers.CharField(required=True)
    pow_solution = PowSolutionSerializer(required=True)
    turnstile_token = serializers.CharField(required=False, allow_blank=True)
    digits = serializers.IntegerField(required=False)

    def validate_phone_number(self, value):
        """Validate and normalize Egyptian phone number."""
        return validate_egyptian_phone(value)

    def validate_digits(self, value):
        """digits must be 4, 5, or 6 if provided."""
        if value not in (4, 5, 6):
            raise serializers.ValidationError(
                "digits must be 4, 5, or 6 if provided."
            )
        return value


# ─── Step 3: Verify OTP ─────────────────────────────────────────


class VerifyOtpSerializer(serializers.Serializer):
    """
    Validates the request body for verifying an OTP code.
    """

    transaction_req_id = serializers.CharField(required=True)
    otp = serializers.CharField(required=True)
    phone_number = serializers.CharField(required=True)

    def validate_transaction_req_id(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("transactionReqID is required.")
        return value.strip()

    def validate_otp(self, value):
        """OTP must be a 4-6 digit numeric string."""
        if not re.match(r"^\d{4,6}$", value):
            raise serializers.ValidationError(
                "A valid 4-6 digit numeric OTP code is required."
            )
        return value

    def validate_phone_number(self, value):
        """Validate and normalize Egyptian phone number."""
        return validate_egyptian_phone(value)


# ─── Response: Auth Tokens ───────────────────────────────────────


class AuthTokenSerializer(serializers.Serializer):
    """Read-only serializer for the authentication response."""

    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)
    is_new_user = serializers.BooleanField(read_only=True)
    user = UserProfileSerializer(read_only=True)
