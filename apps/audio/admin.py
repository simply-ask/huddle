from django.contrib import admin
from .models import AudioRecording, TranscriptionSegment, AudioQualityMetric, MeetingSummary

@admin.register(AudioRecording)
class AudioRecordingAdmin(admin.ModelAdmin):
    list_display = ['meeting', 'participant', 'duration_seconds', 'file_size', 'created_at']
    list_filter = ['created_at', 'is_processed']
    search_fields = ['meeting__meeting_id', 'participant__user__username']
    readonly_fields = ['created_at', 'updated_at', 'file_size']

@admin.register(TranscriptionSegment)
class TranscriptionSegmentAdmin(admin.ModelAdmin):
    list_display = ['recording', 'start_time', 'end_time', 'speaker_id', 'confidence']
    list_filter = ['confidence', 'recording__created_at']
    search_fields = ['text', 'speaker_id', 'recording__meeting__meeting_id']

@admin.register(AudioQualityMetric)
class AudioQualityMetricAdmin(admin.ModelAdmin):
    list_display = ['recording', 'volume_level', 'clarity_score', 'created_at']
    list_filter = ['created_at']

@admin.register(MeetingSummary)
class MeetingSummaryAdmin(admin.ModelAdmin):
    list_display = ['meeting', 'created_at']
    search_fields = ['meeting__meeting_id', 'summary']
    readonly_fields = ['created_at', 'updated_at']