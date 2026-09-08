"""URL configuration for the fixed-sequence survey."""
from django.urls import path
from apps.ai.views import SurveyAnswerView, SurveyResultsView, SurveyStartView

urlpatterns = [
    path("survey/start/", SurveyStartView.as_view(), name="ai-survey-start"),
    path("survey/answer/", SurveyAnswerView.as_view(), name="ai-survey-answer"),
    path("survey/<uuid:session_id>/results/", SurveyResultsView.as_view(), name="ai-survey-results"),
]
