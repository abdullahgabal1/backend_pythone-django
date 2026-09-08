"""Business logic for the fixed-sequence property recommendation survey."""
from typing import Any

from django.db import transaction
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from apps.ai.consultation_scoring import score_property_for_track
from apps.ai.models import SurveyAnswer, SurveyQuestion, SurveyResult, SurveySession
from apps.properties.models import Property
from apps.properties.serializers import PropertyListSerializer


QUESTION_BANK = [
    {"key": "budget_max", "text": "What is your maximum budget in Egyptian pounds?", "question_type": "currency", "options": []},
    {"key": "financing_needed", "text": "Which payment method do you prefer?", "options": ["cash", "installment", "mortgage", "any"]},
    {"key": "timeline", "text": "When would you like to receive the property?", "options": ["ready", "within_1_year", "within_3_years"]},
    {"key": "household_size", "text": "How many bedrooms do you need?", "options": ["single_or_couple", "small_family", "large_family"]},
    {"key": "preferred_areas", "text": "Which areas do you prefer?", "question_type": "multi_choice", "options": ["التجمع الخامس", "الشيخ زايد", "المعادي", "الشروق", "الساحل الشمالي", "open_to_suggestions"]},
    {"key": "unit_types", "text": "Which property types interest you?", "question_type": "multi_choice", "options": ["apartment", "villa", "townhouse", "duplex", "penthouse"]},
    {"key": "must_haves", "text": "Which features are essential?", "question_type": "multi_choice", "options": ["parking", "pool", "security", "schools_nearby", "transit_access"]},
]


def _ensure_question_bank() -> None:
    for order, definition in enumerate(QUESTION_BANK, start=1):
        SurveyQuestion.objects.update_or_create(
            key=definition["key"],
            defaults={
                "text": definition["text"],
                "question_type": definition.get("question_type", "single_choice"),
                "options": definition["options"],
                "order": order,
                "required": True,
            },
        )


@transaction.atomic
def start_survey(user):
    _ensure_question_bank()
    session = SurveySession.objects.create(user=user if getattr(user, "is_authenticated", False) else None)
    return session, SurveyQuestion.objects.get(order=1)


def _get_session_for_request(request, session_id):
    try:
        session = SurveySession.objects.get(pk=session_id)
    except SurveySession.DoesNotExist as exc:
        raise NotFound("Survey session was not found.") from exc
    if session.user_id and session.user_id != getattr(request.user, "id", None):
        raise PermissionDenied("This survey belongs to another user.")
    return session


def _serialize_matches(session):
    answers = {answer.question.key: answer.value for answer in session.answers.select_related("question")}
    scored = []
    properties = Property.objects.prefetch_related("images", "amenities").select_related("agent")
    for property_obj in properties:
        score = score_property_for_track(property_obj, "homebuyer", answers)
        scored.append({
            "property": PropertyListSerializer(property_obj).data,
            "property_id": property_obj.id,
            "title": property_obj.title,
            "match_percentage": score["match_percentage"],
            "score": score["score"],
            "tags": score["tags"],
            "reasons": score["reasons"],
        })
    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:4]


@transaction.atomic
def answer_survey_question(request, data: dict[str, Any]):
    session_id = request.data.get("session_id")
    if not session_id:
        raise ValidationError({"session_id": "This field is required."})
    session = _get_session_for_request(request, session_id)
    if session.status == SurveySession.Status.COMPLETED:
        raise ValidationError("This survey is already complete.")

    if data.get("question_id"):
        question = SurveyQuestion.objects.filter(pk=data["question_id"]).first()
    else:
        question = SurveyQuestion.objects.filter(key=data.get("question_key")).first()
    if question is None:
        raise NotFound("Survey question was not found.")
    if question.order != session.current_question_order:
        raise ValidationError({"question": "Answers must be submitted in sequence."})

    SurveyAnswer.objects.update_or_create(session=session, question=question, defaults={"value": data["answer"]})
    next_question = SurveyQuestion.objects.filter(order__gt=question.order).first()
    if next_question:
        session.current_question_order = next_question.order
        session.save(update_fields=["current_question_order", "updated_at"])
        return {"session_id": session.id, "completed": False, "question": {
            "id": next_question.id, "key": next_question.key, "text": next_question.text,
            "question_type": next_question.question_type, "options": next_question.options,
            "required": next_question.required, "order": next_question.order,
        }}

    top_properties = _serialize_matches(session)
    session.status = SurveySession.Status.COMPLETED
    session.save(update_fields=["status", "updated_at"])
    result = SurveyResult.objects.create(session=session, top_properties=top_properties)
    return {"session_id": session.id, "completed": True, "result": {
        "session_id": result.session_id, "top_properties": result.top_properties, "created_at": result.created_at,
    }}
