"""
Tests — Authentication Views
===============================
Integration tests for the 3-step Akedly OTP authentication endpoints.
Mocks the Akedly client so no real API calls are made.
"""
import pytest
from unittest.mock import patch, MagicMock

from django.urls import reverse
from rest_framework import status

from apps.common.akedly import AkedlyApiError


pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def akedly_settings(settings):
    """Inject test Akedly credentials into Django settings."""
    settings.AKEDLY_API_KEY = "test-api-key"
    settings.AKEDLY_PIPELINE_ID = "test-pipeline-id"


# ─── GET /api/v1/auth/challenge/ ─────────────────────────────────


class TestChallengeView:
    """Tests for the challenge endpoint."""

    @patch("apps.authentication.services.get_challenge")
    def test_returns_challenge_data(self, mock_get_challenge, api_client):
        """Should return PoW challenge data from Akedly."""
        mock_get_challenge.return_value = {
            "challenge": "abc123",
            "difficulty": 5,
            "challengeToken": "tok-xyz",
            "challengeRequired": True,
            "turnstile": {"required": False},
        }

        response = api_client.get(reverse("auth-challenge"))

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["data"]["challenge"] == "abc123"

    @patch("apps.authentication.services.get_challenge")
    def test_handles_akedly_error(self, mock_get_challenge, api_client):
        """Should return error envelope when Akedly fails."""
        mock_get_challenge.side_effect = AkedlyApiError(
            "Service unavailable",
            status=429,
            code="SERVICE_UNAVAILABLE",
            retryable=True,
        )

        response = api_client.get(reverse("auth-challenge"))

        assert response.status_code == 429
        data = response.json()
        assert data["success"] is False
        assert data["errors"][0]["code"] == "SERVICE_UNAVAILABLE"


# ─── POST /api/v1/auth/send-otp/ ────────────────────────────────


