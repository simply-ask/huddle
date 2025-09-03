#!/usr/bin/env python3
"""
Quick SendGrid test script
Run with: python test_sendgrid.py
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ['FORCE_SENDGRID_EMAIL'] = '1'  # Force SendGrid usage
django.setup()

from apps.meetings.email_utils import debug_email_config, send_voice_setup_invitation
from apps.meetings.models import Meeting

def test_sendgrid():
    print("🧪 SENDGRID TEST SCRIPT")
    print("=" * 50)
    
    # Debug current configuration
    debug_email_config()
    print()
    
    # Check if we have SendGrid API key
    api_key = os.getenv('SENDGRID_API_KEY')
    if not api_key:
        print("❌ SENDGRID_API_KEY not found in environment")
        print("Please set SENDGRID_API_KEY environment variable")
        return False
    
    print(f"✅ SendGrid API Key found (length: {len(api_key)} chars)")
    print(f"   Starts with: {api_key[:10]}...")
    print()
    
    # Find a test meeting
    meetings = Meeting.objects.all()
    if not meetings.exists():
        print("❌ No meetings found in database")
        print("Please create a meeting first or run: python manage.py shell")
        return False
    
    meeting = meetings.first()
    print(f"✅ Using test meeting: {meeting.meeting_id} - {meeting.title}")
    print()
    
    # Attempt to send test email
    test_email = "mitchel@simplyask.io"  # Your verified email
    print(f"📧 Sending test email to: {test_email}")
    print("   (This should be a verified sender in your SendGrid account)")
    print()
    
    try:
        success, message = send_voice_setup_invitation(
            meeting=meeting,
            email=test_email,
            host_name="SendGrid Test"
        )
        
        print("=" * 50)
        if success:
            print("✅ EMAIL SENT SUCCESSFULLY!")
            print(f"   Message: {message}")
            print("\n🎉 SendGrid integration is working!")
            print(f"   Check your inbox at {test_email}")
        else:
            print("❌ EMAIL FAILED TO SEND")
            print(f"   Error: {message}")
            print("\n🔍 Possible issues:")
            print("   1. SendGrid API key invalid")
            print("   2. Sender email not verified in SendGrid")
            print("   3. Domain authentication incomplete")
            
        return success
        
    except Exception as e:
        print(f"❌ EXCEPTION OCCURRED: {str(e)}")
        print(f"   Type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    test_sendgrid()