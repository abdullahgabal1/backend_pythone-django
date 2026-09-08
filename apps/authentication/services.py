"""
Authentication — Business Logic Services
===========================================
Orchestrates the Akedly OTP flow and user authentication.
"""
import logging

from rest_framework_simplejwt.tokens import RefreshToken

from apps.common.akedly import get_challenge, send_otp, verify_otp
from apps.common.validators import validate_egyptian_phone
from apps.users.models import User

logger = logging.getLogger(__name__)


def get_akedly_challenge() -> dict:
    """
    Step 1 — Fetch a Proof-of-Work challenge from Akedly.
    Returns the challenge data for the frontend to solve.
    """
    return get_challenge()


def send_akedly_otp(
    *,
    phone_number: str,
    pow_solution: dict,
    turnstile_token: str | None = None,
    digits: int | None = None,
    end_user_ip: str | None = None,
) -> dict:
    """
    Step 2 — Send an OTP to the user's phone via Akedly.

    Normalizes the phone number to E.164 format before sending
    because Akedly expects +201XXXXXXXXX.
    """
    # Normalize to local format first (our validator does this)
    normalized_local = validate_egyptian_phone(phone_number)

    # Convert to E.164 for Akedly: 01XXXXXXXXX → +201XXXXXXXXX
    e164_phone = f"+2{normalized_local}"

    return send_otp(
        verification_address={"phoneNumber": e164_phone},
        pow_solution=pow_solution,
        turnstile_token=turnstile_token,
        digits=digits,
        end_user_ip=end_user_ip,
    )


def verify_akedly_otp_and_authenticate(
    *,
    transaction_req_id: str,
    otp: str,
    phone_number: str,
) -> dict:
    """
    Step 3 — Verify the OTP code and authenticate the user.

    After Akedly confirms the OTP is correct:
    1. Get or create the user by phone number
    2. Activate the user (is_active=True)
    3. Generate JWT tokens via SimpleJWT
    4. Return tokens + user data

    If the user doesn't exist yet, auto-creates with just the phone number.
    They can fill in name + birthday later via PATCH /api/v1/account/me/.
    """
    # Verify with Akedly
    result = verify_otp(
        transaction_req_id=transaction_req_id,
        otp=otp,
    )

    if not result.get("verified"):
        return {"verified": False}

    # Normalize phone to local format for DB lookup
    normalized_phone = validate_egyptian_phone(phone_number)

    # Get or create user
    is_new_user = False
    try:
        user = User.objects.get(phone=normalized_phone)
    except User.DoesNotExist:
        is_new_user = True
        user = User(
            phone=normalized_phone,
            name="",
            birthday="2000-01-01",  # Placeholder — user updates via profile
            is_active=True,
        )
        user.set_unusable_password()
        user.save()
        logger.info("Created new user for phone: %s", normalized_phone)

    # Activate user if not already active
    if not user.is_active:
        user.is_active = True
        user.save(update_fields=["is_active"])

    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)

    return {
        "verified": True,
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "is_new_user": is_new_user,
        "user": user,
    }
