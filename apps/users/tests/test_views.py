from datetime import date
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status

User = get_user_model()


@pytest.mark.django_db
class TestAccountViews:
    """Test suite for the account (profile) endpoints."""

    @pytest.fixture(autouse=True)
    def setup_data(self):
        self.user = User.objects.create_user(
            phone="01012345678",
            password="SecurePassword123!",
            name="أحمد علي",
            birthday=date(1995, 5, 15),
            is_active=True,
        )
        self.url = reverse("account-me")

    def test_get_profile_unauthenticated(self, api_client):
        """Test that unauthenticated requests are blocked."""
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_profile_authenticated(self, api_client):
        """Test retrieving the profile of the logged-in user."""
        api_client.force_authenticate(user=self.user)
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        # Check standard envelope format
        data = response.json()
        assert data["success"] is True
        assert data["data"]["phone"] == "01012345678"
        assert data["data"]["name"] == "أحمد علي"
        assert data["data"]["birthday"] == "1995-05-15"
        assert data["data"]["role"] == "buyer"

    def test_update_profile_success(self, api_client):
        """Test modifying profile properties (name and birthday)."""
        api_client.force_authenticate(user=self.user)
        update_data = {"name": "أحمد رأفت", "birthday": "1990-05-14"}
        response = api_client.patch(self.url, data=update_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "أحمد رأفت"
        assert data["data"]["birthday"] == "1990-05-14"

        # Verify change is stored
        self.user.refresh_from_db()
        assert self.user.name == "أحمد رأفت"
        assert self.user.birthday == date(1990, 5, 14)

    def test_update_profile_phone_fails(self, api_client):
        """Test that the user cannot modify their phone number."""
        api_client.force_authenticate(user=self.user)
        # Pass a valid updatable field ('name') along with the immutable 'phone'
        update_data = {"name": "أحمد الجديد", "phone": "01198765432"}
        response = api_client.patch(self.url, data=update_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "أحمد الجديد"
        assert data["data"]["phone"] == "01012345678"  # phone remains unchanged

        self.user.refresh_from_db()
        assert self.user.name == "أحمد الجديد"
        assert self.user.phone == "01012345678"  # unchanged
