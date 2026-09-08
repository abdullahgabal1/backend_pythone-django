"""
Search — Services & View Tests
===============================
Comprehensive test suite for the search filter engine and ranking.
"""
from decimal import Decimal
import pytest
from django.urls import reverse
from rest_framework import status

from apps.properties.models import Agent, Amenity, Property, PropertyImage, PropertyType, CompletionStatus, Furnishing, PaymentMethod
from apps.search.services import search_properties


@pytest.mark.django_db
class TestSearchService:
    @pytest.fixture(autouse=True)
    def setup_properties(self):
        self.agent = Agent.objects.create(name="أحمد سمير", phone="01234567890", image="https://example.com/a.jpg")

        self.pool = Amenity.objects.create(name="حمام سباحة")
        self.gym = Amenity.objects.create(name="جيم")
        self.security = Amenity.objects.create(name="أمن")

        # 1. Studio in New Cairo
        self.studio = Property.objects.create(
            title="ستوديو مميز بالتجمع",
            description="ستوديو راقي بتشطيب ممتاز في التجمع الخامس",
            location="التجمع الخامس, القاهرة",
            price=Decimal("1500000.00"),
            area_sqm=55,
            beds=0,
            baths=1,
            property_type=PropertyType.APARTMENT,
            completion_status=CompletionStatus.OFF_PLAN,
            furnishing=Furnishing.UNFURNISHED,
            payment_method=PaymentMethod.INSTALLMENT,
            is_featured=False,
            parking=0,
            agent=self.agent,
        )
        self.studio.amenities.add(self.security)

        # 2. Apartment in Maadi
        self.apt = Property.objects.create(
            title="شقة واسعة بالمعادي",
            description="شقة 3 غرف في دجلة المعادي",
            location="دجلة, المعادي",
            price=Decimal("3500000.00"),
            area_sqm=175,
            beds=3,
            baths=2,
            property_type=PropertyType.APARTMENT,
            completion_status=CompletionStatus.READY,
            furnishing=Furnishing.FURNISHED,
            payment_method=PaymentMethod.CASH,
            is_featured=True,
            parking=1,
            agent=self.agent,
        )
        self.apt.amenities.add(self.pool, self.gym, self.security)
        PropertyImage.objects.create(property=self.apt, image="https://example.com/apt.jpg", is_cover=True)

        # 3. Large Villa in Zayed (7+ beds, 7+ baths)
        self.villa = Property.objects.create(
            title="قصر وفيلا فاخرة بالشيخ زايد",
            description="قصر 8 غرف نوم و8 حمامات مع حديقة شاسعة ومسبح",
            location="الشيخ زايد, الجيزة",
            price=Decimal("25000000.00"),
            area_sqm=800,
            beds=8,
            baths=7,
            property_type=PropertyType.VILLA,
            completion_status=CompletionStatus.READY,
            furnishing=Furnishing.SEMI_FURNISHED,
            payment_method=PaymentMethod.MORTGAGE,
            is_featured=True,
            parking=4,
            agent=self.agent,
        )
        self.villa.amenities.add(self.pool, self.gym, self.security)
        PropertyImage.objects.create(property=self.villa, image="https://example.com/villa.jpg", is_cover=True)

        # 4. Chalet in North Coast
        self.chalet = Property.objects.create(
            title="شاليه على البحر بالساحل الشمالي",
            description="شاليه بإطلالة مباشرة على اللاجون",
            location="الساحل الشمالي, سيدي عبد الرحمن",
            price=Decimal("5000000.00"),
            area_sqm=120,
            beds=2,
            baths=2,
            property_type=PropertyType.CHALET,
            completion_status=CompletionStatus.READY,
            furnishing=Furnishing.FURNISHED,
            payment_method=PaymentMethod.INSTALLMENT,
            is_featured=False,
            parking=1,
        )
        self.chalet.amenities.add(self.pool)

    def test_empty_filters_matches_everything(self):
        qs = search_properties({})
        assert qs.count() == 4

    def test_filter_location_icontains(self):
        qs = search_properties({"location": "معادي"})
        assert qs.count() == 1
        assert qs.first().id == self.apt.id

    def test_filter_property_types_plural_aliases(self):
        # "شقق" should match APARTMENT (both studio and apt)
        qs = search_properties({"propertyTypes": "شقق"})
        assert qs.count() == 2
        assert set(qs.values_list("id", flat=True)) == {self.studio.id, self.apt.id}

        # "فلل,شاليهات" should match villa and chalet
        qs2 = search_properties({"propertyTypes": "فلل,شاليهات"})
        assert qs2.count() == 2
        assert set(qs2.values_list("id", flat=True)) == {self.villa.id, self.chalet.id}

    def test_filter_bedrooms_studio_and_gte7(self):
        # "ستوديو"
        qs_studio = search_properties({"bedrooms": "ستوديو"})
        assert qs_studio.count() == 1
        assert qs_studio.first().id == self.studio.id

        # "7+"
        qs_large = search_properties({"bedrooms": "7+"})
        assert qs_large.count() == 1
        assert qs_large.first().id == self.villa.id

        # Exact and studio combo
        qs_combo = search_properties({"bedrooms": "3,ستوديو"})
        assert qs_combo.count() == 2
        assert set(qs_combo.values_list("id", flat=True)) == {self.studio.id, self.apt.id}

    def test_filter_bathrooms_exact_and_gte7(self):
        qs_baths = search_properties({"bathrooms": "7+"})
        assert qs_baths.count() == 1
        assert qs_baths.first().id == self.villa.id

        qs_2baths = search_properties({"bathrooms": "2"})
        assert qs_2baths.count() == 2
        assert set(qs_2baths.values_list("id", flat=True)) == {self.apt.id, self.chalet.id}

    def test_filter_price_range(self):
        qs = search_properties({"minPrice": "2000000", "maxPrice": "6000000"})
        assert qs.count() == 2
        assert set(qs.values_list("id", flat=True)) == {self.apt.id, self.chalet.id}

    def test_filter_area_range(self):
        qs = search_properties({"minArea": "100", "maxArea": "200"})
        assert qs.count() == 2
        assert set(qs.values_list("id", flat=True)) == {self.apt.id, self.chalet.id}

    def test_filter_completion_status(self):
        qs_ready = search_properties({"completionStatus": "ready"})
        assert qs_ready.count() == 3

        qs_offplan = search_properties({"completionStatus": "تحت الإنشاء"})
        assert qs_offplan.count() == 1
        assert qs_offplan.first().id == self.studio.id

    def test_filter_furnishing(self):
        qs = search_properties({"furnishing": "furnished"})
        assert qs.count() == 2
        assert set(qs.values_list("id", flat=True)) == {self.apt.id, self.chalet.id}

    def test_filter_amenities_and_logic(self):
        # Both pool AND gym are present only on apt and villa
        qs = search_properties({"amenities": "حمام سباحة,جيم"})
        assert qs.count() == 2
        assert set(qs.values_list("id", flat=True)) == {self.apt.id, self.villa.id}

        # Pool only matches chalet, apt, and villa
        qs_pool = search_properties({"amenities": "حمام سباحة"})
        assert qs_pool.count() == 3

    def test_filter_payment_method_param_name(self):
        # The parameter from frontend is 'payment', NOT 'paymentMethod'
        qs_cash = search_properties({"payment": "cash"})
        assert qs_cash.count() == 1
        assert qs_cash.first().id == self.apt.id

        qs_installment = search_properties({"payment": "تقسيط"})
        assert qs_installment.count() == 2
        assert set(qs_installment.values_list("id", flat=True)) == {self.studio.id, self.chalet.id}

    def test_combination_multiple_filters(self):
        filters = {
            "propertyTypes": "شقق",
            "bedrooms": "3",
            "payment": "cash",
            "completionStatus": "ready",
            "amenities": "حمام سباحة,أمن",
        }
        qs = search_properties(filters)
        assert qs.count() == 1
        assert qs.first().id == self.apt.id

    def test_sort_by_relevance_deterministic(self):
        qs = search_properties({}, ordering="relevance")
        ids = list(qs.values_list("id", flat=True))
        assert len(ids) == 4
        # Running it a second time should give identical deterministic ordering
        qs2 = search_properties({}, ordering="relevance")
        ids2 = list(qs2.values_list("id", flat=True))
        assert ids == ids2

    def test_search_view_endpoint(self, api_client):
        url = reverse("property-search")
        response = api_client.get(
            url,
            {
                "location": "معادي",
                "propertyTypes": "شقق",
                "sortBy": "price-asc",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == self.apt.id
