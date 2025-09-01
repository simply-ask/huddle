from django.db import models
from apps.core.models import TimeStampedModel
from apps.meetings.models import Meeting, MeetingParticipant

class CoordinationDecision(TimeStampedModel):
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='coordination_decisions')
    primary_recorder = models.ForeignKey(MeetingParticipant, on_delete=models.CASCADE, related_name='primary_recordings')
    backup_recorders = models.ManyToManyField(MeetingParticipant, related_name='backup_recordings', blank=True)
    algorithm_version = models.CharField(max_length=20, default='1.0')
    decision_factors = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'huddle_coordination_decision'
    
    def __str__(self):
        return f"Coordination for {self.meeting.meeting_id} - Primary: {self.primary_recorder.session_id}"

class AudioQualityMetric(TimeStampedModel):
    participant = models.ForeignKey(MeetingParticipant, on_delete=models.CASCADE, related_name='quality_metrics')
    volume_level = models.FloatField(null=True, blank=True)
    background_noise = models.FloatField(null=True, blank=True)
    clarity_score = models.FloatField(null=True, blank=True)
    proximity_score = models.FloatField(null=True, blank=True)
    overall_score = models.FloatField(null=True, blank=True)
    
    class Meta:
        db_table = 'huddle_audio_quality_metric'