class TestSendOtpView:
    """Tests for the send-otp endpoint."""

    @patch("apps.authentication.services.send_otp")
    def test_success(self, mock_send_otp, api_client):
        """Should send OTP and return transaction data."""
        mock_send_otp.return_value = {
            "transactionID": "txn-001",
            "transactionReqID": "req-001",
            "channels": ["whatsapp"],
            "expiresAt": "2026-08-30T15:00:00Z",
        }

        response = api_client.post(
            reverse("auth-send-otp"),
            data={
                "phone_number": "01012345678",
                "pow_solution": {
                    "challengeToken": "tok-xyz",
                    "nonce": 42,
                },
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

    def test_rejects_invalid_phone(self, api_client):
        """Should return 400 for invalid phone numbers."""
        response = api_client.post(
            reverse("auth-send-otp"),
            data={
                "phone_number": "123",
                "pow_solution": {
                    "challengeToken": "tok-xyz",
                    "nonce": 42,
                },
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_rejects_missing_pow_solution(self, api_client):
        """Should return 400 when pow_solution is missing."""
        response = api_client.post(
            reverse("auth-send-otp"),
            data={
                "phone_number": "01012345678",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_rejects_invalid_digits(self, api_client):
        """Should return 400 when digits is not 4, 5, or 6."""
        response = api_client.post(
            reverse("auth-send-otp"),
            data={
                "phone_number": "01012345678",
                "pow_solution": {
                    "challengeToken": "tok-xyz",
                    "nonce": 42,
                },
                "digits": 8,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ─── POST /api/v1/auth/verify-otp/ ──────────────────────────────


class TestVerifyOtpView:
    """Tests for the verify-otp endpoint."""

    @patch("apps.authentication.services.verify_otp")
    def test_success_creates_user_and_returns_tokens(self, mock_verify_otp, api_client):
        """Should verify OTP, create user, and return JWT tokens."""
        mock_verify_otp.return_value = {
            "verified": True,
            "transactionID": "txn-001",
        }

        response = api_client.post(
            reverse("auth-verify-otp"),
            data={
                "transaction_req_id": "req-001",
                "otp": "1234",
                "phone_number": "01012345678",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]
        assert "access" in data
        assert "refresh" in data
        assert data["is_new_user"] is True
        assert data["user"]["phone"] == "01012345678"

    @patch("apps.authentication.services.verify_otp")
    def test_existing_user_returns_tokens(self, mock_verify_otp, api_client):
        """Should return JWT tokens for an existing user."""
        from apps.users.models import User

        # Create existing user
        user = User(phone="01012345678", name="Ahmed", birthday="1990-01-01", is_active=True)
        user.set_unusable_password()
        user.save()

        mock_verify_otp.return_value = {
            "verified": True,
            "transactionID": "txn-001",
        }

        response = api_client.post(
            reverse("auth-verify-otp"),
            data={
                "transaction_req_id": "req-001",
                "otp": "1234",
                "phone_number": "01012345678",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]
        assert data["is_new_user"] is False
        assert data["user"]["name"] == "Ahmed"

    def test_rejects_invalid_otp_format(self, api_client):
        """Should return 400 for non-numeric OTP."""
        response = api_client.post(
            reverse("auth-verify-otp"),
            data={
                "transaction_req_id": "req-001",
                "otp": "abcd",
                "phone_number": "01012345678",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_rejects_missing_transaction_req_id(self, api_client):
        """Should return 400 when transaction_req_id is missing."""
        response = api_client.post(
            reverse("auth-verify-otp"),
            data={
                "otp": "1234",
                "phone_number": "01012345678",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch("apps.authentication.services.verify_otp")
    def test_handles_akedly_error(self, mock_verify_otp, api_client):
        """Should return error envelope when Akedly verification fails."""
        mock_verify_otp.side_effect = AkedlyApiError(
            "Maximum attempts exceeded",
            status=403,
            code="MAX_ATTEMPTS_EXCEEDED",
            retryable=False,
        )

        response = api_client.post(
            reverse("auth-verify-otp"),
            data={
                "transaction_req_id": "req-001",
                "otp": "9999",
                "phone_number": "01012345678",
            },
            format="json",
        )

        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False
        assert data["errors"][0]["code"] == "MAX_ATTEMPTS_EXCEEDED"


# ─── POST /api/v1/auth/token/refresh/ ───────────────────────────


class TestTokenRefreshView:
    """Tests for the token refresh endpoint."""

    def test_refresh_success(self, api_client):
        """Should return a new access token when a valid refresh token is provided."""
        from apps.users.models import User
        from rest_framework_simplejwt.tokens import RefreshToken

        user = User.objects.create_user(
            phone="01012345678",
            password="SecurePassword123!",
            name="Test User",
            birthday="1995-05-15",
            is_active=True,
        )
        refresh = RefreshToken.for_user(user)

        response = api_client.post(
            reverse("token-refresh"),
            data={"refresh": str(refresh)},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "access" in data["data"]

    def test_refresh_invalid_token(self, api_client):
        """Should return 401 error envelope when token is invalid."""
        response = api_client.post(
            reverse("token-refresh"),
            data={"refresh": "invalid-token"},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert data["success"] is False


# ─── POST /api/v1/auth/logout/ ──────────────────────────────────


class TestLogoutView:
    """Tests for the logout endpoint."""

    @pytest.fixture(autouse=True)
    def setup_user(self):
        from apps.users.models import User
        self.user = User.objects.create_user(
            phone="01012345678",
            password="SecurePassword123!",
            name="Test User",
            birthday="1995-05-15",
            is_active=True,
        )
        self.url = reverse("auth-logout")

    def test_logout_unauthenticated(self, api_client):
        """Should return 401 for unauthenticated requests."""
        response = api_client.post(self.url, data={"refresh": "token"}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_missing_refresh_token(self, api_client):
        """Should return 400 when refresh token is missing."""
        api_client.force_authenticate(user=self.user)
        response = api_client.post(self.url, data={}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["success"] is False
        assert "refresh" in data["errors"]

    def test_logout_success(self, api_client):
        """Should blacklist the refresh token and return success."""
        from rest_framework_simplejwt.tokens import RefreshToken

        api_client.force_authenticate(user=self.user)
        refresh = RefreshToken.for_user(self.user)

        response = api_client.post(
            self.url,
            data={"refresh": str(refresh)},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "message" in data

        # Trying to use the blacklisted token again should fail
        refresh_url = reverse("token-refresh")
        refresh_response = api_client.post(
            refresh_url,
            data={"refresh": str(refresh)},
            format="json",
        )
        assert refresh_response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_invalid_token(self, api_client):
        """Should return 400 when refresh token is invalid."""
        api_client.force_authenticate(user=self.user)
        response = api_client.post(
            self.url,
            data={"refresh": "invalid-token"},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["success"] is False
        assert "refresh" in data["errors"]

