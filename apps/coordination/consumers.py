import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .algorithms import PhoneCoordinationAlgorithm

class CoordinationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.meeting_id = self.scope['url_route']['kwargs']['meeting_id']
        self.coordination_group_name = f'coordination_{self.meeting_id}'
        
        await self.channel_layer.group_add(
            self.coordination_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.coordination_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'quality_update':
            await self.handle_quality_update(data)
        elif message_type == 'request_coordination':
            await self.handle_coordination_request(data)
    
    async def handle_quality_update(self, data):
        # Update quality metrics and trigger coordination if needed
        await self.channel_layer.group_send(
            self.coordination_group_name,
            {
                'type': 'quality_update_message',
                'session_id': data.get('session_id'),
                'quality_metrics': data.get('quality_metrics', {}),
            }
        )
    
    async def handle_coordination_request(self, data):
        # Trigger coordination algorithm
        coordination_result = await self.run_coordination_algorithm()
        
        await self.channel_layer.group_send(
            self.coordination_group_name,
            {
                'type': 'coordination_decision_message',
                'decision': coordination_result,
            }
        )
    
    @database_sync_to_async
    def run_coordination_algorithm(self):
        from apps.meetings.models import Meeting
        
        try:
            meeting = Meeting.objects.get(meeting_id=self.meeting_id)
            algorithm = PhoneCoordinationAlgorithm()
            decision = algorithm.create_coordination_decision(meeting)
            
            if decision:
                return {
                    'primary_recorder': decision.primary_recorder.session_id,
                    'backup_recorders': list(decision.backup_recorders.values_list('session_id', flat=True)),
                    'decision_id': decision.id
                }
            
        except Meeting.DoesNotExist:
            pass
        
        return None
    
    async def quality_update_message(self, event):
        await self.send(text_data=json.dumps(event))
    
    async def coordination_decision_message(self, event):
        await self.send(text_data=json.dumps(event))