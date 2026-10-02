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
    class QuestionType(models.TextChoices):
        SINGLE_CHOICE = "single_choice", "Single Choice (اختيار واحد)"
        MULTI_CHOICE = "multi_choice", "Multi Choice (اختيار متعدد)"
        FREE_TEXT = "free_text", "Free Text (كتابة حرة)"
        CURRENCY = "currency", "Currency / Number (مبلغ مالي)"

    key = models.SlugField(
        max_length=50, unique=True,
        help_text="⚠️ Used by the AI engine internally. Do NOT change existing keys.",
    )
    text = models.CharField(
        max_length=255,
        help_text="The question text shown to the buyer (Arabic or English).",
    )
    question_type = models.CharField(
        max_length=30,
        choices=QuestionType.choices,
        default=QuestionType.SINGLE_CHOICE,
        help_text="Single Choice = one answer, Multi Choice = multiple answers, Free Text = buyer types freely.",
    )
    options = models.JSONField(
        default=list, blank=True,
        help_text='List of choices as JSON. Example: ["cash", "installment", "mortgage"]. Leave empty for Free Text.',
    )
    order = models.PositiveIntegerField(
        unique=True,
        help_text="Controls the sequence. Lower number = asked first.",
    )
    required = models.BooleanField(default=True)

    # ─── Conditional Branching (Groups) ───────────────────────
    depends_on = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="dependent_questions",
        verbose_name="Parent Question",
        help_text="Leave empty = always shown. Set a parent = only shown if buyer picked a specific answer.",
    )
    depends_on_value = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Trigger Answer",
        help_text="The exact answer from the parent question that triggers this question.",
    )

    class Meta:
        ordering = ["order"]

    def __str__(self):
        prefix = f"Q{self.order}"
        if self.depends_on_id:
            return f"{prefix}: {self.text} (→ if '{self.depends_on_value}')"
        return f"{prefix}: {self.text}"


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

