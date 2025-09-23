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
    """Handle audio file uploads from PWA clients - Admin/Host only"""
    print(f"🎵 Audio upload request received: {request.method}")
    print(f"🎵 Request data keys: {list(request.data.keys())}")
    print(f"🎵 Request files: {list(request.FILES.keys())}")

    try:
        meeting_id = request.data.get('meeting_id')
        session_id = request.data.get('session_id')
        audio_file = request.FILES.get('audio_file')

        print(f"🎵 Parsed data - meeting_id: {meeting_id}, session_id: {session_id}, audio_file: {audio_file}")

        if not all([meeting_id, session_id, audio_file]):
            print(f"🎵 Missing fields error!")
            return Response(
                {'error': 'Missing required fields'},
                status=status.HTTP_400_BAD_REQUEST
            )

        print(f"🎵 Looking for meeting: {meeting_id}")
        meeting = get_object_or_404(Meeting, meeting_id=meeting_id)
        print(f"🎵 Found meeting: {meeting}")

        print(f"🎵 Looking for participant with session_id: {session_id}")
        participant = meeting.participants.filter(session_id=session_id).first()
        print(f"🎵 Found participant: {participant}")

        # If no participant found, create one for the authenticated user
        if not participant and request.user.is_authenticated:
            print(f"🎵 Creating participant for authenticated user: {request.user}")
            from apps.meetings.models import MeetingParticipant
            participant = MeetingParticipant.objects.create(
                meeting=meeting,
                user=request.user,
                session_id=session_id,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                is_recording=False,
            )
            print(f"🎵 Created participant: {participant}")

        if not participant:
            print(f"🎵 No participant after creation attempt!")
            return Response(
                {'error': 'Participant not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # ADMIN-ONLY RECORDING: Only the meeting host can upload recordings
        if not participant.user or participant.user != meeting.host:
            return Response(
                {'error': 'Only the meeting admin can record'},
                status=status.HTTP_403_FORBIDDEN
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