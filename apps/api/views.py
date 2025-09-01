from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from apps.meetings.models import Meeting
from apps.audio.models import AudioRecording
from apps.audio.tasks import process_audio_recording
from .serializers import MeetingSerializer, AudioRecordingSerializer

class MeetingViewSet(viewsets.ModelViewSet):
    queryset = Meeting.objects.all()
    serializer_class = MeetingSerializer
    lookup_field = 'meeting_id'
    permission_classes = [AllowAny]

class AudioRecordingViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AudioRecording.objects.all()
    serializer_class = AudioRecordingSerializer
    permission_classes = [AllowAny]

@api_view(['POST'])
@permission_classes([AllowAny])
def upload_audio(request):
    """Handle audio file uploads from PWA clients"""
    try:
        meeting_id = request.data.get('meeting_id')
        session_id = request.data.get('session_id')
        audio_file = request.FILES.get('audio_file')
        
        if not all([meeting_id, session_id, audio_file]):
            return Response(
                {'error': 'Missing required fields'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        meeting = get_object_or_404(Meeting, meeting_id=meeting_id)
        participant = meeting.participants.filter(session_id=session_id).first()
        
        if not participant:
            return Response(
                {'error': 'Participant not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Create audio recording
        recording = AudioRecording.objects.create(
            meeting=meeting,
            participant=participant,
            audio_file=audio_file,
            format=audio_file.name.split('.')[-1].lower(),
            file_size=audio_file.size
        )
        
        # Queue for background processing
        process_audio_recording.delay(recording.id)
        
        return Response({
            'recording_id': recording.id,
            'status': 'uploaded',
            'queued_for_processing': True
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def meeting_status(request, meeting_id):
    """Get current meeting status and participants"""
    meeting = get_object_or_404(Meeting, meeting_id=meeting_id)
    
    participants = meeting.participants.all()
    
    return Response({
        'meeting_id': meeting.meeting_id,
        'is_active': meeting.is_active,
        'participant_count': participants.count(),
        'recording_participants': participants.filter(is_recording=True).count(),
        'participants': [
            {
                'session_id': p.session_id,
                'is_recording': p.is_recording,
                'last_seen': p.last_seen,
                'audio_quality_score': p.audio_quality_score
            }
            for p in participants
        ]
    })