"""Serializers for the fixed-sequence property survey."""
from rest_framework import serializers
from apps.ai.models import SurveyQuestion, SurveyResult


class SurveyQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurveyQuestion
        fields = ["id", "key", "text", "question_type", "options", "required", "order"]


class SurveyAnswerSerializer(serializers.Serializer):
    question_id = serializers.IntegerField(required=False)
    question_key = serializers.CharField(required=False)
    answer = serializers.JSONField()

    def validate(self, attrs):
        if not attrs.get("question_id") and not attrs.get("question_key"):
            raise serializers.ValidationError("question_id or question_key is required")
        return attrs


class SurveyResultSerializer(serializers.ModelSerializer):
    session_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = SurveyResult
        fields = ["session_id", "top_properties", "created_at"]
