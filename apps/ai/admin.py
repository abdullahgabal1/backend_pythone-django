"""
Admin registration for the AI Survey engine.
─────────────────────────────────────────────
Provides a user-friendly interface for managing survey questions,
conditional branching (groups), sessions, answers, and results.
"""
from django.contrib import admin
from django import forms
from django.utils.html import format_html

from apps.ai.models import SurveyAnswer, SurveyQuestion, SurveyResult, SurveySession


# ─── Custom Form for SurveyQuestion ──────────────────────────────
class SurveyQuestionForm(forms.ModelForm):
    """
    Custom form that makes editing options easier.
    Instead of raw JSON, the admin sees a simple textarea
    with one option per line.
    """
    options_text = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 5, "cols": 60, "placeholder": "cash\ninstallment\nmortgage\nany"}),
        required=False,
        label="Answer Choices (one per line)",
        help_text="Type each choice on its own line. Leave empty for Free Text questions.",
    )

    class Meta:
        model = SurveyQuestion
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Convert the stored JSON list into newline-separated text for easy editing
        if self.instance and self.instance.pk and self.instance.options:
            self.initial["options_text"] = "\n".join(
                str(opt) for opt in self.instance.options
            )

    def clean_options_text(self):
        raw = self.cleaned_data.get("options_text", "")
        if not raw.strip():
            return []
        return [line.strip() for line in raw.splitlines() if line.strip()]

    def clean(self):
        cleaned = super().clean()
        # Write the parsed list back into the actual 'options' JSON field
        cleaned["options"] = self.cleaned_data.get("options_text", [])
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.options = self.cleaned_data.get("options_text", [])
        if commit:
            instance.save()
        return instance


# ─── SurveyQuestion Admin ────────────────────────────────────────
@admin.register(SurveyQuestion)
class SurveyQuestionAdmin(admin.ModelAdmin):
    form = SurveyQuestionForm

    # ── List View ──
    list_display = ("order_badge", "text", "question_type_badge", "parent_display", "required")
    list_display_links = ("text",)
    ordering = ("order",)
    list_filter = ("question_type", "required", "depends_on")
    search_fields = ("key", "text")

    # ── Edit View: organized into clear sections ──
    fieldsets = (
        ("📝 Question Content", {
            "fields": ("text", "question_type", "options_text"),
            "description": "Write the question and its available choices.",
        }),
        ("⚙️ Settings", {
            "fields": ("key", "order", "required"),
            "description": "⚠️ Only change 'Key' if you know what you are doing — the AI engine relies on these keys.",
        }),
        ("🔀 Conditional Branching (Groups)", {
            "fields": ("depends_on", "depends_on_value"),
            "classes": ("collapse",),
            "description": (
                "Use this to create question groups. "
                "Set 'Parent Question' to a previous question, and 'Trigger Answer' "
                "to the specific choice that should unlock this question. "
                "Leave both empty if this question should always be shown."
            ),
        }),
    )

    # Exclude the raw JSON 'options' field — we use 'options_text' instead
    exclude = ("options",)

    def order_badge(self, obj):
        return format_html(
            '<span style="background:#4a90d9;color:#fff;padding:3px 10px;'
            'border-radius:12px;font-weight:bold;">Q{}</span>',
            obj.order,
        )
    order_badge.short_description = "#"
    order_badge.admin_order_field = "order"

    def question_type_badge(self, obj):
        colors = {
            "single_choice": "#27ae60",
            "multi_choice": "#8e44ad",
            "free_text": "#e67e22",
            "currency": "#2980b9",
        }
        color = colors.get(obj.question_type, "#7f8c8d")
        label = obj.get_question_type_display()
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:8px;font-size:11px;">{}</span>',
            color, label,
        )
    question_type_badge.short_description = "Type"
    question_type_badge.admin_order_field = "question_type"

    def parent_display(self, obj):
        if not obj.depends_on_id:
            return format_html('<span style="color:#999;">— Always shown —</span>')
        return format_html(
            '↳ If <b>Q{}</b> = "<i>{}</i>"',
            obj.depends_on.order,
            obj.depends_on_value,
        )
    parent_display.short_description = "Group / Branch"


# ─── SurveySession Admin ─────────────────────────────────────────
class SurveyAnswerInline(admin.TabularInline):
    """Show all answers inline inside a session for quick review."""
    model = SurveyAnswer
    extra = 0
    readonly_fields = ("question", "value", "created_at")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(SurveySession)
class SurveySessionAdmin(admin.ModelAdmin):
    list_display = ("short_id", "user", "status_badge", "current_question_order", "created_at")
    list_filter = ("status", "created_at")
    readonly_fields = ("id", "user", "status", "current_question_order", "created_at", "updated_at")
    inlines = [SurveyAnswerInline]

    def short_id(self, obj):
        return str(obj.id)[:8] + "…"
    short_id.short_description = "Session ID"

    def status_badge(self, obj):
        color = "#27ae60" if obj.status == "completed" else "#e67e22"
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:8px;font-size:11px;">{}</span>',
            color, obj.get_status_display(),
        )
    status_badge.short_description = "Status"

    def has_add_permission(self, request):
        return False


# ─── SurveyAnswer Admin ──────────────────────────────────────────
@admin.register(SurveyAnswer)
class SurveyAnswerAdmin(admin.ModelAdmin):
    list_display = ("session_short", "question", "value", "created_at")
    list_select_related = ("session", "question")
    list_filter = ("question",)
    readonly_fields = ("session", "question", "value", "created_at")

    def session_short(self, obj):
        return str(obj.session_id)[:8] + "…"
    session_short.short_description = "Session"

    def has_add_permission(self, request):
        return False


# ─── SurveyResult Admin ──────────────────────────────────────────
@admin.register(SurveyResult)
class SurveyResultAdmin(admin.ModelAdmin):
    list_display = ("session_short", "num_properties", "created_at")
    readonly_fields = ("session", "top_properties", "created_at", "updated_at")

    def session_short(self, obj):
        return str(obj.session_id)[:8] + "…"
    session_short.short_description = "Session"

    def num_properties(self, obj):
        count = len(obj.top_properties) if obj.top_properties else 0
        return f"{count} properties"
    num_properties.short_description = "Results"

    def has_add_permission(self, request):
        return False
