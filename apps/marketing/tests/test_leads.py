import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.developer_accounts.models import (
    DeveloperAccount,
    DeveloperAuthToken,
    DeveloperUser,
    Permission,
)
from apps.inquiries.models import Inquiry, InquiryStatus
from apps.locations.models import Location
from apps.marketing.models import MarketingLead
from apps.projects.models import Project
from apps.properties.models import Property


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def developer_account(db):
    return DeveloperAccount.objects.create(company_name="SODIC Developments")


@pytest.fixture
def location(db):
    return Location.objects.create(name="New Cairo")


@pytest.fixture
def project(developer_account, location):
    return Project.objects.create(
        account=developer_account,
        name="Villette",
        project_type="residential",
        location=location,
        price_per_meter=45000,
    )


@pytest.fixture
def property_listing(project):
    return Property.objects.create(
        title="Modern Villa in Villette",
        description="Luxurious villa with private pool",
        location="New Cairo",
        price=15000000,
        area_sqm=350,
        beds=4,
        baths=5,
        property_type="villa",
        completion_status="ready",
        furnishing="unfurnished",
        payment_method="cash",
        project=project,
    )


@pytest.fixture
def primary_developer_user(developer_account):
    user = DeveloperUser.objects.create_user(
        email="sodic.owner@sodic.com",
        password="securepass123",
        first_name="Hany",
        last_name="Saad",
        account=developer_account,
        is_primary=True,
    )
    return user


@pytest.fixture
def team_member_no_perms(developer_account):
    user = DeveloperUser.objects.create_user(
        email="sodic.junior@sodic.com",
        password="securepass123",
        first_name="Amr",
        last_name="Adel",
        account=developer_account,
        is_primary=False,
    )
    return user


@pytest.fixture
def team_member_with_view_perm(developer_account):
    user = DeveloperUser.objects.create_user(
        email="sodic.viewer@sodic.com",
        password="securepass123",
        first_name="Rana",
        last_name="Hesham",
        account=developer_account,
        is_primary=False,
    )
    perm, _ = Permission.objects.get_or_create(codename="view_leads", defaults={"name": "عرض العملاء المحتملين"})
    user.permissions.add(perm)
    return user


@pytest.mark.django_db
class TestMarketingLeadCreate:
    def test_public_marketing_lead_create(self, api_client, project):
        payload = {
            "project": project.id,
            "name": "Mahmoud Zaki",
            "phone": "01012345678",
            "source": "facebook",
            "campaign_name": "Summer 2026",
        }
        response = api_client.post("/api/v1/contact/lead/", payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert MarketingLead.objects.filter(phone="01012345678").exists()


@pytest.mark.django_db
class TestDeveloperLeadAccessAndRating:
    def test_list_leads_enforces_view_leads_permission(self, api_client, team_member_no_perms, team_member_with_view_perm):
        token_no_perm, _ = DeveloperAuthToken.objects.get_or_create(user=team_member_no_perms)
        api_client.credentials(HTTP_AUTHORIZATION=f"Token {token_no_perm.key}")
        response = api_client.get("/api/v1/developer/leads/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

        token_with_perm, _ = DeveloperAuthToken.objects.get_or_create(user=team_member_with_view_perm)
        api_client.credentials(HTTP_AUTHORIZATION=f"Token {token_with_perm.key}")
        response = api_client.get("/api/v1/developer/leads/")
        assert response.status_code == status.HTTP_200_OK

    def test_list_and_patch_inquiry_lead(self, api_client, primary_developer_user, property_listing):
        token, _ = DeveloperAuthToken.objects.get_or_create(user=primary_developer_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        inquiry = Inquiry.objects.create(
            property=property_listing,
            project=property_listing.project,
            name="Omar Sherif",
            phone="+201123456789",
            message="Interested in the villa",
        )

        # List should include this inquiry
        response = api_client.get("/api/v1/developer/leads/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["meta"]["count"] == 1
        assert response.data["data"][0]["name"] == "Omar Sherif"

        # PATCH rating and status
        patch_payload = {
            "status": "contacted",
            "rating": "excellent",
        }
        patch_response = api_client.patch(f"/api/v1/developer/leads/{inquiry.id}/", patch_payload, format="json")
        assert patch_response.status_code == status.HTTP_200_OK
        assert patch_response.data["status"] == "contacted"
        assert patch_response.data["rating"] == "excellent"

        inquiry.refresh_from_db()
        assert inquiry.status == InquiryStatus.CONTACTED
        assert inquiry.rating == "excellent"

    def test_patch_lead_enforces_rate_leads_permission(self, api_client, team_member_with_view_perm, property_listing):
        token, _ = DeveloperAuthToken.objects.get_or_create(user=team_member_with_view_perm)
        api_client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        inquiry = Inquiry.objects.create(
            property=property_listing,
            project=property_listing.project,
            name="Nouran Tarek",
            phone="+201234567890",
        )

        patch_payload = {"rating": "good"}
        response = api_client.patch(f"/api/v1/developer/leads/{inquiry.id}/", patch_payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_export_leads_csv(self, api_client, primary_developer_user, project, property_listing):
        token, _ = DeveloperAuthToken.objects.get_or_create(user=primary_developer_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        MarketingLead.objects.create(
            project=project,
            name="Maged Adly",
            phone="+201099887766",
            source="facebook",
        )
        Inquiry.objects.create(
            property=property_listing,
            project=project,
            name="Laila Mourad",
            phone="+201199887766",
        )

        response = api_client.get("/api/v1/developer/leads/export/")
        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "text/csv"
        content = response.content.decode("utf-8-sig")
        assert "Maged Adly" in content
        assert "Laila Mourad" in content


@pytest.mark.django_db
class TestDashboardOverviewWithInquiries:
    def test_overview_includes_inquiries_and_marketing_leads(
        self, api_client, primary_developer_user, project, property_listing
    ):
        token, _ = DeveloperAuthToken.objects.get_or_create(user=primary_developer_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        MarketingLead.objects.create(
            project=project,
            name="Lead 1",
            phone="+201011111111",
            source="facebook",
        )
        Inquiry.objects.create(
            property=property_listing,
            project=project,
            name="Lead 2",
            phone="+201022222222",
            source="contact",
        )

        response = api_client.get("/api/v1/developer/dashboard/overview/")
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert data["leads"]["marketing_total"] == 1
        assert data["leads"]["inquiries_total"] == 1
        assert data["leads"]["total"] == 2
