"""
Developer Accounts — URLs
===========================
Routes for developer authentication and team management.
"""
from django.urls import path
from apps.developer_accounts.views import (
    AccountView,
    LoginView,
    RegisterView,
    TeamCreateView,
    TeamDetailView,
    TeamListView,
)

urlpatterns = [
    path("login/", LoginView.as_view(), name="developer-login"),
    path("register/", RegisterView.as_view(), name="developer-register"),
    path("account/", AccountView.as_view(), name="developer-account"),
    path("team/", TeamListView.as_view(), name="developer-team-list"),
    path("team/invite/", TeamCreateView.as_view(), name="developer-team-create"),
    path("team/<int:pk>/", TeamDetailView.as_view(), name="developer-team-detail"),
]
