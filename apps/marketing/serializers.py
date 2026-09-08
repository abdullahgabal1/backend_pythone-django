from rest_framework import serializers
from apps.marketing.models import MarketingLead

class MarketingLeadCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketingLead
        fields = ["name", "phone", "source", "campaign_name", "project"]
