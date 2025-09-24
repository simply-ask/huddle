"""Views for displaying meeting transcripts with speaker identification"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Meeting
from apps.audio.models import MeetingSummary, TranscriptionSegment


@login_required
def meeting_transcript_view(request, meeting_id):
    """Display meeting transcript with speaker identification"""
    meeting = get_object_or_404(Meeting, meeting_id=meeting_id, host=request.user)
    
    # Get meeting summary if available
    try:
        summary = meeting.summary
        has_summary = True
        has_ai_processed = summary.is_ai_processed
    except MeetingSummary.DoesNotExist:
        summary = None
        has_summary = False
        has_ai_processed = False
    
    # Get all transcript segments from all recordings
    all_segments = []
    for recording in meeting.recordings.filter(is_processed=True):
        segments = recording.segments.all().order_by('start_time')
        for segment in segments:
            all_segments.append({
                'start_time': segment.start_time,
                'end_time': segment.end_time,
                'speaker_name': segment.speaker_name or 'Unknown Speaker',
                'speaker_id': segment.speaker_id,
                'text': segment.text,
                'confidence': segment.confidence,
                'recording_service': recording.transcription_service,
            })
    
    # Sort all segments by start time
    all_segments.sort(key=lambda x: x['start_time'])
    
    # Group segments by speaker for better display
    grouped_segments = []
    current_speaker = None
    current_group = []
    
    for segment in all_segments:
        if segment['speaker_name'] != current_speaker:
            if current_group:
                grouped_segments.append({
                    'speaker': current_speaker,
                    'segments': current_group
                })
            current_speaker = segment['speaker_name']
            current_group = [segment]
        else:
            current_group.append(segment)
    
    if current_group:
        grouped_segments.append({
            'speaker': current_speaker,
            'segments': current_group
        })
    
    context = {
        'meeting': meeting,
        'summary': summary,
        'has_summary': has_summary,
        'has_ai_processed': has_ai_processed,
        'all_segments': all_segments,
        'grouped_segments': grouped_segments,
        'total_segments': len(all_segments),
        'processing_status': {
            'total_recordings': meeting.recordings.count(),
            'processed_recordings': meeting.recordings.filter(is_processed=True).count(),
            'ai_processing_complete': has_ai_processed,
        }
    }
    
    return render(request, 'meetings/transcript.html', context)


@login_required
def meeting_transcript_api(request, meeting_id):
    """API endpoint for getting meeting transcript data"""
    meeting = get_object_or_404(Meeting, meeting_id=meeting_id, host=request.user)
    
    # Get all transcript segments
    all_segments = []
    for recording in meeting.recordings.filter(is_processed=True):
        segments = recording.segments.all().order_by('start_time')
        for segment in segments:
            all_segments.append({
                'start_time': segment.start_time,
                'end_time': segment.end_time,
                'speaker_name': segment.speaker_name,
                'speaker_id': segment.speaker_id,
                'text': segment.text,
                'confidence': segment.confidence,
                'service': recording.transcription_service,
            })
    
    # Sort by start time
    all_segments.sort(key=lambda x: x['start_time'])
    
    # Get summary if available
    summary_data = None
    if hasattr(meeting, 'summary'):
        summary_data = {
            'full_transcript': meeting.summary.full_transcript,
            'summary': meeting.summary.summary,
            'key_points': meeting.summary.key_points,
            'action_items': meeting.summary.action_items,
        }
    
    return JsonResponse({
        'meeting_id': meeting.meeting_id,
        'meeting_title': meeting.title,
        'segments': all_segments,
        'summary': summary_data,
        'processing_status': {
            'total_recordings': meeting.recordings.count(),
            'processed_recordings': meeting.recordings.filter(is_processed=True).count(),
            'is_complete': meeting.recordings.filter(is_processed=True).count() == meeting.recordings.count()
        }
    })


def format_timestamp(seconds):
    """Format timestamp for display"""
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"