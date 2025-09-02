from django.contrib import admin
from .models import Meeting, MeetingParticipant, MeetingSummary

@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ['meeting_id', 'title', 'host', 'status', 'is_active', 'created_at']
    list_filter = ['status', 'is_active', 'created_at']
    search_fields = ['meeting_id', 'title', 'host__username']
    readonly_fields = ['meeting_id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('meeting_id', 'title', 'description')
        }),
        ('Settings', {
            'fields': ('host', 'status', 'is_active', 'organization_name')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(MeetingParticipant)
class MeetingParticipantAdmin(admin.ModelAdmin):
    list_display = ['meeting', 'user', 'device_type', 'is_recording', 'joined_at']
    list_filter = ['device_type', 'is_recording', 'joined_at']
    search_fields = ['meeting__meeting_id', 'user__username', 'device_info']

@admin.register(MeetingSummary)
class MeetingSummaryAdmin(admin.ModelAdmin):
    list_display = ['meeting', 'created_at']
    search_fields = ['meeting__meeting_id', 'summary', 'action_items']
    readonly_fields = ['created_at']