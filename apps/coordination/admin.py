from django.contrib import admin
from .models import CoordinationDecision, AudioQualityMetric

@admin.register(CoordinationDecision)
class CoordinationDecisionAdmin(admin.ModelAdmin):
    list_display = ['meeting', 'selected_recorder', 'algorithm', 'confidence', 'created_at']
    list_filter = ['algorithm', 'created_at']
    search_fields = ['meeting__meeting_id', 'selected_recorder__user__username']
    readonly_fields = ['created_at']

@admin.register(AudioQualityMetric)
class AudioQualityMetricAdmin(admin.ModelAdmin):
    list_display = ['recording', 'volume_level', 'clarity_score', 'created_at']
    list_filter = ['created_at']
    search_fields = ['recording__meeting__meeting_id']