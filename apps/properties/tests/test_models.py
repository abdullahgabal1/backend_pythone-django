"""
Properties — Model Tests
=========================
Unit tests for Property, Agent, Amenity, and PropertyImage models.
"""
from decimal import Decimal
import pytest
from apps.properties.models import (
    Agent,
    Amenity,
    CompletionStatus,
    Furnishing,
    PaymentMethod,
    Property,
    PropertyImage,
    PropertyType,
)


@pytest.mark.django_db
class TestPropertyModels:
    def test_create_agent(self):
        agent = Agent.objects.create(
            name="سارة أحمد",
            phone="01099887766",
            image="https://example.com/agent.jpg",
        )
        assert agent.name == "سارة أحمد"
        assert str(agent) == "سارة أحمد"

    def test_create_amenity(self):
        amenity = Amenity.objects.create(name="حمام سباحة")
        assert amenity.name == "حمام سباحة"
        assert str(amenity) == "حمام سباحة"

    def test_create_property_all_fields(self):
        agent = Agent.objects.create(
            name="كريم حسن",
            phone="01122334455",
            image="https://example.com/agent2.jpg",
        )
        pool = Amenity.objects.create(name="مسبح")
        gym = Amenity.objects.create(name="جيم")

        prop = Property.objects.create(
            title="شقة فاخرة للبيع في التجمع الخامس",
            description="شقة مميزة بتشطيب الترا سوبر لوكس وإطلالة رائعة.",
            location="التجمع الخامس, القاهرة الجديدة",
            price=Decimal("4500000.00"),
            price_suffix="",
            area_sqm=180,
            beds=3,
            baths=2,
            property_type=PropertyType.APARTMENT,
            completion_status=CompletionStatus.READY,
            furnishing=Furnishing.SEMI_FURNISHED,
            payment_method=PaymentMethod.INSTALLMENT,
            parking=1,
            agent=agent,
            is_featured=True,
            view_count=0,
        )
        prop.amenities.add(pool, gym)

        assert prop.pk is not None
        assert prop.property_type == "apartment"
        assert prop.completion_status == "ready"
        assert prop.furnishing == "semi_furnished"
        assert prop.payment_method == "installment"
        assert prop.amenities.count() == 2
        assert pool in prop.amenities.all()
        assert gym in prop.amenities.all()
        assert str(prop) == f"{prop.title} - {prop.location}"

    def test_property_studio_zero_beds(self):
        prop = Property.objects.create(
            title="ستوديو للبيع بالشيخ زايد",
            description="ستوديو استثماري مميز.",
            location="الشيخ زايد",
            price=Decimal("1800000.00"),
            area_sqm=65,
            beds=0,  # 0 means studio
            baths=1,
            property_type=PropertyType.APARTMENT,
            completion_status=CompletionStatus.OFF_PLAN,
            furnishing=Furnishing.UNFURNISHED,
            payment_method=PaymentMethod.CASH,
        )
        assert prop.beds == 0

    def test_property_images(self):
        prop = Property.objects.create(
            title="فيلا مستقلة",
            description="فيلا واسعة مع حديقة خاصة.",
            location="الشروق",
            price=Decimal("12000000.00"),
            area_sqm=400,
            beds=5,
            baths=4,
            property_type=PropertyType.VILLA,
            completion_status=CompletionStatus.READY,
            furnishing=Furnishing.FURNISHED,
            payment_method=PaymentMethod.MORTGAGE,
        )
        img1 = PropertyImage.objects.create(
            property=prop,
            image="https://example.com/cover.jpg",
            order=0,
            is_cover=True,
        )
        img2 = PropertyImage.objects.create(
            property=prop,
            image="https://example.com/interior.jpg",
            order=1,
            is_cover=False,
        )
        assert prop.images.count() == 2
        assert "Image 0 for فيلا مستقلة" in str(img1)
