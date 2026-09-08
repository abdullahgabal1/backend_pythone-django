from django.urls import path
from apps.marketing.views import MarketingLeadCreateView

urlpatterns = [
    path("lead/", MarketingLeadCreateView.as_view(), name="marketing-lead-create"),
]
