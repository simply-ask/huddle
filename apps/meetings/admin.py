from django.contrib import admin
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.urls import path
from django.shortcuts import render, get_object_or_404
from .models import Meeting, MeetingParticipant
from .email_utils import send_voice_setup_invitation, send_meeting_invitation

@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ['meeting_id', 'title', 'host', 'expected_count', 'known_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['meeting_id', 'title', 'host__username']
    readonly_fields = ['meeting_id', 'created_at', 'updated_at']
    filter_horizontal = ['known_speakers']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('meeting_id', 'title')
        }),
        ('Settings', {
            'fields': ('host', 'is_active', 'organization_name')
        }),
        ('Speakers', {
            'fields': ('expected_speakers', 'known_speakers'),
            'description': 'Manage expected attendees and existing voice profiles'
        }),
        ('Timestamps', {
            'fields': ('started_at', 'ended_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['send_voice_invitations', 'send_meeting_invitations']
    
    def expected_count(self, obj):
        return len(obj.expected_speakers)
    expected_count.short_description = 'Expected'
    
    def known_count(self, obj):
        return obj.known_speakers.count()
    known_count.short_description = 'Known'
    
    def send_voice_invitations(self, request, queryset):
        """Send voice setup invitations to expected speakers"""
        total_sent = 0
        total_failed = 0
        
        for meeting in queryset:
            new_speakers = meeting.get_new_speakers()
            for speaker in new_speakers:
                success, message = send_voice_setup_invitation(meeting, speaker['email'])
                if success:
                    total_sent += 1
                else:
                    total_failed += 1
        
        if total_sent > 0:
            messages.success(request, f"Voice setup invitations sent to {total_sent} speakers")
        if total_failed > 0:
            messages.warning(request, f"Failed to send {total_failed} invitations")
    
    send_voice_invitations.short_description = "Send voice setup invitations"
    
    def send_meeting_invitations(self, request, queryset):
        """Send meeting invitations to expected speakers"""
        total_sent = 0
        total_failed = 0
        
        for meeting in queryset:
            for email in meeting.expected_speakers:
                success, message = send_voice_setup_invitation(meeting, email)
                if success:
                    total_sent += 1
                else:
                    total_failed += 1
        
        if total_sent > 0:
            messages.success(request, f"Meeting invitations sent to {total_sent} attendees")
        if total_failed > 0:
            messages.warning(request, f"Failed to send {total_failed} invitations")
    
    send_meeting_invitations.short_description = "Send meeting invitations with voice setup"

@admin.register(MeetingParticipant)
class MeetingParticipantAdmin(admin.ModelAdmin):
    list_display = ['meeting', 'user', 'session_id', 'is_recording', 'created_at']
    list_filter = ['is_recording', 'created_at']
    search_fields = ['meeting__meeting_id', 'user__username', 'session_id']

