from django.urls import path
from apps.projects.views import ProjectDetailView, ProjectListCreateView, ProjectStatsView

urlpatterns = [
    path("projects/", ProjectListCreateView.as_view(), name="project-list"),
    path("projects/<int:pk>/", ProjectDetailView.as_view(), name="project-detail"),
    path("projects/<int:pk>/stats/", ProjectStatsView.as_view(), name="project-stats"),
]
