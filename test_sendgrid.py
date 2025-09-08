#!/usr/bin/env python
"""Test SendGrid email functionality"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.core.mail import send_mail
from django.conf import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_sendgrid():
    """Test SendGrid email sending"""
    
    # Check configuration
    print("\n=== SendGrid Configuration ===")
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"SENDGRID_API_KEY exists: {'Yes' if settings.SENDGRID_API_KEY else 'No'}")
    print(f"SENDGRID_FROM_EMAIL: {getattr(settings, 'SENDGRID_FROM_EMAIL', 'Not set')}")
    print(f"DEBUG mode: {settings.DEBUG}")
    
    if not settings.SENDGRID_API_KEY:
        print("\n❌ SENDGRID_API_KEY is not set in environment variables")
        return False
    
    # Test email
    test_email = input("\nEnter test email address to send to: ").strip()
    if not test_email:
        print("No email provided, exiting")
        return False
    
    print(f"\n=== Sending Test Email to {test_email} ===")
    
    try:
        result = send_mail(
            subject='Huddle Test Email - SendGrid',
            message='This is a test email from Huddle application using SendGrid.',
            from_email=getattr(settings, 'SENDGRID_FROM_EMAIL', 'noreply@huddle.spot'),
            recipient_list=[test_email],
            fail_silently=False,
        )
        
        if result > 0:
            print(f"✅ Email sent successfully! Check {test_email} inbox.")
            return True
        else:
            print("❌ Email sending failed - no emails were sent")
            return False
            
    except Exception as e:
        print(f"❌ Error sending email: {str(e)}")
        print(f"Exception type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    success = test_sendgrid()
    sys.exit(0 if success else 1)