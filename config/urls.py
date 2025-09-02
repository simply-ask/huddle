"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from apps.meetings import views as meeting_views
from apps.meetings import voice_views
import os

def home_view(request):
    return HttpResponse("""
    <h1>Huddle - Meeting Intelligence Platform</h1>
    <p>Welcome to Huddle!</p>
    <p>To join a meeting, go to: /meet/[meeting-id]/</p>
    <p>API endpoints available at: /api/</p>
    <p>Admin panel: /admin/</p>
    """)

def debug_view(request):
    """Debug endpoint to check configuration"""
    from django.conf import settings
    return JsonResponse({
        'debug': settings.DEBUG,
        'allowed_hosts': settings.ALLOWED_HOSTS,
        'db_host': 'configured' if os.environ.get('DB_HOST') else 'not configured',
        'db_name': 'configured' if os.environ.get('DB_NAME') else 'not configured',
        'static_url': settings.STATIC_URL,
        'csrf_cookie_secure': settings.CSRF_COOKIE_SECURE,
        'session_cookie_secure': settings.SESSION_COOKIE_SECURE,
        'request_is_secure': request.is_secure(),
        'host': request.get_host(),
        'scheme': request.scheme,
        'meta_http_host': request.META.get('HTTP_HOST'),
        'meta_server_name': request.META.get('SERVER_NAME'),
        'meta_forwarded_proto': request.META.get('HTTP_X_FORWARDED_PROTO'),
    })

@csrf_exempt  
def test_login(request):
    """Test login without CSRF to debug the issue"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return JsonResponse({'success': True, 'message': 'Login successful'})
        else:
            return JsonResponse({'success': False, 'message': 'Invalid credentials'})
    
    return HttpResponse("""
    <h2>Test Login (No CSRF)</h2>
    <form method="post">
        <p>Username: <input type="text" name="username"></p>
        <p>Password: <input type="password" name="password"></p>
        <input type="submit" value="Login">
    </form>
    """)

def db_test(request):
    """Test database connection"""
    try:
        from django.db import connection
        from django.contrib.auth.models import User
        
        # Test basic connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_result = cursor.fetchone()
        
        # Test user query
        user_count = User.objects.count()
        
        return JsonResponse({
            'success': True,
            'message': 'Database connection successful',
            'test_query': db_result[0],
            'user_count': user_count,
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__,
        })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apps.api.urls')),
    path('meet/<str:meeting_id>/', meeting_views.join_meeting, name='join_meeting'),
    path('meet/<str:meeting_id>/room/', meeting_views.meeting_room, name='meeting_room'),
    path('meet/<str:meeting_id>/voice-setup/', voice_views.voice_setup_view, name='voice_setup'),
    path('meet/<str:meeting_id>/voice-setup-process/', voice_views.process_voice_setup, name='process_voice_setup'),
    path('meet/<str:meeting_id>/voice-setup-complete/', voice_views.voice_setup_view, name='voice_setup_complete'),
    path('api/meeting/<str:meeting_id>/speakers/', voice_views.meeting_speaker_status, name='meeting_speaker_status'),
    path('', home_view, name='home'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

