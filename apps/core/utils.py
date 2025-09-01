import secrets
import string
from django.conf import settings

def generate_meeting_id():
    """Generate a random meeting ID"""
    alphabet = string.ascii_lowercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(settings.MEETING_ID_LENGTH))

def get_user_organization(user):
    """Get user's organization name from simplyAsk UserProfile"""
    if not user.is_authenticated:
        return None
    
    try:
        # Import here to avoid circular imports
        from django.contrib.auth.models import User
        from django.apps import apps
        
        # Try to get UserProfile from simplyAsk core app
        if apps.is_installed('core'):
            UserProfile = apps.get_model('core', 'UserProfile')
            profile = UserProfile.objects.get(user=user)
            return profile.organisation_name
        
    except Exception as e:
        print(f"Could not get user organization: {e}")
        
    return None