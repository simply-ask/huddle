from django.contrib import admin
from django.utils.html import format_html
from .models import SpeakerProfile, VoiceSetupToken

@admin.register(SpeakerProfile)
class SpeakerProfileAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'organization', 'meetings_count', 'accuracy_score', 'has_audio', 'is_active', 'created_at']
    list_filter = ['is_active', 'organization', 'created_at']
    search_fields = ['full_name', 'email', 'job_title', 'organization__username']
    readonly_fields = ['created_at', 'updated_at', 'audio_player']
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('full_name', 'email', 'job_title', 'organization')
        }),
        ('Voice Profile', {
            'fields': ('sample_audio', 'audio_player', 'voice_signature'),
            'description': 'Voice sample and analysis data'
        }),
        ('Statistics', {
            'fields': ('meetings_count', 'accuracy_score', 'is_active'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def has_audio(self, obj):
        if obj.sample_audio:
            return format_html('<span style="color: green;">✓ Yes</span>')
        return format_html('<span style="color: red;">✗ No</span>')
    has_audio.short_description = 'Audio Sample'
    has_audio.admin_order_field = 'sample_audio'
    
    def audio_player(self, obj):
        if obj.sample_audio:
            return format_html(
                '<audio controls style="width: 300px;"><source src="{}" type="audio/webm">Your browser does not support audio.</audio>',
                obj.sample_audio.url
            )
        return 'No audio sample available'
    audio_player.short_description = 'Audio Player'

@admin.register(VoiceSetupToken)
class VoiceSetupTokenAdmin(admin.ModelAdmin):
    list_display = ['meeting_id', 'email', 'token_preview', 'used', 'expires_at', 'created_at']
    list_filter = ['used', 'expires_at', 'created_at']
    search_fields = ['meeting_id', 'email', 'token']
    readonly_fields = ['token', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Token Information', {
            'fields': ('meeting_id', 'email', 'token')
        }),
        ('Status', {
            'fields': ('used', 'expires_at'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def token_preview(self, obj):
        return f"{obj.token[:12]}..."
    token_preview.short_description = 'Token (Preview)'
    
    actions = ['mark_as_used', 'mark_as_unused']
    
    def mark_as_used(self, request, queryset):
        updated = queryset.update(used=True)
        self.message_user(request, f'{updated} tokens marked as used.')
    mark_as_used.short_description = 'Mark selected tokens as used'
    
    def mark_as_unused(self, request, queryset):
        updated = queryset.update(used=False)
        self.message_user(request, f'{updated} tokens marked as unused.')
    mark_as_unused.short_description = 'Mark selected tokens as unused'