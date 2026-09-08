"""
Properties — View Tests
========================
Tests for PropertyListView and PropertyDetailView.
"""
from decimal import Decimal
import pytest
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status

from apps.properties.models import Agent, Amenity, Property, PropertyImage, PropertyType, CompletionStatus, Furnishing, PaymentMethod


@pytest.mark.django_db
class TestPropertyViews:
    @pytest.fixture(autouse=True)
    def setup_data(self):
        cache.clear()
        self.agent = Agent.objects.create(
            name="عمر خالد",
            phone="01011223344",
            image="https://example.com/agent.jpg",
        )
        self.amenity = Amenity.objects.create(name="أمن 24/7")

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
            is_featured=True,
            agent=self.agent,
        )
        self.prop1.amenities.add(self.amenity)
        self.img1 = PropertyImage.objects.create(
            property=self.prop1,
            image="https://example.com/prop1.jpg",
            is_cover=True,
        )

        self.prop2 = Property.objects.create(
            title="تاون هاوس في 6 أكتوبر",
            description="تاون هاوس في كمبوند راقي.",
            location="6 أكتوبر, الجيزة",
            price=Decimal("6000000.00"),
            area_sqm=250,
            beds=4,
            baths=3,
            property_type=PropertyType.TOWNHOUSE,
            completion_status=CompletionStatus.OFF_PLAN,
            furnishing=Furnishing.UNFURNISHED,
            payment_method=PaymentMethod.INSTALLMENT,
            is_featured=False,
        )

    def test_property_list_pagination(self, api_client):
        url = reverse("property-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 2
        assert data["meta"]["count"] == 2
        # Check cover image is serialized
        prop_data = next(p for p in data["data"] if p["id"] == self.prop1.id)
        assert prop_data["cover_image"] == "https://example.com/prop1.jpg"

    def test_property_list_filter_is_featured(self, api_client):
        url = reverse("property-list")
        response = api_client.get(f"{url}?is_featured=true")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == self.prop1.id

    def test_property_detail_success(self, api_client):
        url = reverse("property-detail", kwargs={"pk": self.prop1.pk})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == self.prop1.id
        assert data["data"]["agent"]["name"] == "عمر خالد"
        assert "أمن 24/7" in data["data"]["amenities"]
        assert len(data["data"]["images"]) == 1

    def test_property_detail_view_count_deduplication(self, api_client):
        url = reverse("property-detail", kwargs={"pk": self.prop1.pk})

        assert self.prop1.view_count == 0

        # First request increments view count
        res1 = api_client.get(url, REMOTE_ADDR="192.168.1.100")
        assert res1.status_code == status.HTTP_200_OK
        self.prop1.refresh_from_db()
        assert self.prop1.view_count == 1

        # Rapid repeat request from same client does NOT increment
        res2 = api_client.get(url, REMOTE_ADDR="192.168.1.100")
        assert res2.status_code == status.HTTP_200_OK
        self.prop1.refresh_from_db()
        assert self.prop1.view_count == 1

        # Request from different IP DOES increment
        res3 = api_client.get(url, REMOTE_ADDR="192.168.1.101")
        assert res3.status_code == status.HTTP_200_OK
        self.prop1.refresh_from_db()
        assert self.prop1.view_count == 2

    def test_property_detail_not_found(self, api_client):
        url = reverse("property-detail", kwargs={"pk": 999999})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["success"] is False
