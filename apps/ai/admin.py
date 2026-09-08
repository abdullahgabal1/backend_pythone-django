"""Admin registration for the fixed-sequence survey models."""
from django.contrib import admin
from apps.ai.models import SurveyAnswer, SurveyQuestion, SurveyResult, SurveySession


@admin.register(SurveyQuestion)
class SurveyQuestionAdmin(admin.ModelAdmin):
    list_display = ("order", "key", "question_type", "required")
    ordering = ("order",)


@admin.register(SurveySession)
class SurveySessionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "current_question_order", "created_at")
    list_filter = ("status", "created_at")
    readonly_fields = ("created_at", "updated_at")


@admin.register(SurveyAnswer)
class SurveyAnswerAdmin(admin.ModelAdmin):
    list_display = ("session", "question", "created_at")
    list_select_related = ("session", "question")


@admin.register(SurveyResult)
class SurveyResultAdmin(admin.ModelAdmin):
    list_display = ("session", "created_at")
    readonly_fields = ("created_at", "updated_at")
