from rest_framework import serializers
from apps.meetings.models import Meeting, MeetingParticipant
from apps.audio.models import AudioRecording, TranscriptionSegment

class MeetingSerializer(serializers.ModelSerializer):
    participant_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Meeting
        fields = [
            'meeting_id', 'title', 'is_active', 'started_at', 
            'ended_at', 'created_at', 'participant_count'
        ]
        read_only_fields = ['meeting_id', 'created_at']
    
    def get_participant_count(self, obj):
        return obj.participants.count()

class MeetingParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeetingParticipant
        fields = [
            'session_id', 'is_recording', 'audio_quality_score', 
            'last_seen', 'created_at'
        ]

class TranscriptionSegmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TranscriptionSegment
        fields = [
            'start_time', 'end_time', 'text', 'confidence', 
            'speaker_id', 'created_at'
        ]

class AudioRecordingSerializer(serializers.ModelSerializer):
    segments = TranscriptionSegmentSerializer(many=True, read_only=True)
    participant = MeetingParticipantSerializer(read_only=True)
    
    class Meta:
        model = AudioRecording
        fields = [
            'id', 'duration_seconds', 'file_size', 'format', 
            'is_processed', 'created_at', 'participant', 'segments'
        ]