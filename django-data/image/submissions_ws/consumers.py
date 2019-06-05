from channels.generic.websocket import AsyncWebsocketConsumer
import json


class SubmissionsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.submission_key = self.scope['url_route']['kwargs']['submission_key']
        self.room_group_name = 'submission_%s' % self.submission_key

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        # Send message to room group
        text_data = json.loads(text_data)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'status_message',
                'message': text_data['message'],
                'notification_message': text_data['notification_message']
            }
        )

    # Receive message from room group
    async def status_message(self, event):
        message = event['message']
        notification_message = event['notification_message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'notification_message': notification_message
        }))
