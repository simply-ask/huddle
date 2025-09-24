from django.db import models
from django.contrib.auth.models import User
from apps.core.models import TimeStampedModel, SpeakerProfile
from apps.core.utils import generate_meeting_id

class Meeting(TimeStampedModel):
    meeting_id = models.CharField(max_length=8, unique=True, default=generate_meeting_id)
    title = models.CharField(max_length=200, blank=True)
    host = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    organization_name = models.CharField(max_length=255, blank=True, null=True, help_text="From simplyAsk UserProfile")
    is_active = models.BooleanField(default=True)
    
    # Scheduling fields
    scheduled_start = models.DateTimeField(null=True, blank=True, help_text="Scheduled meeting start time")
    scheduled_duration = models.IntegerField(default=60, help_text="Duration in minutes")
    location = models.CharField(max_length=255, blank=True, help_text="Meeting location")
    
    # Actual meeting times
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    # Meeting status choices
    class Status(models.TextChoices):
        SCHEDULED = 'scheduled', 'Scheduled'
        ACTIVE = 'active', 'In Progress'
        COMPLETED = 'completed', 'Completed'

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.SCHEDULED,
        help_text="Current meeting status"
    )
    
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

    @property
    def is_active(self):
        """Check if meeting is currently active"""
        return self.status == self.Status.ACTIVE

    @property
    def is_completed(self):
        """Check if meeting is completed"""
        return self.status == self.Status.COMPLETED

    @property
    def has_recordings(self):
        """Check if meeting has any recordings"""
        return self.recordings.exists()

    @property
    def has_transcripts(self):
        """Check if meeting has processed transcripts"""
        return self.recordings.filter(is_processed=True).exists()

    def start_meeting(self):
        """Start the meeting - called when first recording begins"""
        from django.utils import timezone
        if not self.started_at:
            self.started_at = timezone.now()
        self.status = self.Status.ACTIVE
        self.save()

    def end_meeting(self):
        """End the meeting - called when host clicks 'End Meeting'"""
        from django.utils import timezone
        self.ended_at = timezone.now()
        self.status = self.Status.COMPLETED
        self.save()
    
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


class AgendaItem(TimeStampedModel):
    """Agenda items for structured meetings"""
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='agenda_items')
    title = models.CharField(max_length=200, help_text="Agenda item title")
    assigned_participant = models.CharField(
        max_length=100,
        blank=True,
        help_text="Email of participant assigned to this agenda item"
    )
    order = models.PositiveIntegerField(default=0, help_text="Display order of agenda item")

    class Meta:
        db_table = 'huddle_agenda_item'
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"{self.meeting.meeting_id}: {self.title}"

    @property
    def participant_name(self):
        """Get friendly name for assigned participant"""
        if not self.assigned_participant:
            return None
        return Meeting.extract_name_from_email(self.assigned_participant)


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