from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import Meeting

def join_meeting(request, meeting_id):
    """Redirect to meeting room - Toaster UI simplicity"""
    meeting = get_object_or_404(Meeting, meeting_id=meeting_id, status=Meeting.Status.ACTIVE)
    return redirect('meeting_room', meeting_id=meeting_id)

def meeting_room(request, meeting_id):
    """Main meeting room interface"""
    meeting = get_object_or_404(Meeting, meeting_id=meeting_id, status=Meeting.Status.ACTIVE)
    return render(request, 'meeting/room.html', {'meeting': meeting})