"""Meeting management views for creating and editing meetings"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
import json
from .models import Meeting
from .email_utils import send_voice_setup_invitation, send_meeting_invitation
from apps.core.models import SpeakerProfile

@login_required
def create_meeting_view(request):
    """Create a new meeting"""
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        attendees = request.POST.get('attendees', '').strip()
        send_invites = request.POST.get('send_invites') == 'on'
        
        # Parse attendee emails (comma or newline separated)
        attendee_list = []
        if attendees:
            # Split by comma or newline
            raw_emails = attendees.replace('\n', ',').replace('\r', ',').split(',')
            attendee_list = [email.strip().lower() for email in raw_emails if email.strip()]
        
        # Validate emails
        import re
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        invalid_emails = [email for email in attendee_list if not email_pattern.match(email)]
        
        if invalid_emails:
            messages.error(request, f'Invalid email addresses: {", ".join(invalid_emails)}')
            return render(request, 'dashboard/create_meeting.html', {
                'title': title,
                'attendees': attendees,
            })
        
        # Create meeting
        meeting = Meeting.objects.create(
            title=title,
            host=request.user,
            organization_name=request.user.get_full_name() or request.user.username,
            expected_speakers=attendee_list
        )
        
        # Check for existing speaker profiles
        existing_profiles = SpeakerProfile.objects.filter(
            organization=request.user,
            email__in=attendee_list
        )
        meeting.known_speakers.set(existing_profiles)
        
        messages.success(request, f'Meeting "{meeting.title}" created successfully! Meeting ID: {meeting.meeting_id}')
        
        # Send invitations if requested
        if send_invites and attendee_list:
            sent_count = 0
            failed_count = 0
            
            for email in attendee_list:
                success, message = send_voice_setup_invitation(meeting, email)
                if success:
                    sent_count += 1
                else:
                    failed_count += 1
            
            if sent_count > 0:
                messages.success(request, f'Voice setup invitations sent to {sent_count} attendees')
            if failed_count > 0:
                messages.warning(request, f'Failed to send {failed_count} invitations')
        
        return redirect('meeting_detail', meeting_id=meeting.meeting_id)
    
    # Get suggested attendees from existing speakers
    suggested_speakers = SpeakerProfile.objects.filter(
        organization=request.user,
        is_active=True
    ).values('email', 'full_name', 'job_title')[:10]
    
    return render(request, 'dashboard/create_meeting.html', {
        'suggested_speakers': list(suggested_speakers)
    })

@login_required
def meeting_detail_view(request, meeting_id):
    """View meeting details and manage attendees"""
    meeting = get_object_or_404(Meeting, meeting_id=meeting_id, host=request.user)
    
    # Get speaker status
    known_speakers = meeting.known_speakers.all()
    known_emails = set(known_speakers.values_list('email', flat=True))
    
    attendee_status = []
    for email in meeting.expected_speakers:
        speaker = known_speakers.filter(email=email).first()
        attendee_status.append({
            'email': email,
            'name': speaker.full_name if speaker else Meeting.extract_name_from_email(email),
            'has_profile': email in known_emails,
            'has_voice': speaker.sample_audio.name if speaker else None,
            'job_title': speaker.job_title if speaker else '',
        })
    
    context = {
        'meeting': meeting,
        'attendee_status': attendee_status,
        'meeting_url': request.build_absolute_uri(f'/meet/{meeting.meeting_id}/'),
    }
    
    return render(request, 'dashboard/meeting_detail.html', context)

@login_required
@require_http_methods(['POST'])
def add_attendees_view(request, meeting_id):
    """Add attendees to existing meeting"""
    meeting = get_object_or_404(Meeting, meeting_id=meeting_id, host=request.user)
    
    try:
        data = json.loads(request.body)
        new_emails = data.get('emails', [])
        send_invites = data.get('send_invites', False)
        
        # Validate and add new emails
        import re
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        
        added_emails = []
        for email in new_emails:
            email = email.strip().lower()
            if email and email_pattern.match(email) and email not in meeting.expected_speakers:
                meeting.expected_speakers.append(email)
                added_emails.append(email)
        
        if added_emails:
            meeting.save()
            
            # Check for existing profiles
            existing_profiles = SpeakerProfile.objects.filter(
                organization=request.user,
                email__in=added_emails
            )
            for profile in existing_profiles:
                meeting.known_speakers.add(profile)
            
            # Send invitations if requested
            if send_invites:
                for email in added_emails:
                    send_voice_setup_invitation(meeting, email)
            
            return JsonResponse({
                'success': True,
                'added': added_emails,
                'message': f'Added {len(added_emails)} attendees'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'No valid new emails to add'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@login_required
@require_http_methods(['POST'])
def remove_attendee_view(request, meeting_id):
    """Remove attendee from meeting"""
    meeting = get_object_or_404(Meeting, meeting_id=meeting_id, host=request.user)
    
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip().lower()
        
        if email in meeting.expected_speakers:
            meeting.expected_speakers.remove(email)
            meeting.save()
            
            # Remove from known speakers if exists
            speaker = meeting.known_speakers.filter(email=email).first()
            if speaker:
                meeting.known_speakers.remove(speaker)
            
            return JsonResponse({
                'success': True,
                'message': f'Removed {email} from meeting'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Email not found in attendee list'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@login_required
@require_http_methods(['POST'])
def send_invitations_view(request, meeting_id):
    """Send voice setup invitations to attendees"""
    meeting = get_object_or_404(Meeting, meeting_id=meeting_id, host=request.user)
    
    try:
        data = json.loads(request.body)
        emails = data.get('emails', [])
        
        if not emails:
            # Send to all attendees who don't have voice profiles
            new_speakers = meeting.get_new_speakers()
            emails = [s['email'] for s in new_speakers]
        
        results = []
        for email in emails:
            if email in meeting.expected_speakers:
                success, message = send_voice_setup_invitation(meeting, email)
                results.append({
                    'email': email,
                    'success': success,
                    'message': message
                })
        
        sent_count = sum(1 for r in results if r['success'])
        
        return JsonResponse({
            'success': True,
            'sent': sent_count,
            'total': len(results),
            'results': results
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@login_required
def delete_meeting_view(request, meeting_id):
    """Delete a meeting"""
    meeting = get_object_or_404(Meeting, meeting_id=meeting_id, host=request.user)
    
    if request.method == 'POST':
        title = meeting.title
        meeting.delete()
        messages.success(request, f'Meeting "{title}" has been deleted')
        return redirect('meetings_list')
    
    return render(request, 'dashboard/delete_meeting.html', {'meeting': meeting})