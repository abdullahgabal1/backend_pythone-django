"""Business logic for the fixed-sequence property recommendation survey."""
from typing import Any

from django.db import transaction
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from apps.ai.consultation_scoring import score_property_for_track
from apps.ai.models import SurveyAnswer, SurveyQuestion, SurveyResult, SurveySession
from apps.properties.models import Property
from apps.properties.serializers import PropertyListSerializer


@transaction.atomic
def start_survey(user):
    # Retrieve the first question based on 'order'
    first_question = SurveyQuestion.objects.order_by("order").first()
    if not first_question:
        raise NotFound("No survey questions found in the database. Please add them via the Admin panel.")
    session = SurveySession.objects.create(user=user if getattr(user, "is_authenticated", False) else None)
    return session, first_question


def get_session_for_request(request, session_id):
    try:
        session = SurveySession.objects.get(pk=session_id)
    except SurveySession.DoesNotExist as exc:
        raise NotFound("Survey session was not found.") from exc
    if session.user_id and session.user_id != getattr(request.user, "id", None):
        raise PermissionDenied("This survey belongs to another user.")
    return session


def _serialize_matches(session):
    # Fetch answers
    answers = {answer.question.key: answer.value for answer in session.answers.select_related("question")}
    
    # ─── Option B: Keyword Search (Free Text Extraction) ───
    # If the user typed free-text, we try to extract known keywords to map to our existing logic.
    free_text_values = []
    for answer in session.answers.all():
        if answer.question.question_type == "free_text" and isinstance(answer.value, str):
            free_text_values.append(answer.value.lower())
    
    if free_text_values:
        combined_text = " ".join(free_text_values)
        
        # 1. Extract Unit Types (villa, apartment, etc)
        extracted_types = []
        if any(w in combined_text for w in ["فيلا", "villa"]):
            extracted_types.append("villa")
        if any(w in combined_text for w in ["شقة", "شقق", "apartment"]):
            extracted_types.append("apartment")
        if any(w in combined_text for w in ["دوبلكس", "duplex"]):
            extracted_types.append("duplex")
        if any(w in combined_text for w in ["تاون هاوس", "townhouse"]):
            extracted_types.append("townhouse")
            
        if extracted_types:
            # Merge with existing
            existing_types = answers.get("unit_types", [])
            if isinstance(existing_types, list):
                answers["unit_types"] = list(set(existing_types + extracted_types))
            else:
                answers["unit_types"] = extracted_types
                
        # 2. Extract Must-haves (pool, parking, etc)
        extracted_must_haves = []
        if any(w in combined_text for w in ["مسبح", "حمام سباحة", "pool"]):
            extracted_must_haves.append("pool")
        if any(w in combined_text for w in ["جراج", "موقف", "parking", "سيارات"]):
            extracted_must_haves.append("parking")
        if any(w in combined_text for w in ["امن", "حراسة", "security"]):
            extracted_must_haves.append("security")
            
        if extracted_must_haves:
            existing_haves = answers.get("must_haves", [])
            if isinstance(existing_haves, list):
                answers["must_haves"] = list(set(existing_haves + extracted_must_haves))
            else:
                answers["must_haves"] = extracted_must_haves

    scored = []
    qs = Property.objects.prefetch_related("images", "amenities").select_related("agent")

    # DB-level pre-filtering: budget and unit types
    budget_max = answers.get("budget_max")
    if budget_max:
        try:
            max_p = float(budget_max) * 1.3
            budget_qs = qs.filter(price__lte=max_p)
            if budget_qs.exists():
                qs = budget_qs
        except (ValueError, TypeError):
            pass

    unit_types = answers.get("unit_types")
    if unit_types and isinstance(unit_types, list):
        types_qs = qs.filter(property_type__in=unit_types)
        if types_qs.exists():
            qs = types_qs

    # Cap candidate set before in-memory scoring pass
    candidates = list(qs[:500])
    for property_obj in candidates:
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
    return scored[:3]


_get_session_for_request = get_session_for_request


def get_next_valid_question(session, current_order):
    """
    Finds the next valid question based on order and conditional branching (depends_on).
    """
    answers = {a.question_id: a.value for a in session.answers.all()}
    
    candidates = SurveyQuestion.objects.filter(order__gt=current_order).order_by("order")
    for q in candidates:
        if not q.depends_on_id:
            return q
        
        parent_answer = answers.get(q.depends_on_id)
        if not parent_answer:
            continue
            
        if isinstance(parent_answer, list):
            if q.depends_on_value in parent_answer:
                return q
        elif str(parent_answer) == q.depends_on_value:
            return q
            
    return None


@transaction.atomic
def answer_survey_question(request, data: dict[str, Any]):
    session_id = request.data.get("session_id")
    if not session_id:
        raise ValidationError({"session_id": "This field is required."})
    session = get_session_for_request(request, session_id)
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
    
    next_question = get_next_valid_question(session, question.order)
    
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
