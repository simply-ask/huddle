"""Public views for viewing meeting content with access tokens (no login required)"""
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from .models import Meeting, MeetingAccessToken
from apps.audio.models import MeetingSummary


def verify_token_access(request, meeting_id):
    """Verify token and return meeting + token if valid"""
    token_string = request.GET.get('token')

    if not token_string:
        return None, None

    # Get meeting
    meeting = get_object_or_404(Meeting, meeting_id=meeting_id)

    # Verify token
    try:
        token = MeetingAccessToken.objects.get(
            token=token_string,
            meeting=meeting
        )

        if not token.is_valid():
            return None, None

        # Record access
        token.record_access()

        return meeting, token

    except MeetingAccessToken.DoesNotExist:
        return None, None


def public_meeting_minutes_view(request, meeting_id):
    """Public view for meeting minutes with token authentication"""
    meeting, token = verify_token_access(request, meeting_id)

    if not meeting or not token:
        return HttpResponseForbidden("Invalid or expired access token")

    if not token.can_view_minutes:
        return HttpResponseForbidden("You don't have permission to view minutes")

    # Get meeting summary if available
    try:
        summary = meeting.summary
        has_summary = True
        has_ai_processed = summary.is_ai_processed
    except MeetingSummary.DoesNotExist:
        summary = None
        has_summary = False
        has_ai_processed = False

    context = {
        'meeting': meeting,
        'summary': summary,
        'has_summary': has_summary,
        'has_ai_processed': has_ai_processed,
        'participant_email': token.email,
        'is_public_view': True,  # Flag for template to hide admin controls
    }

    return render(request, 'meetings/public_minutes.html', context)


def public_meeting_transcript_view(request, meeting_id):
    """Public view for meeting transcript with token authentication"""
    meeting, token = verify_token_access(request, meeting_id)

    if not meeting or not token:
        return HttpResponseForbidden("Invalid or expired access token")

    if not token.can_view_transcript:
        return HttpResponseForbidden("You don't have permission to view transcript")

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
                'agenda_item': segment.agenda_item.title if segment.agenda_item else None
            })

    # Sort all segments by start time
    all_segments.sort(key=lambda x: x['start_time'])

    # Group segments by speaker
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
        'all_segments': all_segments,
        'grouped_segments': grouped_segments,
        'total_segments': len(all_segments),
        'participant_email': token.email,
        'is_public_view': True,
        'processing_status': {
            'total_recordings': meeting.recordings.count(),
            'processed_recordings': meeting.recordings.filter(is_processed=True).count(),
        }
    }

    return render(request, 'meetings/public_transcript.html', context)


def public_meeting_actions_view(request, meeting_id):
    """Public view for meeting action items with token authentication"""
    meeting, token = verify_token_access(request, meeting_id)

    if not meeting or not token:
        return HttpResponseForbidden("Invalid or expired access token")

    if not token.can_view_action_items:
        return HttpResponseForbidden("You don't have permission to view action items")

    # Get meeting summary for action items
    try:
        summary = meeting.summary
        action_items = summary.action_items if summary.is_ai_processed else []

        # Filter action items for this participant
        participant_actions = []
        all_actions = []

        for item in action_items:
            all_actions.append(item)
            # Check if this action is assigned to the viewer
            if item.get('owner', '').lower() == token.email.lower():
                participant_actions.append(item)

    except MeetingSummary.DoesNotExist:
        participant_actions = []
        all_actions = []

    context = {
        'meeting': meeting,
        'participant_actions': participant_actions,
        'all_actions': all_actions,
        'participant_email': token.email,
        'is_public_view': True,
    }

    return render(request, 'meetings/public_actions.html', context)


def public_meeting_summary_view(request, meeting_id):
    """Combined summary view with minutes and actions"""
    meeting, token = verify_token_access(request, meeting_id)

    if not meeting or not token:
        return HttpResponseForbidden("Invalid or expired access token")

    # Redirect to minutes view as the main summary
    return public_meeting_minutes_view(request, meeting_id)