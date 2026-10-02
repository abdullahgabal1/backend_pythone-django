"""
Developer Accounts — Authentication Backend
=============================================
Custom authentication backend to resolve Token → DeveloperUser.
"""
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed

from apps.developer_accounts.models import DeveloperAuthToken, DeveloperUser


class DeveloperTokenAuthentication(TokenAuthentication):
    """
    Token authentication that resolves to DeveloperUser instead of the default User.
    The frontend sends `Authorization: Token <token>`.
    """

    model = DeveloperAuthToken

    def authenticate_credentials(self, key):
        try:
            token = DeveloperAuthToken.objects.select_related("user").get(key=key)
        except DeveloperAuthToken.DoesNotExist:
            raise AuthenticationFailed("رمز المصادقة غير صالح.")

        user = token.user
        if not user.is_active:
            raise AuthenticationFailed("هذا الحساب غير نشط.")

        return (user, token)
