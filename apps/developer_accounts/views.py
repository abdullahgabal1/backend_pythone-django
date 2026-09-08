"""
Developer Accounts — Views
============================
API views for developer login, account management, and team CRUD.
"""
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.pagination import StandardPagination
from apps.developer_accounts.authentication import DeveloperTokenAuthentication
from apps.developer_accounts.models import DeveloperAccount, DeveloperUser
from apps.developer_accounts.permissions import HasDeveloperPermission, IsDeveloperAuthenticated
from apps.developer_accounts.selectors import get_team_members
from apps.developer_accounts.serializers import (
    AccountUpdateSerializer,
    DeveloperUserSerializer,
    LoginSerializer,
    TeamMemberCreateSerializer,
    TeamMemberSerializer,
    TeamMemberUpdateSerializer,
)
from apps.developer_accounts.services import (
    authenticate_developer,
    deactivate_team_member,
    delete_developer_account,
    invite_team_member,
    update_developer_account,
    update_team_member,
)


class LoginView(APIView):
    """
    Developer login — returns token + user data.
    POST /api/v1/developer/login/
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user, token_key = authenticate_developer(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )

        return Response(
            {
                "token": token_key,
                "user": DeveloperUserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


class RegisterView(APIView):
    """
    Developer registration — creates account + primary user.
    POST /api/v1/developer/register/
    """

    permission_classes = [AllowAny]

    def post(self, request):
        from rest_framework import serializers as s

        class RegisterSerializer(s.Serializer):
            company_name = s.CharField(max_length=255)
            email = s.EmailField()
            password = s.CharField(write_only=True, min_length=8)
            first_name = s.CharField(max_length=100)
            last_name = s.CharField(max_length=100)

        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        from rest_framework.exceptions import ValidationError

        if DeveloperUser.objects.filter(email=data["email"]).exists():
            raise ValidationError({"email": "هذا البريد الإلكتروني مستخدم بالفعل."})

        from django.db import transaction
        from rest_framework.authtoken.models import Token

        with transaction.atomic():
            account = DeveloperAccount.objects.create(
                company_name=data["company_name"],
            )
            user = DeveloperUser.objects.create_user(
                email=data["email"],
                password=data["password"],
                first_name=data["first_name"],
                last_name=data["last_name"],
                account=account,
                is_primary=True,
            )
            token, _ = Token.objects.get_or_create(user_id=user.pk)

        return Response(
            {
                "token": token.key,
                "user": DeveloperUserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class AccountView(APIView):
    """
    Manage the authenticated developer's own profile.
    PUT /api/v1/developer/account/ — update profile
    DELETE /api/v1/developer/account/ — delete entire account
    """

    authentication_classes = [DeveloperTokenAuthentication]
    permission_classes = [IsDeveloperAuthenticated]

    def get(self, request):
        return Response(DeveloperUserSerializer(request.user).data)

    def put(self, request):
        serializer = AccountUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = update_developer_account(request.user, serializer.validated_data)
        return Response(DeveloperUserSerializer(user).data)

    def delete(self, request):
        delete_developer_account(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TeamListView(APIView):
    """
    List all team members in the developer's account.
    GET /api/v1/developer/team/
    """

    authentication_classes = [DeveloperTokenAuthentication]
    permission_classes = [IsDeveloperAuthenticated]

    def get(self, request):
        members = get_team_members(request.user.account)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(members, request)
        serializer = TeamMemberSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class TeamCreateView(APIView):
    """
    Invite a new team member.
    POST /api/v1/developer/team/
    """

    authentication_classes = [DeveloperTokenAuthentication]
    permission_classes = [IsDeveloperAuthenticated, HasDeveloperPermission]
    required_permission = "manage_team"

    def post(self, request):
        serializer = TeamMemberCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        member = invite_team_member(request.user.account, serializer.validated_data)
        return Response(
            TeamMemberSerializer(member).data,
            status=status.HTTP_201_CREATED,
        )


class TeamDetailView(APIView):
    """
    Update or deactivate a team member.
    PUT /api/v1/developer/team/<id>/
    DELETE /api/v1/developer/team/<id>/ — soft-deactivate
    """

    authentication_classes = [DeveloperTokenAuthentication]
    permission_classes = [IsDeveloperAuthenticated, HasDeveloperPermission]
    required_permission = "manage_team"

    def _get_member(self, pk, account):
        try:
            return DeveloperUser.objects.get(pk=pk, account=account)
        except DeveloperUser.DoesNotExist:
            raise NotFound("عضو الفريق غير موجود.")

    def put(self, request, pk):
        member = self._get_member(pk, request.user.account)
        serializer = TeamMemberUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        member = update_team_member(member, serializer.validated_data)
        return Response(TeamMemberSerializer(member).data)

    def delete(self, request, pk):
        member = self._get_member(pk, request.user.account)
        deactivate_team_member(member)
        return Response(status=status.HTTP_204_NO_CONTENT)
