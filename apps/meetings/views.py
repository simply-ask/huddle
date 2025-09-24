from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import Meeting

def join_meeting(request, meeting_id):
    """Redirect to meeting room - Toaster UI simplicity"""
    # Allow joining scheduled or active meetings
    meeting = get_object_or_404(Meeting, meeting_id=meeting_id)

    # Don't allow joining completed meetings
    if meeting.status == Meeting.Status.COMPLETED:
        return render(request, 'meeting/meeting_ended.html', {'meeting': meeting})

    # Auto-start scheduled meetings when someone joins
    if meeting.status == Meeting.Status.SCHEDULED:
        meeting.start_meeting()

    return redirect('meeting_room', meeting_id=meeting_id)

def meeting_room(request, meeting_id):
    """Main meeting room interface"""
    # Allow access to scheduled or active meetings
    meeting = get_object_or_404(Meeting, meeting_id=meeting_id)

    # Don't allow joining completed meetings
    if meeting.status == Meeting.Status.COMPLETED:
        return render(request, 'meeting/meeting_ended.html', {'meeting': meeting})

    # Auto-start scheduled meetings when someone joins
    if meeting.status == Meeting.Status.SCHEDULED:
        meeting.start_meeting()

    return render(request, 'meeting/room.html', {'meeting': meeting})