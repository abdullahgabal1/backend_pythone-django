from django.contrib import admin
from apps.projects.models import Project, ProjectImage

class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 1

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["name", "account", "project_type", "status", "created_at"]
    list_filter = ["project_type", "status", "account"]
    search_fields = ["name", "account__company_name"]
    inlines = [ProjectImageInline]
