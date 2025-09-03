"""Debug views for troubleshooting email issues"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.admin.views.decorators import staff_member_required
from .models import Meeting
from .email_utils import send_voice_setup_invitation, debug_email_config
import json
import traceback
import os
from django.conf import settings
from django.utils import timezone

@staff_member_required
def email_debug_info(request):
    """Debug endpoint to show email configuration"""
    try:
        # Get email configuration
        config = {
            'backend': settings.EMAIL_BACKEND,
            'host': getattr(settings, 'EMAIL_HOST', 'Not set'),
            'port': getattr(settings, 'EMAIL_PORT', 'Not set'),
            'use_ssl': getattr(settings, 'EMAIL_USE_SSL', 'Not set'),
            'use_tls': getattr(settings, 'EMAIL_USE_TLS', 'Not set'),
            'host_user': getattr(settings, 'EMAIL_HOST_USER', 'Not set'),
            'default_from_email': getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not set'),
            'password_set': bool(os.getenv('DO_EMAIL_PASSWORD')),
            'password_length': len(os.getenv('DO_EMAIL_PASSWORD', '')),
            'site_url': getattr(settings, 'SITE_URL', 'Not set'),
            'debug_mode': settings.DEBUG,
        }
        
        # Get environment info
        env_info = {
            'django_env': os.getenv('DJANGO_ENV', 'Not set'),
            'python_version': f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
        }
        
        # Test database connection
        try:
            meeting_count = Meeting.objects.count()
            db_status = f"✅ Connected - {meeting_count} meetings"
        except Exception as e:
            db_status = f"❌ Error: {str(e)}"
        
        return JsonResponse({
            'status': 'success',
            'email_config': config,
            'environment': env_info,
            'database': db_status,
            'timestamp': str(timezone.now())
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@staff_member_required
def test_email_send(request):
    """Debug endpoint to test email sending"""
    try:
        data = json.loads(request.body)
        test_email = data.get('email')
        meeting_id = data.get('meeting_id')
        
        if not test_email:
            return JsonResponse({
                'status': 'error',
                'error': 'Email address required'
            }, status=400)
        
        # Get or create test meeting
        if meeting_id:
            try:
                meeting = Meeting.objects.get(meeting_id=meeting_id)
            except Meeting.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'error': f'Meeting {meeting_id} not found'
                }, status=404)
        else:
            # Use first available meeting or create a test one
            meeting = Meeting.objects.first()
            if not meeting:
                return JsonResponse({
                    'status': 'error',
                    'error': 'No meetings available for testing'
                }, status=400)
        
        # Debug email configuration
        debug_email_config()
        
        # Attempt to send email
        success, message = send_voice_setup_invitation(
            meeting=meeting,
            email=test_email,
            host_name="Debug Test"
        )
        
        return JsonResponse({
            'status': 'success' if success else 'error',
            'message': message,
            'meeting_id': meeting.meeting_id,
            'meeting_title': meeting.title,
            'test_email': test_email,
            'email_backend': settings.EMAIL_BACKEND,
            'timestamp': str(timezone.now())
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)

@staff_member_required  
def email_test_page(request):
    """Simple HTML page for testing emails"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Email Debug - Huddle</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; max-width: 800px; margin: 0 auto; }
            .section { background: #f5f5f5; padding: 20px; margin: 20px 0; border-radius: 8px; }
            button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
            input[type="email"] { padding: 8px; width: 300px; margin: 10px; }
            .result { margin: 20px 0; padding: 15px; border-radius: 4px; }
            .success { background: #d4edda; color: #155724; }
            .error { background: #f8d7da; color: #721c24; }
            pre { background: #f8f9fa; padding: 15px; border-radius: 4px; overflow-x: auto; }
        </style>
    </head>
    <body>
        <h1>📧 Huddle Email Debug</h1>
        
        <div class="section">
            <h2>Email Configuration</h2>
            <button onclick="checkConfig()">Check Email Config</button>
            <div id="configResult"></div>
        </div>
        
        <div class="section">
            <h2>Test Email Sending</h2>
            <input type="email" id="testEmail" placeholder="Enter email address to test" value="mitchel@simplyask.io">
            <button onclick="sendTestEmail()">Send Test Email</button>
            <div id="emailResult"></div>
        </div>
        
        <script>
        async function checkConfig() {
            const result = document.getElementById('configResult');
            result.innerHTML = '<p>Checking configuration...</p>';
            
            try {
                const response = await fetch('/debug/email-config/');
                const data = await response.json();
                
                if (data.status === 'success') {
                    result.innerHTML = `
                        <div class="result success">
                            <h3>✅ Email Configuration</h3>
                            <pre>${JSON.stringify(data, null, 2)}</pre>
                        </div>
                    `;
                } else {
                    result.innerHTML = `
                        <div class="result error">
                            <h3>❌ Configuration Error</h3>
                            <p>${data.error}</p>
                            <pre>${data.traceback || ''}</pre>
                        </div>
                    `;
                }
            } catch (error) {
                result.innerHTML = `
                    <div class="result error">
                        <h3>❌ Network Error</h3>
                        <p>${error.message}</p>
                    </div>
                `;
            }
        }
        
        async function sendTestEmail() {
            const email = document.getElementById('testEmail').value;
            const result = document.getElementById('emailResult');
            
            if (!email) {
                result.innerHTML = '<div class="result error">Please enter an email address</div>';
                return;
            }
            
            result.innerHTML = '<p>Sending test email...</p>';
            
            try {
                const response = await fetch('/debug/test-email/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify({ email: email })
                });
                
                const data = await response.json();
                
                if (data.status === 'success') {
                    result.innerHTML = `
                        <div class="result success">
                            <h3>✅ Email Sent Successfully!</h3>
                            <p><strong>Message:</strong> ${data.message}</p>
                            <p><strong>To:</strong> ${data.test_email}</p>
                            <p><strong>Meeting:</strong> ${data.meeting_title} (${data.meeting_id})</p>
                            <p><strong>Backend:</strong> ${data.email_backend}</p>
                        </div>
                    `;
                } else {
                    result.innerHTML = `
                        <div class="result error">
                            <h3>❌ Email Failed</h3>
                            <p><strong>Error:</strong> ${data.message || data.error}</p>
                            <pre>${data.traceback || ''}</pre>
                        </div>
                    `;
                }
            } catch (error) {
                result.innerHTML = `
                    <div class="result error">
                        <h3>❌ Network Error</h3>
                        <p>${error.message}</p>
                    </div>
                `;
            }
        }
        
        function getCookie(name) {
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }
        
        // Auto-load config on page load
        window.onload = function() {
            checkConfig();
        };
        </script>
    </body>
    </html>
    """
    
    from django.http import HttpResponse
    return HttpResponse(html)