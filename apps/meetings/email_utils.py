"""Email utilities for meeting invitations and voice setup"""
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from apps.meetings.voice_views import generate_setup_token
from .models import Meeting
import ssl
import logging
import traceback
import os

# Configure logging
logger = logging.getLogger(__name__)

def debug_email_config():
    """Log email configuration for debugging"""
    logger.info("=== EMAIL CONFIGURATION DEBUG ===")
    logger.info(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    logger.info(f"DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not set')}")
    logger.info(f"SENDGRID_API_KEY set: {'Yes' if os.getenv('SENDGRID_API_KEY') else 'No'}")
    if os.getenv('SENDGRID_API_KEY'):
        api_key = os.getenv('SENDGRID_API_KEY')
        logger.info(f"SENDGRID_API_KEY length: {len(api_key)} chars")
        logger.info(f"SENDGRID_API_KEY starts with: {api_key[:10]}...")
    logger.info(f"SITE_URL: {getattr(settings, 'SITE_URL', 'Not set')}")
    logger.info("=== END EMAIL CONFIG DEBUG ===")
    
    # Also print to console for immediate visibility
    print("📧 EMAIL DEBUG INFO:")
    print(f"   Backend: {settings.EMAIL_BACKEND}")
    print(f"   From: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not set')}")
    print(f"   SendGrid API Key set: {'Yes' if os.getenv('SENDGRID_API_KEY') else 'No'}")
    if os.getenv('SENDGRID_API_KEY'):
        api_key = os.getenv('SENDGRID_API_KEY')
        print(f"   API Key length: {len(api_key)} chars")

def send_voice_setup_invitation(meeting, email, host_name=None):
    """Send voice setup invitation email to a participant"""
    # Debug email configuration first
    debug_email_config()
    
    logger.info(f"=== SENDING VOICE SETUP INVITATION ===")
    logger.info(f"Meeting: {meeting.meeting_id} - {meeting.title}")
    logger.info(f"Recipient: {email}")
    logger.info(f"Host: {host_name}")
    
    print(f"🚀 SENDING EMAIL TO: {email}")
    print(f"   Meeting: {meeting.meeting_id} - {meeting.title}")
    
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
        
        # Log email details before sending
        logger.info(f"Email subject: {subject}")
        logger.info(f"From email: {settings.DEFAULT_FROM_EMAIL}")
        logger.info(f"To email: {email}")
        logger.info(f"Setup URL: {setup_url}")
        logger.info(f"Text message length: {len(text_message)} chars")
        logger.info(f"HTML message length: {len(html_message)} chars")
        
        print(f"📧 EMAIL DETAILS:")
        print(f"   Subject: {subject}")
        print(f"   From: {settings.DEFAULT_FROM_EMAIL}")
        print(f"   To: {email}")
        print(f"   Setup URL: {setup_url}")
        
        # Send email with detailed error handling
        print("📤 Attempting to send email...")
        logger.info("Attempting to send email via Django send_mail...")
        
        send_mail(
            subject=subject,
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False
        )
        
        logger.info("✅ Email sent successfully via Django send_mail")
        print("✅ Email sent successfully!")
        
        return True, f"Voice setup invitation sent to {email}"
        
    except Exception as e:
        error_msg = f"Failed to send invitation to {email}: {str(e)}"
        logger.error(f"❌ Email sending failed: {error_msg}")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        print(f"❌ EMAIL FAILED: {error_msg}")
        print(f"   Exception type: {type(e).__name__}")
        print(f"   Full error: {str(e)}")
        
        return False, error_msg

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