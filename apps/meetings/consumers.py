import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Meeting, MeetingParticipant

class MeetingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.meeting_id = self.scope['url_route']['kwargs']['meeting_id']
        self.room_group_name = f'meeting_{self.meeting_id}'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'participant_joined':
            await self.handle_participant_joined(data)
        elif message_type == 'audio_quality_update':
            await self.handle_audio_quality_update(data)
        elif message_type == 'recording_status':
            await self.handle_recording_status(data)
    
    async def handle_participant_joined(self, data):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'participant_joined_message',
                'session_id': data.get('session_id'),
                'user_agent': data.get('user_agent', ''),
            }
        )
    
    async def handle_audio_quality_update(self, data):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'audio_quality_message',
                'session_id': data.get('session_id'),
                'quality_score': data.get('quality_score'),
            }
        )
    
    async def handle_recording_status(self, data):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'recording_status_message',
                'session_id': data.get('session_id'),
                'is_recording': data.get('is_recording'),
            }
        )
    
    async def participant_joined_message(self, event):
        await self.send(text_data=json.dumps(event))
    
    async def audio_quality_message(self, event):
        await self.send(text_data=json.dumps(event))
    
    async def recording_status_message(self, event):
        await self.send(text_data=json.dumps(event))