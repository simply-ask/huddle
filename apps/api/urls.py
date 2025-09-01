from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('meetings', views.MeetingViewSet)
router.register('recordings', views.AudioRecordingViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('upload-audio/', views.upload_audio, name='upload_audio'),
    path('meeting/<str:meeting_id>/status/', views.meeting_status, name='meeting_status'),
]