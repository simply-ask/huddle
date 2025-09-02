from django.contrib import admin
from .models import AudioRecording, TranscriptionSegment, AudioQualityMetric

@admin.register(AudioRecording)
class AudioRecordingAdmin(admin.ModelAdmin):
    list_display = ['meeting', 'participant', 'duration', 'file_size', 'created_at']
    list_filter = ['created_at', 'meeting__status']
    search_fields = ['meeting__meeting_id', 'participant__user__username']
    readonly_fields = ['created_at', 'updated_at', 'file_size']

@admin.register(TranscriptionSegment)
class TranscriptionSegmentAdmin(admin.ModelAdmin):
    list_display = ['audio_recording', 'start_time', 'end_time', 'speaker', 'confidence']
    list_filter = ['confidence', 'audio_recording__created_at']
    search_fields = ['text', 'speaker', 'audio_recording__meeting__meeting_id']

@admin.register(AudioQualityMetric)
class AudioQualityMetricAdmin(admin.ModelAdmin):
    list_display = ['recording', 'volume_level', 'clarity_score', 'created_at']
    list_filter = ['created_at']