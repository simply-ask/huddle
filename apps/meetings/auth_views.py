"""Authentication and dashboard views for meeting management"""
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import Meeting
from apps.core.models import SpeakerProfile

def login_view(request):
    """Modern login page for admins"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'auth/login.html')

def logout_view(request):
    """Logout user and redirect to login"""
    logout(request)
    messages.info(request, 'You have been logged out successfully')
    return redirect('login')

@login_required
def dashboard_view(request):
    """Main dashboard for meeting management"""
    # Get user's meetings
    meetings = Meeting.objects.filter(host=request.user).order_by('-created_at')
    
    # Statistics
    total_meetings = meetings.count()
    active_meetings = meetings.filter(status=Meeting.Status.ACTIVE).count()
    recent_meetings = meetings[:5]
    
    # Speaker statistics
    total_speakers = SpeakerProfile.objects.filter(organization=request.user).count()
    speakers_with_voice = SpeakerProfile.objects.filter(
        organization=request.user,
        sample_audio__isnull=False
    ).count()
    
    # Upcoming meetings (if started_at is used for scheduling)
    upcoming = meetings.filter(
        started_at__gte=timezone.now(),
        status=Meeting.Status.ACTIVE
    ).order_by('started_at')[:5]
    
    context = {
        'total_meetings': total_meetings,
        'active_meetings': active_meetings,
        'recent_meetings': recent_meetings,
        'total_speakers': total_speakers,
        'speakers_with_voice': speakers_with_voice,
        'upcoming_meetings': upcoming,
    }
    
    return render(request, 'dashboard/home.html', context)

@login_required
def meetings_list_view(request):
    """List all meetings with search and filter"""
    meetings = Meeting.objects.filter(host=request.user)
    
    # Search
    search = request.GET.get('search', '')
    if search:
        meetings = meetings.filter(
            Q(title__icontains=search) |
            Q(meeting_id__icontains=search)
        )
    
    # Filter by status
    status = request.GET.get('status', '')
    if status == 'active':
        meetings = meetings.filter(status=Meeting.Status.ACTIVE)
    elif status == 'inactive':
        meetings = meetings.filter(status=Meeting.Status.COMPLETED)
    
    meetings = meetings.order_by('-created_at')
    
    # Add speaker counts
    meetings = meetings.annotate(
        speaker_count=Count('known_speakers')
    )
    
    context = {
        'meetings': meetings,
        'search': search,
        'status': status,
    }
    
    return render(request, 'dashboard/meetings_list.html', context)

@login_required
def speakers_view(request):
    """View all speaker profiles"""
    speakers = SpeakerProfile.objects.filter(
        organization=request.user,
        status=Meeting.Status.ACTIVE  # Only show active profiles
    ).order_by('-created_at')
    
    # Search
    search = request.GET.get('search', '')
    if search:
        speakers = speakers.filter(
            Q(full_name__icontains=search) |
            Q(email__icontains=search) |
            Q(job_title__icontains=search)
        )
    
    context = {
        'speakers': speakers,
        'search': search,
    }
    
    return render(request, 'dashboard/speakers.html', context)