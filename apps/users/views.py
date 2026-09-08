"""
Users — Views
===============
Account endpoints for the authenticated user.
"""
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers import UserProfileSerializer, UserUpdateSerializer
from apps.users.services import update_user_profile


class MeView(APIView):
    """
    GET  /api/v1/account/me/ — retrieve current user profile
    PATCH /api/v1/account/me/ — update current user profile (name, birthday)
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        serializer = UserUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = update_user_profile(request.user, **serializer.validated_data)
        return Response(
            UserProfileSerializer(user).data,
            status=status.HTTP_200_OK,
        )
