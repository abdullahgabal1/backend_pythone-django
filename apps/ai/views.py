"""Views for the fixed-sequence property recommendation survey."""
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.ai.models import SurveyQuestion, SurveyResult, SurveySession
from apps.ai.serializers import (
    SurveyAnswerSerializer,
    SurveyQuestionSerializer,
    SurveyResultSerializer,
)
from apps.ai.services import (
    answer_survey_question,
    get_session_for_request,
    start_survey,
)


class SurveyStartView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = SurveyQuestionSerializer

    def post(self, request):
        session, question = start_survey(request.user)
        return Response(
            {
                "session_id": session.id,
                "question": SurveyQuestionSerializer(question).data,
            },
            status=status.HTTP_201_CREATED,
        )


class SurveyAnswerView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = SurveyAnswerSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = answer_survey_question(request, serializer.validated_data)
        return Response(result, status=status.HTTP_200_OK)


class SurveyResultsView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = SurveyResultSerializer

    def get(self, request, session_id):
        session = get_session_for_request(request, session_id)
        if session.status != SurveySession.Status.COMPLETED:
            return Response(
                {"detail": "Survey is not complete."},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(self.get_serializer(session.result).data)
