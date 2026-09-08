"""
Developer Accounts — Authentication Backend
=============================================
Custom authentication backend to resolve Token → DeveloperUser.
"""
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed

from apps.developer_accounts.models import DeveloperUser


class DeveloperTokenAuthentication(TokenAuthentication):
    """
    Token authentication that resolves to DeveloperUser instead of the default User.
    The frontend sends `Authorization: Token <token>`.
    """

    def authenticate_credentials(self, key):
        try:
            token = Token.objects.get(key=key)
        except Token.DoesNotExist:
            raise AuthenticationFailed("رمز المصادقة غير صالح.")

        # The token's user_id points to a DeveloperUser
        try:
            user = DeveloperUser.objects.get(pk=token.user_id)
        except DeveloperUser.DoesNotExist:
            raise AuthenticationFailed("المستخدم غير موجود.")

        if not user.is_active:
            raise AuthenticationFailed("هذا الحساب غير نشط.")

        return (user, token)
