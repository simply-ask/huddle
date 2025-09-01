from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Meeting

def join_meeting(request, meeting_id):
    """PWA meeting room view"""
    meeting = get_object_or_404(Meeting, meeting_id=meeting_id, is_active=True)
    return render(request, 'meeting/join.html', {'meeting': meeting})

def meeting_room(request, meeting_id):
    """Main meeting room interface"""
    meeting = get_object_or_404(Meeting, meeting_id=meeting_id, is_active=True)
    return render(request, 'meeting/room.html', {'meeting': meeting})