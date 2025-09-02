from django.contrib import admin
from .models import Meeting, MeetingParticipant

@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ['meeting_id', 'title', 'host', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['meeting_id', 'title', 'host__username']
    readonly_fields = ['meeting_id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('meeting_id', 'title')
        }),
        ('Settings', {
            'fields': ('host', 'is_active', 'organization_name')
        }),
        ('Timestamps', {
            'fields': ('started_at', 'ended_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(MeetingParticipant)
class MeetingParticipantAdmin(admin.ModelAdmin):
    list_display = ['meeting', 'user', 'session_id', 'is_recording', 'created_at']
    list_filter = ['is_recording', 'created_at']
    search_fields = ['meeting__meeting_id', 'user__username', 'session_id']

