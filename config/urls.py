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
from django.http import HttpResponse
from apps.meetings import views as meeting_views

def home_view(request):
    return HttpResponse("""
    <h1>Huddle - Meeting Intelligence Platform</h1>
    <p>Welcome to Huddle!</p>
    <p>To join a meeting, go to: /meet/[meeting-id]/</p>
    <p>API endpoints available at: /api/</p>
    <p>Admin panel: /admin/</p>
    """)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apps.api.urls')),
    path('meet/<str:meeting_id>/', meeting_views.join_meeting, name='join_meeting'),
    path('meet/<str:meeting_id>/room/', meeting_views.meeting_room, name='meeting_room'),
    path('', home_view, name='home'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

