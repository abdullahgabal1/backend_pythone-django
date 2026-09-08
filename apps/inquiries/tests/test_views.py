"""
Inquiries — View & Service Tests
=================================
Tests for inquiry creation, anti-spam duplicate prevention, notifications, and user history.
"""
from datetime import date
from decimal import Decimal
import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status

from apps.inquiries.models import Inquiry, InquiryType, ContactMethod
from apps.properties.models import Agent, Property, PropertyType, CompletionStatus, Furnishing, PaymentMethod

User = get_user_model()


@pytest.mark.django_db
class TestInquiryViews:
    @pytest.fixture(autouse=True)
    def setup_data(self):
        cache.clear()
        self.user = User.objects.create_user(
            phone="01012345678",
            password="SecurePassword123!",
            name="علي مصطفى",
            birthday=date(1992, 4, 10),
            is_active=True,
        )
        self.agent = Agent.objects.create(
            name="خالد منصور",
            phone="01155443322",
            image="https://example.com/agent.jpg",
        )
        self.prop = Property.objects.create(
            title="شقة مميزة بالتجمع الخامس",
            description="شقة للبيع",
            location="التجمع الخامس, القاهرة",
            price=Decimal("4200000.00"),
            area_sqm=160,
            beds=3,
            baths=2,
            property_type=PropertyType.APARTMENT,
            completion_status=CompletionStatus.READY,
            furnishing=Furnishing.SEMI_FURNISHED,
            payment_method=PaymentMethod.INSTALLMENT,
            agent=self.agent,
        )

    def test_create_inquiry_guest_success(self, api_client):
        url = reverse("inquiry-create")
        payload = {
            "property_id": self.prop.id,
            "name": "يوسف محمود",
            "phone": "01099887766",
            "message": "أرغب في الاستفسار عن تفاصيل التقسيط.",
            "inquiry_type": "viewing",
            "preferred_contact_method": "whatsapp",
        }
        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "يوسف محمود"
        assert data["data"]["phone"] == "01099887766"
        assert data["data"]["agent_notified"] is True

        inquiry = Inquiry.objects.get(pk=data["data"]["id"])
        assert inquiry.property == self.prop
        assert inquiry.user is None

    def test_create_inquiry_authenticated_user(self, api_client):
        api_client.force_authenticate(user=self.user)
        url = reverse("inquiry-create")
        payload = {
            "property_id": self.prop.id,
            "name": self.user.name,
            "phone": self.user.phone,
            "message": "طلب معاينة في عطلة نهاية الأسبوع.",
            "inquiry_type": "viewing",
        }
        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        inquiry = Inquiry.objects.get(pk=data["data"]["id"])
        assert inquiry.user == self.user

    def test_duplicate_inquiry_anti_spam_cooldown(self, api_client):
        url = reverse("inquiry-create")
        payload = {
            "property_id": self.prop.id,
            "name": "محمود عادل",
            "phone": "01233445566",
            "message": "طلب أول",
        }
        # First submission succeeds
        res1 = api_client.post(url, payload, format="json")
        assert res1.status_code == status.HTTP_201_CREATED

        # Rapid second submission is blocked by cooldown
        res2 = api_client.post(url, payload, format="json")
        assert res2.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_phone_rejection(self, api_client):
        url = reverse("inquiry-create")
        payload = {
            "property_id": self.prop.id,
            "name": "أحمد",
            "phone": "12345",  # Invalid
        }
        response = api_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_my_inquiries_list_authenticated_only(self, api_client):
        url = reverse("inquiry-my-list")
        res_unauth = api_client.get(url)
        assert res_unauth.status_code == status.HTTP_401_UNAUTHORIZED

        Inquiry.objects.create(
            property=self.prop,
            user=self.user,
            name=self.user.name,
            phone=self.user.phone,
            message="رسالتي",
        )
        api_client.force_authenticate(user=self.user)
        res_auth = api_client.get(url)
        assert res_auth.status_code == status.HTTP_200_OK
        data = res_auth.json()
        assert data["success"] is True
        assert len(data["data"]) == 1
