"""
Tests — Akedly API Client
============================
Unit tests for apps.common.akedly — mocks the requests library
to test all three API calls without hitting the real Akedly service.
"""
import pytest
from unittest.mock import patch, MagicMock

from apps.common.akedly import (
    AkedlyApiError,
    get_challenge,
    send_otp,
    verify_otp,
)


@pytest.fixture(autouse=True)
def akedly_settings(settings):
    """Inject test Akedly credentials into Django settings."""
    settings.AKEDLY_API_KEY = "test-api-key"
    settings.AKEDLY_PIPELINE_ID = "test-pipeline-id"


def _mock_response(status_code=200, json_data=None):
    """Create a mock requests.Response."""
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = json_data or {}
    return mock_resp


# ─── get_challenge() ─────────────────────────────────────────────


class TestGetChallenge:
    """Tests for the GET /transactions/challenge call."""

    @patch("apps.common.akedly.requests.get")
    def test_success(self, mock_get):
        """Should return challenge data on success."""
        mock_get.return_value = _mock_response(200, {
            "status": "success",
            "data": {
                "challenge": "abc123",
                "difficulty": 5,
                "challengeToken": "tok-xyz",
                "challengeRequired": True,
                "turnstile": {"required": False},
            },
        })

        result = get_challenge()

        assert result["challenge"] == "abc123"
        assert result["difficulty"] == 5
        assert result["challengeToken"] == "tok-xyz"
        mock_get.assert_called_once()

    @patch("apps.common.akedly.requests.get")
    def test_retries_on_transient_failure(self, mock_get):
        """Should retry up to 3 times on transient (5xx) failures."""
        # First two calls fail with 500, third succeeds
        mock_get.side_effect = [
            _mock_response(500, {
                "status": "error",
                "message": "Internal error",
                "code": "INTERNAL_ERROR",
                "retryable": True,
            }),
            _mock_response(500, {
                "status": "error",
                "message": "Internal error",
                "code": "INTERNAL_ERROR",
                "retryable": True,
            }),
            _mock_response(200, {
                "status": "success",
                "data": {"challenge": "retry-ok"},
            }),
        ]

        result = get_challenge()
        assert result["challenge"] == "retry-ok"
        assert mock_get.call_count == 3

    @patch("apps.common.akedly.requests.get")
    def test_raises_on_non_retryable_error(self, mock_get):
        """Should raise immediately on non-retryable errors."""
        mock_get.return_value = _mock_response(401, {
            "status": "error",
            "message": "Invalid API key",
            "code": "INVALID_API_KEY",
            "retryable": False,
        })

        with pytest.raises(AkedlyApiError) as exc_info:
            get_challenge()

        assert exc_info.value.code == "INVALID_API_KEY"
        assert exc_info.value.status == 401
        assert mock_get.call_count == 1

    def test_raises_without_credentials(self, settings):
        """Should raise if AKEDLY_API_KEY is not set."""
        settings.AKEDLY_API_KEY = ""

        with pytest.raises(AkedlyApiError) as exc_info:
            get_challenge()

        assert exc_info.value.code == "MISSING_CREDENTIALS"


# ─── send_otp() ─────────────────────────────────────────────────


class TestSendOtp:
    """Tests for the POST /transactions/send call."""

    @patch("apps.common.akedly.requests.post")
    def test_success(self, mock_post):
        """Should return transaction data on success."""
        mock_post.return_value = _mock_response(200, {
            "status": "success",
            "data": {
                "transactionID": "txn-001",
                "transactionReqID": "req-001",
                "channels": ["whatsapp", "sms"],
                "expiresAt": "2026-08-30T15:00:00Z",
            },
        })

        result = send_otp(
            verification_address={"phoneNumber": "+201012345678"},
            pow_solution={"challengeToken": "tok-xyz", "nonce": 42},
        )

        assert result["transactionID"] == "txn-001"
        assert result["transactionReqID"] == "req-001"
        assert "whatsapp" in result["channels"]
        mock_post.assert_called_once()

    @patch("apps.common.akedly.requests.post")
    def test_raises_on_rate_limit(self, mock_post):
        """Should raise AkedlyApiError with cooldown info on 429."""
        mock_post.return_value = _mock_response(429, {
            "status": "error",
            "message": "Rate limited",
            "code": "RATE_LIMITED",
            "retryable": True,
            "cooldownSeconds": 30,
        })

        with pytest.raises(AkedlyApiError) as exc_info:
            send_otp(
                verification_address={"phoneNumber": "+201012345678"},
                pow_solution={"challengeToken": "tok-xyz", "nonce": 42},
            )

        assert exc_info.value.code == "RATE_LIMITED"
        assert exc_info.value.cooldown_seconds == 30


# ─── verify_otp() ───────────────────────────────────────────────


class TestVerifyOtp:
    """Tests for the POST /transactions/verify call."""

    @patch("apps.common.akedly.requests.post")
    def test_success(self, mock_post):
        """Should return verified=True on correct OTP."""
        mock_post.return_value = _mock_response(200, {
            "status": "success",
            "data": {
                "verified": True,
                "transactionID": "txn-001",
            },
        })

        result = verify_otp(transaction_req_id="req-001", otp="1234")

        assert result["verified"] is True
        assert result["transactionID"] == "txn-001"

    @patch("apps.common.akedly.requests.post")
    def test_raises_on_wrong_otp(self, mock_post):
        """Should raise AkedlyApiError on wrong OTP code."""
        mock_post.return_value = _mock_response(400, {
            "status": "error",
            "message": "Invalid OTP",
            "code": "INVALID_OTP",
            "retryable": False,
        })

        with pytest.raises(AkedlyApiError) as exc_info:
            verify_otp(transaction_req_id="req-001", otp="0000")

        assert exc_info.value.code == "INVALID_OTP"

    @patch("apps.common.akedly.requests.post")
    def test_raises_on_max_attempts(self, mock_post):
        """Should raise AkedlyApiError when max attempts exceeded."""
        mock_post.return_value = _mock_response(403, {
            "status": "error",
            "message": "Maximum attempts exceeded",
            "code": "MAX_ATTEMPTS_EXCEEDED",
            "retryable": False,
        })

        with pytest.raises(AkedlyApiError) as exc_info:
            verify_otp(transaction_req_id="req-001", otp="9999")

        assert exc_info.value.code == "MAX_ATTEMPTS_EXCEEDED"
        assert exc_info.value.status == 403
