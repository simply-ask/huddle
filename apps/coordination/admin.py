from django.contrib import admin
from .models import CoordinationDecision, AudioQualityMetric

@admin.register(CoordinationDecision)
class CoordinationDecisionAdmin(admin.ModelAdmin):
    list_display = ['meeting', 'primary_recorder', 'algorithm_version', 'created_at']
    list_filter = ['algorithm_version', 'created_at']
    search_fields = ['meeting__meeting_id', 'primary_recorder__user__username']
    readonly_fields = ['created_at']

@admin.register(AudioQualityMetric)
class AudioQualityMetricAdmin(admin.ModelAdmin):
    list_display = ['participant', 'volume_level', 'clarity_score', 'overall_score', 'created_at']
    list_filter = ['created_at']
    search_fields = ['participant__meeting__meeting_id']