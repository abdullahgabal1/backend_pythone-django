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
