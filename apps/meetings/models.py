from django.db import models
from django.contrib.auth.models import User
from apps.core.models import TimeStampedModel
from apps.core.utils import generate_meeting_id

class Meeting(TimeStampedModel):
    meeting_id = models.CharField(max_length=8, unique=True, default=generate_meeting_id)
    title = models.CharField(max_length=200, blank=True)
    host = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    organization_name = models.CharField(max_length=255, blank=True, null=True, help_text="From simplyAsk UserProfile")
    is_active = models.BooleanField(default=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'huddle_meeting'
    
    def __str__(self):
        return f"Meeting {self.meeting_id} - {self.title or 'Untitled'}"

class MeetingParticipant(TimeStampedModel):
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, help_text="Linked user if authenticated")
    session_id = models.CharField(max_length=64)
    user_agent = models.TextField(blank=True)
    is_recording = models.BooleanField(default=False)
    audio_quality_score = models.FloatField(null=True, blank=True)
    last_seen = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'huddle_meeting_participant'
        unique_together = ['meeting', 'session_id']