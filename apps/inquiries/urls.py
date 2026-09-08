"""
Inquiries — URL Configuration
==============================
Routes for creating inquiries and checking buyer inquiry history.
"""
from django.urls import path
from apps.inquiries.views import InquiryCreateView, InquiryDetailView, MyInquiriesListView

urlpatterns = [
    path("", InquiryCreateView.as_view(), name="inquiry-create"),
    path("my/", MyInquiriesListView.as_view(), name="inquiry-my-list"),
    path("<int:pk>/", InquiryDetailView.as_view(), name="inquiry-detail"),
]
