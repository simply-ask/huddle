from django.db import models
from django.contrib.auth.models import User

class TimeStampedModel(models.Model):
    """Abstract base class with created and modified timestamps"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class SpeakerProfile(TimeStampedModel):
    """Persistent voice profiles for meeting participants"""
    organization = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        help_text="Company/team owner"
    )
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    job_title = models.CharField(max_length=100, blank=True)
    
    # Voice characteristics
    voice_signature = models.JSONField(
        default=dict, 
        help_text="Audio fingerprint data"
    )
    sample_audio = models.FileField(
        upload_to='voice-samples/%Y/%m/',
        blank=True,
        help_text="Reference audio sample"
    )
    
    # Statistics
    meetings_count = models.IntegerField(
        default=0, 
        help_text="Number of meetings attended"
    )
    accuracy_score = models.FloatField(
        default=0.0, 
        help_text="Recognition accuracy over time"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'huddle_speaker_profile'
        unique_together = ['organization', 'email']
    
    def __str__(self):
        return f"{self.full_name} ({self.email})"

class VoiceSetupToken(TimeStampedModel):
    """Secure tokens for voice setup links"""
    meeting_id = models.CharField(max_length=8)
    email = models.EmailField()
    token = models.CharField(max_length=64, unique=True)
    used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'huddle_voice_setup_token'