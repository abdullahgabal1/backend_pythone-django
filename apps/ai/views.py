"""Views for the fixed-sequence property recommendation survey."""
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ai.models import SurveyQuestion
from apps.ai.serializers import SurveyAnswerSerializer, SurveyQuestionSerializer, SurveyResultSerializer
from apps.ai.services import answer_survey_question, start_survey


class SurveyStartView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        session, question = start_survey(request.user)
        return Response({"session_id": session.id, "question": SurveyQuestionSerializer(question).data}, status=201)


class SurveyAnswerView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SurveyAnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = answer_survey_question(request, serializer.validated_data)
        return Response(result, status=status.HTTP_200_OK)


class SurveyResultsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, session_id):
        from apps.ai.models import SurveySession
        from django.shortcuts import get_object_or_404

        session = get_object_or_404(SurveySession, pk=session_id)
        if session.status != SurveySession.Status.COMPLETED:
            return Response({"detail": "Survey is not complete."}, status=status.HTTP_409_CONFLICT)
        return Response(SurveyResultSerializer(session.result).data)
