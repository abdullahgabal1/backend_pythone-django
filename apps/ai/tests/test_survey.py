from datetime import date
from decimal import Decimal

import pytest
from django.urls import reverse

from apps.properties.models import Property


@pytest.mark.django_db
def test_fixed_sequence_survey_returns_top_four(api_client):
    Property.objects.create(
        title="Family apartment",
        description="A complete family home in New Cairo.",
        location="التجمع الخامس",
        price=Decimal("4000000"),
        area_sqm=160,
        beds=3,
        baths=2,
        property_type="apartment",
        completion_status="ready",
        furnishing="unfurnished",
        payment_method="installment",
        parking=1,
    )

    response = api_client.post(reverse("ai-survey-start"), {}, format="json")
    assert response.status_code == 201
    payload = response.json()["data"]
    session_id = payload["session_id"]
    question = payload["question"]

    answers = {
        "budget_max": "5000000",
        "financing_needed": "installment",
        "timeline": "ready",
        "household_size": "small_family",
        "preferred_areas": ["التجمع الخامس"],
        "unit_types": ["apartment"],
        "must_haves": ["parking"],
    }
    completed = None
    for key, value in answers.items():
        response = api_client.post(
            reverse("ai-survey-answer"),
            {"session_id": session_id, "question_id": question["id"], "answer": value},
            format="json",
        )
        assert response.status_code == 200
        completed = response.json()["data"]
        if not completed["completed"]:
            question = completed["question"]

    assert completed["completed"] is True
    assert len(completed["result"]["top_properties"]) == 1
    result_response = api_client.get(reverse("ai-survey-results", args=[session_id]))
    assert result_response.status_code == 200
    assert result_response.json()["data"]["session_id"] == session_id


@pytest.mark.django_db
def test_survey_results_ownership_check(api_client):
    from apps.ai.models import SurveySession, SurveyResult
    from apps.users.models import User

    user_a = User.objects.create_user(phone="01011111111", name="User A", birthday=date(1995, 1, 1))
    user_b = User.objects.create_user(phone="01022222222", name="User B", birthday=date(1995, 1, 1))

    session = SurveySession.objects.create(user=user_a, status=SurveySession.Status.COMPLETED)
    SurveyResult.objects.create(session=session, top_properties=[])

    # Unauthenticated / user B requests session owned by user A -> 403
    api_client.force_authenticate(user=user_b)
    response = api_client.get(reverse("ai-survey-results", args=[session.id]))
    assert response.status_code == 403

    # User A requests their own session -> 200
    api_client.force_authenticate(user=user_a)
    response = api_client.get(reverse("ai-survey-results", args=[session.id]))
    assert response.status_code == 200
