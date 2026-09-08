"""
Authentication — URL Routes
==============================
Three endpoints for the Akedly OTP authentication flow.

Mounted at /api/v1/auth/ via the root URL config.
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.authentication.views import ChallengeView, SendOtpView, VerifyOtpView, LogoutView

urlpatterns = [
    path("challenge/", ChallengeView.as_view(), name="auth-challenge"),
    path("send-otp/", SendOtpView.as_view(), name="auth-send-otp"),
    path("verify-otp/", VerifyOtpView.as_view(), name="auth-verify-otp"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
]

