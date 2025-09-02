"""Email utilities for meeting invitations and voice setup"""
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from apps.meetings.voice_views import generate_setup_token
from .models import Meeting

def send_voice_setup_invitation(meeting, email, host_name=None):
    """Send voice setup invitation email to a participant"""
    try:
        # Generate secure token
        token = generate_setup_token(meeting.meeting_id, email)
        
        # Generate voice setup URL
        setup_url = f"{settings.SITE_URL}/meet/{meeting.meeting_id}/voice-setup/?email={email}&token={token}"
        
        # Prepare context for email template
        context = {
            'meeting': meeting,
            'recipient_email': email,
            'recipient_name': Meeting.extract_name_from_email(email),
            'host_name': host_name or (meeting.host.get_full_name() if meeting.host else 'Meeting Host'),
            'setup_url': setup_url,
            'expires_days': 7,
            'site_name': 'Huddle',
        }
        
        # Render email content
        subject = f"Voice Setup Required - {meeting.title or 'Meeting'} ({meeting.meeting_id})"
        html_message = render_to_string('emails/voice_setup_invitation.html', context)
        text_message = render_to_string('emails/voice_setup_invitation.txt', context)
        
        # Send email
        send_mail(
            subject=subject,
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False
        )
        
        return True, f"Voice setup invitation sent to {email}"
        
    except Exception as e:
        return False, f"Failed to send invitation to {email}: {str(e)}"

def send_meeting_invitation(meeting, email_list, include_voice_setup=True):
    """Send meeting invitation with optional voice setup to multiple recipients"""
    results = []
    
    for email in email_list:
        if include_voice_setup:
            success, message = send_voice_setup_invitation(meeting, email)
        else:
            success, message = send_basic_meeting_invitation(meeting, email)
        
        results.append({
            'email': email,
            'success': success,
            'message': message
        })
    
    return results

def send_basic_meeting_invitation(meeting, email):
    """Send basic meeting invitation without voice setup"""
    try:
        # Generate meeting join URL
        meeting_url = f"{settings.SITE_URL}/meet/{meeting.meeting_id}/"
        
        context = {
            'meeting': meeting,
            'recipient_email': email,
            'recipient_name': Meeting.extract_name_from_email(email),
            'host_name': meeting.host.get_full_name() if meeting.host else 'Meeting Host',
            'meeting_url': meeting_url,
            'site_name': 'Huddle',
        }
        
        subject = f"Meeting Invitation - {meeting.title or 'Meeting'} ({meeting.meeting_id})"
        html_message = render_to_string('emails/meeting_invitation.html', context)
        text_message = render_to_string('emails/meeting_invitation.txt', context)
        
        send_mail(
            subject=subject,
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False
        )
        
        return True, f"Meeting invitation sent to {email}"
        
    except Exception as e:
        return False, f"Failed to send invitation to {email}: {str(e)}"

def send_meeting_reminder(meeting, email_list, hours_before=2):
    """Send meeting reminder emails"""
    results = []
    
    for email in email_list:
        try:
            context = {
                'meeting': meeting,
                'recipient_email': email,
                'recipient_name': Meeting.extract_name_from_email(email),
                'host_name': meeting.host.get_full_name() if meeting.host else 'Meeting Host',
                'meeting_url': f"{settings.SITE_URL}/meet/{meeting.meeting_id}/",
                'hours_before': hours_before,
                'site_name': 'Huddle',
            }
            
            subject = f"Meeting Reminder - {meeting.title or 'Meeting'} in {hours_before} hours"
            html_message = render_to_string('emails/meeting_reminder.html', context)
            text_message = render_to_string('emails/meeting_reminder.txt', context)
            
            send_mail(
                subject=subject,
                message=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                html_message=html_message,
                fail_silently=False
            )
            
            results.append({
                'email': email,
                'success': True,
                'message': f"Reminder sent to {email}"
            })
            
        except Exception as e:
            results.append({
                'email': email,
                'success': False,
                'message': f"Failed to send reminder to {email}: {str(e)}"
            })
    
    return results