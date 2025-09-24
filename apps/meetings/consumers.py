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

        if message_type == 'join':
            await self.handle_join_meeting(data)
        elif message_type == 'participant_joined':
            await self.handle_participant_joined(data)
        elif message_type == 'audio_quality_update':
            await self.handle_audio_quality_update(data)
        elif message_type == 'recording_status':
            await self.handle_recording_status(data)
        elif message_type == 'remote_audio':
            await self.handle_remote_audio(data)
        elif message_type == 'request_audio_stream':
            await self.handle_audio_stream_request(data)
        elif message_type == 'mic_status':
            await self.handle_mic_status(data)
    
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
    
    async def handle_remote_audio(self, data):
        """Handle audio from remote participants"""
        # Store remote audio for processing
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'remote_audio_message',
                'participant_id': data.get('participant_id'),
                'participant_name': data.get('participant_name'),
                'audio_data': data.get('audio_data'),
                'timestamp': data.get('timestamp'),
            }
        )
    
    async def handle_audio_stream_request(self, data):
        """Handle request for room audio stream"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'audio_stream_request_message',
                'participant_id': data.get('participant_id'),
            }
        )
    
    async def handle_join_meeting(self, data):
        """Handle user joining meeting - create/update MeetingParticipant record"""
        meeting_id = data.get('meeting_id')
        role = data.get('role', 'participant')
        device_type = data.get('device_type', 'unknown')

        # Get or create participant record
        participant = await self.get_or_create_participant(
            meeting_id,
            role,
            device_type
        )

        if participant:
            # Get host info safely
            is_host = await self.check_is_host(participant)
            participant_name = await self.get_participant_name(participant)

            # Notify group about new participant
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'participant_joined_message',
                    'participant_id': str(participant.id),
                    'participant_name': participant_name,
                    'role': role,
                    'is_host': is_host,
                }
            )

    async def handle_mic_status(self, data):
        """Handle microphone mute/unmute status"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'mic_status_message',
                'participant_id': data.get('participant_id'),
                'muted': data.get('muted'),
            }
        )
    
    async def remote_audio_message(self, event):
        await self.send(text_data=json.dumps(event))
    
    async def audio_stream_request_message(self, event):
        await self.send(text_data=json.dumps(event))
    
    async def mic_status_message(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def get_or_create_participant(self, meeting_id, role, device_type):
        """Get or create MeetingParticipant record for current user"""
        try:
            meeting = Meeting.objects.get(meeting_id=meeting_id, status=Meeting.Status.ACTIVE)
            user = self.scope.get('user')

            # Generate session ID based on user and timestamp
            import uuid
            import time
            session_id = f"{user.id if user and user.is_authenticated else 'guest'}_{int(time.time())}_{uuid.uuid4().hex[:8]}"

            # Create or get participant
            participant, created = MeetingParticipant.objects.get_or_create(
                meeting=meeting,
                session_id=session_id,
                defaults={
                    'user': user if user and user.is_authenticated else None,
                    'user_agent': device_type,
                    'is_recording': False,
                    'audio_quality_score': None,
                }
            )

            # For existing participants, update user if they weren't linked before
            if not created and not participant.user and user and user.is_authenticated:
                participant.user = user
                participant.save()

            return participant

        except Meeting.DoesNotExist:
            return None
        except Exception as e:
            print(f"Error creating participant: {e}")
            return None

    @database_sync_to_async
    def check_is_host(self, participant):
        """Check if participant is the meeting host"""
        try:
            return participant.user and participant.meeting.host == participant.user
        except Exception:
            return False

    @database_sync_to_async
    def get_participant_name(self, participant):
        """Get participant display name"""
        try:
            if participant.user:
                return participant.user.get_full_name() or participant.user.username
            return 'Guest'
        except Exception:
            return 'Guest'