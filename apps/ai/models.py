"""Models for the fixed-sequence property recommendation survey."""
import uuid

from django.conf import settings
from django.db import models

from apps.common.models import TimestampedModel


class SurveySession(TimestampedModel):
    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress", "In progress"
        COMPLETED = "completed", "Completed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="survey_sessions",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.IN_PROGRESS)
    current_question_order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["-created_at"]


class SurveyQuestion(TimestampedModel):
    key = models.SlugField(max_length=50, unique=True)
    text = models.CharField(max_length=255)
    question_type = models.CharField(max_length=30, default="single_choice")
    options = models.JSONField(default=list)
    order = models.PositiveIntegerField(unique=True)
    required = models.BooleanField(default=True)

    class Meta:
        ordering = ["order"]


class SurveyAnswer(TimestampedModel):
    session = models.ForeignKey(SurveySession, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(SurveyQuestion, on_delete=models.PROTECT, related_name="answers")
    value = models.JSONField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["session", "question"], name="unique_survey_answer"),
        ]


class SurveyResult(TimestampedModel):
    session = models.OneToOneField(SurveySession, on_delete=models.CASCADE, related_name="result")
    top_properties = models.JSONField(default=list)

