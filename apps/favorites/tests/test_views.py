"""
Favorites — View Tests
=======================
Tests for FavoriteListView and FavoriteToggleView.
"""
from datetime import date
from decimal import Decimal
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from apps.favorites.models import Favorite
from apps.properties.models import Property, PropertyType, CompletionStatus, Furnishing, PaymentMethod

User = get_user_model()


@pytest.mark.django_db
class TestFavoriteViews:
    @pytest.fixture(autouse=True)
    def setup_data(self):
        self.user1 = User.objects.create_user(
            phone="01011112222",
            password="StrongPassword123!",
            name="مستخدم أول",
            birthday=date(1995, 1, 1),
            is_active=True,
        )
        self.user2 = User.objects.create_user(
            phone="01033334444",
            password="StrongPassword123!",
            name="مستخدم ثان",
            birthday=date(1996, 2, 2),
            is_active=True,
        )
        self.prop1 = Property.objects.create(
            title="شقة في المعادي",
            description="شقة بإطلالة نيلية هادئة.",
            location="المعادي, القاهرة",
            price=Decimal("3000000.00"),
            area_sqm=150,
            beds=3,
            baths=2,
            property_type=PropertyType.APARTMENT,
            completion_status=CompletionStatus.READY,
            furnishing=Furnishing.FURNISHED,
            payment_method=PaymentMethod.CASH,
        )
        self.prop2 = Property.objects.create(
            title="فيلا في التجمع",
            description="فيلا راقية.",
            location="التجمع الخامس",
            price=Decimal("15000000.00"),
            area_sqm=450,
            beds=5,
            baths=4,
            property_type=PropertyType.VILLA,
            completion_status=CompletionStatus.READY,
            furnishing=Furnishing.SEMI_FURNISHED,
            payment_method=PaymentMethod.INSTALLMENT,
        )

    def test_unauthenticated_toggle_returns_401(self, api_client):
        url = reverse("favorite-toggle", kwargs={"pk": self.prop1.pk})
        response = api_client.post(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_unauthenticated_list_returns_401(self, api_client):
        url = reverse("favorite-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_toggle_favorite_add_and_remove(self, api_client):
        api_client.force_authenticate(user=self.user1)
        url = reverse("favorite-toggle", kwargs={"pk": self.prop1.pk})

        # First toggle: adds to favorites
        res1 = api_client.post(url)
        assert res1.status_code == status.HTTP_200_OK
        data1 = res1.json()
        assert data1["success"] is True
        assert data1["data"]["action"] == "added"
        assert data1["data"]["is_favorited"] is True
        assert Favorite.objects.filter(user=self.user1, property=self.prop1).exists()

        # Second toggle: removes from favorites (idempotent toggle)
        res2 = api_client.post(url)
        assert res2.status_code == status.HTTP_200_OK
        data2 = res2.json()
        assert data2["success"] is True
        assert data2["data"]["action"] == "removed"
        assert data2["data"]["is_favorited"] is False
        assert not Favorite.objects.filter(user=self.user1, property=self.prop1).exists()

    def test_favorite_list_isolation_per_user(self, api_client):
        # user1 favorites prop1
        Favorite.objects.create(user=self.user1, property=self.prop1)
        # user2 favorites prop2
        Favorite.objects.create(user=self.user2, property=self.prop2)

        # user1 list
        api_client.force_authenticate(user=self.user1)
        url = reverse("favorite-list")
        res1 = api_client.get(url)
        assert res1.status_code == status.HTTP_200_OK
        data1 = res1.json()
        assert len(data1["data"]) == 1
        assert data1["data"][0]["property"]["id"] == self.prop1.id

        # user2 list
        api_client.force_authenticate(user=self.user2)
        res2 = api_client.get(url)
        assert res2.status_code == status.HTTP_200_OK
        data2 = res2.json()
        assert len(data2["data"]) == 1
        assert data2["data"][0]["property"]["id"] == self.prop2.id
