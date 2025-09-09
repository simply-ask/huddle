"""Voice setup and speaker identification views"""
import secrets
import hashlib
from datetime import datetime, timedelta
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.base import ContentFile
from django.utils import timezone
from apps.core.models import SpeakerProfile, VoiceSetupToken
from .models import Meeting
import json

def generate_setup_token(meeting_id, email):
    """Generate secure token for voice setup"""
    token = secrets.token_urlsafe(48)
    expires_at = timezone.now() + timedelta(days=7)  # 7-day expiry
    
    VoiceSetupToken.objects.create(
        meeting_id=meeting_id,
        email=email,
        token=token,
        expires_at=expires_at
    )
    
    return token

def verify_setup_token(meeting_id, email, token):
    """Verify voice setup token"""
    try:
        token_obj = VoiceSetupToken.objects.get(
            meeting_id=meeting_id,
            email=email,
            token=token,
            used=False,
            expires_at__gt=timezone.now()
        )
        return True
    except VoiceSetupToken.DoesNotExist:
        return False

def voice_setup_view(request, meeting_id):
    """Pre-meeting voice setup page"""
    meeting = get_object_or_404(Meeting, meeting_id=meeting_id, is_active=True)
    email = request.GET.get('email')
    token = request.GET.get('token')
    
    # Verify required parameters
    if not email or not token:
        return render(request, 'voice_setup_error.html', {
            'error': 'Invalid setup link. Please check your email invitation.'
        })
    
    # Verify token
    if not verify_setup_token(meeting_id, email, token):
        return render(request, 'voice_setup_error.html', {
            'error': 'This setup link has expired or been used. Please contact the meeting host.'
        })
    
    # Check if profile already exists
    try:
        speaker_profile = SpeakerProfile.objects.get(
            organization=meeting.host,
            email=email
        )
        return render(request, 'voice_setup_complete.html', {
            'meeting': meeting,
            'speaker': speaker_profile
        })
    except SpeakerProfile.DoesNotExist:
        pass
    
    return render(request, 'voice_setup.html', {
        'meeting': meeting,
        'email': email,
        'suggested_name': Meeting.extract_name_from_email(email),
        'token': token
    })

@csrf_exempt
@require_http_methods(["POST"])
def process_voice_setup(request, meeting_id):
    """Process voice setup form submission"""
    meeting = get_object_or_404(Meeting, meeting_id=meeting_id, is_active=True)
    
    try:
        email = request.POST.get('email')
        token = request.POST.get('token')
        full_name = request.POST.get('full_name', '').strip()
        job_title = request.POST.get('job_title', '').strip()
        audio_file = request.FILES.get('voice_sample')
        
        # Verify token
        if not verify_setup_token(meeting_id, email, token):
            return JsonResponse({'error': 'Invalid or expired token'}, status=400)
        
        # Validate inputs
        if not full_name or not audio_file:
            return JsonResponse({'error': 'Name and voice sample are required'}, status=400)
        
        # Check if profile already exists
        speaker_profile, created = SpeakerProfile.objects.get_or_create(
            organization=meeting.host,
            email=email,
            defaults={
                'full_name': full_name,
                'job_title': job_title,
            }
        )
        
        if not created:
            # Update existing profile
            speaker_profile.full_name = full_name
            speaker_profile.job_title = job_title
        
        # Process and save audio file
        audio_filename = f"voice_sample_{speaker_profile.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.webm"
        speaker_profile.sample_audio.save(
            audio_filename,
            ContentFile(audio_file.read()),
            save=False
        )
        
        # Process voice characteristics (placeholder for now)
        voice_features = analyze_voice_sample(audio_file)
        speaker_profile.voice_signature = voice_features
        speaker_profile.save()
        
        # Add to meeting's known speakers
        meeting.known_speakers.add(speaker_profile)
        
        # Mark token as used
        VoiceSetupToken.objects.filter(
            meeting_id=meeting_id,
            email=email,
            token=token
        ).update(used=True)
        
        return JsonResponse({
            'success': True,
            'speaker_id': speaker_profile.id,
            'message': 'Voice profile created successfully!'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def voice_setup_complete_view(request, meeting_id):
    """Voice setup completion page"""
    meeting = get_object_or_404(Meeting, meeting_id=meeting_id, is_active=True)
    email = request.GET.get('email')
    
    # Try to find the speaker profile
    try:
        speaker_profile = SpeakerProfile.objects.get(
            organization=meeting.host,
            email=email
        )
        return render(request, 'voice_setup_complete.html', {
            'meeting': meeting,
            'speaker': speaker_profile
        })
    except SpeakerProfile.DoesNotExist:
        return render(request, 'voice_setup_error.html', {
            'error': 'Voice setup not found. Please try the setup process again.'
        })

def analyze_voice_sample(audio_file):
    """Analyze voice sample and extract features (placeholder implementation)"""
    # This would integrate with actual voice analysis library
    # For now, return basic metadata
    return {
        'file_size': audio_file.size,
        'processed_at': timezone.now().isoformat(),
        'version': '1.0',
        # Placeholder for actual voice features:
        # 'pitch_average': 150.5,
        # 'speech_rate': 180,  # words per minute
        # 'vocal_signature': [...],  # MFCC coefficients
    }

def meeting_speaker_status(request, meeting_id):
    """API endpoint to get speaker setup status for a meeting"""
    meeting = get_object_or_404(Meeting, meeting_id=meeting_id, is_active=True)
    
    known_speakers = []
    for speaker in meeting.known_speakers.all():
        known_speakers.append({
            'name': speaker.full_name,
            'email': speaker.email,
            'job_title': speaker.job_title,
            'meetings_count': speaker.meetings_count,
            'accuracy_score': round(speaker.accuracy_score, 1),
            'has_voice_sample': bool(speaker.sample_audio)
        })
    
    new_speakers = meeting.get_new_speakers()
    
    return JsonResponse({
        'meeting_id': meeting.meeting_id,
        'title': meeting.title,
        'host': meeting.host.get_full_name() if meeting.host else 'Host',
        'known_speakers': known_speakers,
        'new_speakers': new_speakers,
        'total_expected': len(meeting.expected_speakers)
    })