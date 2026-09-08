"""
Authentication — Views
========================
API views for the 3-step Akedly OTP authentication flow.

All endpoints are AllowAny — authentication happens through OTP verification.
"""
import logging

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from apps.authentication.serializers import (
    AuthTokenSerializer,
    SendOtpSerializer,
    VerifyOtpSerializer,
)
from apps.authentication.services import (
    get_akedly_challenge,
    send_akedly_otp,
    verify_akedly_otp_and_authenticate,
)
from apps.common.akedly import AkedlyApiError

logger = logging.getLogger(__name__)


class OtpRateThrottle(AnonRateThrottle):
    """
    Throttle class to limit OTP requests.
    Matches the Node.js Express rate limiter via the 'otp' scope in settings.
    """
    scope = "otp"



def _handle_akedly_error(err: AkedlyApiError) -> Response:
    """
    Map an AkedlyApiError to the standard API error envelope.
    Mirrors the sendErrorResponse() from the Node.js routes.
    """
    return Response(
        {
            "success": False,
            "data": None,
            "message": str(err),
            "errors": [err.to_error_dict()],
            "meta": {},
        },
        status=err.status or 502,
    )


class ChallengeView(APIView):
    """
    GET /api/v1/auth/challenge/

    Step 1 — Returns a Proof-of-Work challenge + Turnstile site key
    for the frontend to solve via @akedly/shield.
    """

    permission_classes = [AllowAny]
    throttle_classes = [OtpRateThrottle]

    def get(self, request):
        try:
            data = get_akedly_challenge()
            return Response(data, status=status.HTTP_200_OK)
        except AkedlyApiError as err:
            return _handle_akedly_error(err)


class SendOtpView(APIView):
    """
    POST /api/v1/auth/send-otp/

    Step 2 — Send the OTP once the client has solved the challenge.
    Server-side validation happens here — never trust the frontend's
    own phone-format checks.
    """

    permission_classes = [AllowAny]
    throttle_classes = [OtpRateThrottle]

    def post(self, request):
        serializer = SendOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            data = send_akedly_otp(
                phone_number=serializer.validated_data["phone_number"],
                pow_solution=serializer.validated_data["pow_solution"],
                turnstile_token=serializer.validated_data.get("turnstile_token"),
                digits=serializer.validated_data.get("digits"),
                end_user_ip=self._get_client_ip(request),
            )
            return Response(data, status=status.HTTP_200_OK)
        except AkedlyApiError as err:
            return _handle_akedly_error(err)

    @staticmethod
    def _get_client_ip(request) -> str | None:
        """
        Extract the real client IP from the request.
        Checks X-Forwarded-For first (for reverse proxies), then REMOTE_ADDR.
        """
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")


class VerifyOtpView(APIView):
    """
    POST /api/v1/auth/verify-otp/

    Step 3 — Verify the code the user typed in.
    On success: creates/activates the user and returns JWT tokens.
    """

    permission_classes = [AllowAny]
    throttle_classes = [OtpRateThrottle]

    def post(self, request):
        serializer = VerifyOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = verify_akedly_otp_and_authenticate(
                transaction_req_id=serializer.validated_data["transaction_req_id"],
                otp=serializer.validated_data["otp"],
                phone_number=serializer.validated_data["phone_number"],
            )
        except AkedlyApiError as err:
            return _handle_akedly_error(err)

        if not result.get("verified"):
            return Response(
                {
                    "success": False,
                    "data": None,
                    "message": "OTP verification failed.",
                    "errors": [{"code": "INVALID_OTP"}],
                    "meta": {},
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Serialize the response with JWT tokens + user data
        response_data = AuthTokenSerializer({
            "access": result["access"],
            "refresh": result["refresh"],
            "is_new_user": result["is_new_user"],
            "user": result["user"],
        }).data

        return Response(response_data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    POST /api/v1/auth/logout/

    Allows the user to log out by blacklisting their refresh token.
    Requires authentication.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {
                    "success": False,
                    "data": None,
                    "message": "يجب تقديم رمز التحديث (refresh token) لتسجيل الخروج.",
                    "errors": {"refresh": ["This field is required."]},
                    "meta": {},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {"message": "تم تسجيل الخروج بنجاح."},
                status=status.HTTP_200_OK,
            )
        except TokenError as e:
            return Response(
                {
                    "success": False,
                    "data": None,
                    "message": "رمز التحديث غير صالح أو منتهي الصلاحية.",
                    "errors": {"refresh": [str(e)]},
                    "meta": {},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

