"""
Common — Akedly V1.2 REST API Client (Shield)
================================================
Python port of the Node.js Akedly client.

This module is the entire "connection to Akedly" — every other file in
the authentication app is either validation, URL routing, or wiring.

Credentials (AKEDLY_API_KEY, AKEDLY_PIPELINE_ID) are read from Django
settings only. They are NEVER hardcoded, and this module never sends
them anywhere except https://api.akedly.io.

Docs: https://docs.akedly.io/authentication/v1-2
"""
import logging
import time
from urllib.parse import urlencode

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://api.akedly.io/api/v1.2"
DEFAULT_TIMEOUT_SECONDS = 10


# ─── Errors ──────────────────────────────────────────────────────


class AkedlyApiError(Exception):
    """
    Wraps every non-"success" response from Akedly's API into a single,
    predictable error shape so callers never have to parse Akedly's raw
    JSON error body themselves.

    See: https://docs.akedly.io/authentication/v1-2#error-reference
    """

    def __init__(
        self,
        message: str,
        *,
        status: int = 502,
        code: str = "UNKNOWN_ERROR",
        retryable: bool = False,
        retry_after: str | None = None,
        cooldown_seconds: int | None = None,
        details: dict | None = None,
    ):
        super().__init__(message)
        self.status = status
        self.code = code
        self.retryable = retryable
        self.retry_after = retry_after
        self.cooldown_seconds = cooldown_seconds
        self.details = details

    def to_error_dict(self) -> dict:
        """Serialize to the standard error shape for the API envelope."""
        return {
            "code": self.code,
            "retryable": self.retryable,
            "retry_after": self.retry_after,
            "cooldown_seconds": self.cooldown_seconds,
        }


# ─── Helpers ─────────────────────────────────────────────────────


def _get_credentials() -> tuple[str, str]:
    """Read Akedly credentials from Django settings."""
    api_key = getattr(settings, "AKEDLY_API_KEY", "")
    pipeline_id = getattr(settings, "AKEDLY_PIPELINE_ID", "")
    if not api_key or not pipeline_id:
        raise AkedlyApiError(
            "AKEDLY_API_KEY and AKEDLY_PIPELINE_ID must be set in Django settings. "
            "See .env.example. Never hardcode these values in source.",
            status=500,
            code="MISSING_CREDENTIALS",
        )
    return api_key, pipeline_id


def _parse_akedly_response(response: requests.Response) -> dict:
    """Parse Akedly's { status, data, message } / { status, code, ... } envelope."""
    try:
        body = response.json()
    except (ValueError, requests.exceptions.JSONDecodeError):
        raise AkedlyApiError(
            "Akedly returned a non-JSON response.",
            status=response.status_code,
            code="INVALID_RESPONSE",
            retryable=response.status_code >= 500,
        )

    if body.get("status") != "success":
        raise AkedlyApiError(
            body.get("message", "Akedly request failed."),
            status=response.status_code,
            code=body.get("code", "UNKNOWN_ERROR"),
            retryable=bool(body.get("retryable")),
            retry_after=body.get("retryAfter"),
            cooldown_seconds=body.get("cooldownSeconds"),
            details=body.get("details"),
        )

    return body.get("data", {})


# ─── Public API ──────────────────────────────────────────────────


def get_challenge() -> dict:
    """
    Step 1 — GET a Proof-of-Work challenge + Turnstile config.

    This is a plain, idempotent GET, so it's the one call in this module
    safe to retry automatically on transient failures.

    Returns dict with: challenge, difficulty, challengeToken, turnstile
    """
    api_key, pipeline_id = _get_credentials()

    params = urlencode({"APIKey": api_key, "pipelineID": pipeline_id})
    url = f"{BASE_URL}/transactions/challenge?{params}"

    max_attempts = 3
    last_err = None

    for attempt in range(max_attempts):
        try:
            response = requests.get(url, timeout=DEFAULT_TIMEOUT_SECONDS)
            return _parse_akedly_response(response)
        except AkedlyApiError as err:
            last_err = err
            if not err.retryable or attempt == max_attempts - 1:
                break
            # Exponential backoff: 0.2s, 0.4s
            time.sleep(0.2 * (2 ** attempt))
        except requests.exceptions.Timeout:
            last_err = AkedlyApiError(
                "Request to Akedly timed out.",
                status=504,
                code="CLIENT_TIMEOUT",
                retryable=True,
            )
            if attempt == max_attempts - 1:
                break
            time.sleep(0.2 * (2 ** attempt))
        except requests.exceptions.ConnectionError:
            last_err = AkedlyApiError(
                "Network error contacting Akedly.",
                status=502,
                code="NETWORK_ERROR",
                retryable=True,
            )
            if attempt == max_attempts - 1:
                break
            time.sleep(0.2 * (2 ** attempt))

    raise last_err


def send_otp(
    *,
    verification_address: dict,
    pow_solution: dict,
    turnstile_token: str | None = None,
    digits: int | None = None,
    end_user_ip: str | None = None,
) -> dict:
    """
    Step 2 — Send the OTP.

    Deliberately NOT auto-retried: this call has a real-world side effect
    (a WhatsApp/SMS/Telegram/email message may go out and get billed), and
    Akedly only allows 1 resend per transaction.

    Returns dict with: transactionID, transactionReqID, channels, expiresAt
    """
    api_key, pipeline_id = _get_credentials()

    headers = {"Content-Type": "application/json"}
    if end_user_ip:
        headers["x-end-user-ip"] = end_user_ip

    payload = {
        "APIKey": api_key,
        "pipelineID": pipeline_id,
        "verificationAddress": verification_address,
        "powSolution": pow_solution,
    }
    if turnstile_token:
        payload["turnstileToken"] = turnstile_token
    if digits and digits in (4, 5, 6):
        payload["digits"] = digits

    try:
        response = requests.post(
            f"{BASE_URL}/transactions/send",
            json=payload,
            headers=headers,
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )
    except requests.exceptions.Timeout:
        raise AkedlyApiError(
            "Request to Akedly timed out.",
            status=504,
            code="CLIENT_TIMEOUT",
            retryable=True,
        )
    except requests.exceptions.ConnectionError:
        raise AkedlyApiError(
            "Network error contacting Akedly.",
            status=502,
            code="NETWORK_ERROR",
            retryable=True,
        )

    return _parse_akedly_response(response)


def verify_otp(*, transaction_req_id: str, otp: str) -> dict:
    """
    Step 3 — Verify the code the user typed in.

    Also not auto-retried: each wrong attempt counts toward Akedly's
    server-side 10-attempt cap (MAX_ATTEMPTS_EXCEEDED force-expires the
    transaction).

    Returns dict with: verified, transactionID
    """
    payload = {
        "transactionReqID": transaction_req_id,
        "otp": otp,
    }

    try:
        response = requests.post(
            f"{BASE_URL}/transactions/verify",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )
    except requests.exceptions.Timeout:
        raise AkedlyApiError(
            "Request to Akedly timed out.",
            status=504,
            code="CLIENT_TIMEOUT",
            retryable=True,
        )
    except requests.exceptions.ConnectionError:
        raise AkedlyApiError(
            "Network error contacting Akedly.",
            status=502,
            code="NETWORK_ERROR",
            retryable=True,
        )

    return _parse_akedly_response(response)
