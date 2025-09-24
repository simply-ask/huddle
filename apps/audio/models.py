from django.db import models
from apps.core.models import TimeStampedModel
from apps.meetings.models import Meeting, MeetingParticipant

def huddle_recording_upload_path(instance, filename):
    """Upload path for Huddle audio recordings organized by user"""
    # Organize by user ID for better structure in DigitalOcean Spaces
    user_id = instance.meeting.host.id if instance.meeting.host else 'anonymous'
    meeting_id = instance.meeting.meeting_id

    # Create a structured path: recordings/user_X/meeting_Y/filename
    return f"recordings/user_{user_id}/meeting_{meeting_id}/{filename}"

class AudioRecording(TimeStampedModel):
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='recordings')
    participant = models.ForeignKey(MeetingParticipant, on_delete=models.CASCADE)
    audio_file = models.FileField(upload_to=huddle_recording_upload_path)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    file_size = models.PositiveIntegerField(null=True, blank=True)
    format = models.CharField(max_length=10)
    is_processed = models.BooleanField(default=False)
    processing_started_at = models.DateTimeField(null=True, blank=True)
    processing_completed_at = models.DateTimeField(null=True, blank=True)
    
    # Transcription service tracking
    transcription_service = models.CharField(
        max_length=20, 
        default='deepgram',
        help_text="Service used for transcription"
    )
    deepgram_request_id = models.CharField(max_length=100, null=True, blank=True)
    transcription_raw = models.JSONField(default=dict, blank=True, help_text="Raw API response")
    
    class Meta:
        db_table = 'huddle_audio_recording'
    
    def __str__(self):
        return f"Recording for {self.meeting.meeting_id} by {self.participant.session_id}"

class TranscriptionSegment(TimeStampedModel):
    recording = models.ForeignKey(AudioRecording, on_delete=models.CASCADE, related_name='segments')
    start_time = models.FloatField()
    end_time = models.FloatField()
    text = models.TextField()
    confidence = models.FloatField(null=True, blank=True)
    speaker_id = models.CharField(max_length=50, null=True, blank=True)
    speaker_name = models.CharField(max_length=100, null=True, blank=True, help_text="Identified speaker name")
    words = models.JSONField(default=list, blank=True, help_text="Word-level timing data")

    # Agenda context for this segment
    agenda_item = models.ForeignKey(
        'meetings.AgendaItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Agenda item that was active when this segment was recorded"
    )
    
    class Meta:
        db_table = 'huddle_transcription_segment'
        ordering = ['start_time']

class MeetingSummary(TimeStampedModel):
    """AI-generated meeting summary and insights"""
    meeting = models.OneToOneField(Meeting, on_delete=models.CASCADE, related_name='summary')

    # Transcript versions
    raw_transcript = models.TextField(blank=True, help_text="Original verbatim transcript from Deepgram")
    clean_transcript = models.TextField(blank=True, help_text="AI-cleaned and formatted transcript")

    # Meeting analysis
    executive_summary = models.TextField(blank=True, help_text="High-level meeting summary")
    key_points = models.JSONField(default=list, help_text="Key discussion points")
    action_items = models.JSONField(default=list, help_text="Action items with owners and due dates")
    decisions_made = models.JSONField(default=list, help_text="Decisions reached during the meeting")

    # Participants and engagement
    participants_summary = models.JSONField(default=dict, help_text="Speaking time and participation stats")
    sentiment_analysis = models.JSONField(default=dict, help_text="Overall meeting sentiment")

    # Processing status
    is_ai_processed = models.BooleanField(default=False, help_text="Whether AI cleanup and analysis is complete")
    ai_processing_started_at = models.DateTimeField(null=True, blank=True)
    ai_processing_completed_at = models.DateTimeField(null=True, blank=True)

    @property
    def full_transcript(self):
        """Backward compatibility - returns clean transcript if available, else raw"""
        return self.clean_transcript or self.raw_transcript
    
    class Meta:
        db_table = 'huddle_meeting_summary'