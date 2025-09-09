from django.db import models
from django.contrib.auth.models import User
from apps.core.models import TimeStampedModel, SpeakerProfile
from apps.core.utils import generate_meeting_id

class Meeting(TimeStampedModel):
    MEETING_TYPE_CHOICES = [
        ('in_person', 'In Person'),
        ('virtual', 'Virtual'),
        ('hybrid', 'Hybrid'),
    ]
    
    meeting_id = models.CharField(max_length=8, unique=True, default=generate_meeting_id)
    title = models.CharField(max_length=200, blank=True)
    host = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    organization_name = models.CharField(max_length=255, blank=True, null=True, help_text="From simplyAsk UserProfile")
    is_active = models.BooleanField(default=True)
    
    # Scheduling fields
    meeting_type = models.CharField(max_length=20, choices=MEETING_TYPE_CHOICES, default='in_person')
    scheduled_start = models.DateTimeField(null=True, blank=True, help_text="Scheduled meeting start time")
    scheduled_duration = models.IntegerField(default=60, help_text="Duration in minutes")
    location = models.CharField(max_length=255, blank=True, help_text="Physical location for in-person/hybrid meetings")
    meeting_link = models.URLField(max_length=500, blank=True, help_text="Virtual meeting link")
    
    # Actual meeting times
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    # Speaker management
    expected_speakers = models.JSONField(
        default=list, 
        help_text="List of expected speaker emails"
    )
    known_speakers = models.ManyToManyField(
        SpeakerProfile, 
        blank=True, 
        help_text="Speakers with existing voice profiles"
    )
    
    class Meta:
        db_table = 'huddle_meeting'
    
    def __str__(self):
        return f"Meeting {self.meeting_id} - {self.title or 'Untitled'}"
    
    def get_new_speakers(self):
        """Get list of speakers who need voice setup"""
        known_emails = set(self.known_speakers.values_list('email', flat=True))
        new_speakers = []
        
        for email in self.expected_speakers:
            if email not in known_emails:
                new_speakers.append({
                    'email': email,
                    'name': self.extract_name_from_email(email),
                    'needs_setup': True
                })
        
        return new_speakers
    
    @staticmethod
    def extract_name_from_email(email):
        """Extract likely name from email address"""
        name_part = email.split('@')[0]
        # Convert john.smith -> John Smith
        return ' '.join(word.capitalize() for word in name_part.replace('.', ' ').replace('_', ' ').split())

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