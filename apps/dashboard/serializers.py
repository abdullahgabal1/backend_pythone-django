"""
Dashboard — Serializers
=========================
Serializers for dashboard API responses (needed for drf-spectacular OpenAPI docs).
"""
from rest_framework import serializers


class ProjectStatsSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    lead_count = serializers.IntegerField()


class ProjectsSummarySerializer(serializers.Serializer):
    total = serializers.IntegerField()
    active = serializers.IntegerField()
    top_by_leads = ProjectStatsSerializer(many=True)


class LeadsSummarySerializer(serializers.Serializer):
    total = serializers.IntegerField()
    marketing_total = serializers.IntegerField()
    inquiries_total = serializers.IntegerField()
    last_30_days = serializers.IntegerField()
    by_source = serializers.DictField(child=serializers.IntegerField())


class DashboardOverviewSerializer(serializers.Serializer):
    projects = ProjectsSummarySerializer()
    leads = LeadsSummarySerializer()
    location_medians = serializers.DictField(child=serializers.FloatField(), required=False)
