import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.developer_accounts.models import (
    DeveloperAccount,
    DeveloperAuthToken,
    DeveloperUser,
    DeveloperUserStatus,
    Permission,
)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def developer_account(db):
    return DeveloperAccount.objects.create(company_name="Palm Hills")


@pytest.fixture
def primary_developer_user(developer_account):
    user = DeveloperUser.objects.create_user(
        email="owner@palmhills.com",
        password="securepassword123",
        first_name="Ahmed",
        last_name="Ali",
        account=developer_account,
        is_primary=True,
    )
    return user


@pytest.fixture
def developer_token(primary_developer_user):
    token, _ = DeveloperAuthToken.objects.get_or_create(user=primary_developer_user)
    return token


@pytest.mark.django_db
class TestDeveloperRegistrationAndLogin:
    def test_registration_creates_account_and_dedicated_token(self, api_client):
        payload = {
            "company_name": "Emaar Misr",
            "email": "dev@emaar.com",
            "password": "Password123!",
            "first_name": "Kareem",
            "last_name": "Hassan",
        }
        response = api_client.post("/api/v1/developer/register/", payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert "token" in response.data
        assert response.data["user"]["email"] == "dev@emaar.com"
        assert response.data["user"]["is_primary"] is True

        user = DeveloperUser.objects.get(email="dev@emaar.com")
        token = DeveloperAuthToken.objects.get(user=user)
        assert response.data["token"] == token.key

    def test_registration_rejects_duplicate_email(self, api_client, primary_developer_user):
        payload = {
            "company_name": "Another Company",
            "email": primary_developer_user.email,
            "password": "Password123!",
            "first_name": "Duplicate",
            "last_name": "User",
        }
        response = api_client.post("/api/v1/developer/register/", payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data.get("errors", response.data)

    def test_login_successful_with_dedicated_token(self, api_client, primary_developer_user):
        payload = {
            "email": primary_developer_user.email,
            "password": "securepassword123",
        }
        response = api_client.post("/api/v1/developer/login/", payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert "token" in response.data
        token = DeveloperAuthToken.objects.get(user=primary_developer_user)
        assert response.data["token"] == token.key

    def test_login_fails_with_invalid_credentials(self, api_client, primary_developer_user):
        payload = {
            "email": primary_developer_user.email,
            "password": "wrongpassword",
        }
        response = api_client.post("/api/v1/developer/login/", payload, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_fails_for_inactive_developer(self, api_client, primary_developer_user):
        primary_developer_user.status = DeveloperUserStatus.INACTIVE
        primary_developer_user.save()

        payload = {
            "email": primary_developer_user.email,
            "password": "securepassword123",
        }
        response = api_client.post("/api/v1/developer/login/", payload, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestDeveloperAuthenticationAndTeam:
    def test_authenticated_profile_view(self, api_client, developer_token, primary_developer_user):
        api_client.credentials(HTTP_AUTHORIZATION=f"Token {developer_token.key}")
        response = api_client.get("/api/v1/developer/account/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == primary_developer_user.email

    def test_unauthenticated_request_fails(self, api_client):
        response = api_client.get("/api/v1/developer/account/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_team_member_management(self, api_client, developer_token, developer_account):
        api_client.credentials(HTTP_AUTHORIZATION=f"Token {developer_token.key}")
        perm = Permission.objects.first()

        # Invite member
        invite_payload = {
            "email": "member@palmhills.com",
            "password": "memberpassword123",
            "first_name": "Sara",
            "last_name": "Tarek",
            "permission_ids": [perm.id] if perm else [],
        }
        response = api_client.post("/api/v1/developer/team/invite/", invite_payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        member_id = response.data["id"]

        # List team
        response = api_client.get("/api/v1/developer/team/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["meta"]["count"] == 2

        # Update member
        update_payload = {"first_name": "Sarah"}
        response = api_client.put(f"/api/v1/developer/team/{member_id}/", update_payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["first_name"] == "Sarah"

        # Deactivate member
        response = api_client.delete(f"/api/v1/developer/team/{member_id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        member = DeveloperUser.objects.get(id=member_id)
        assert member.status == DeveloperUserStatus.INACTIVE
