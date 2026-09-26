import json
from channels.generic.websocket import AsyncWebsocketConsumer

class DashboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = 'dashboard_updates'

        # Join dashboard updates group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()
        print(f"WebSocket Client Connected to {self.group_name}")

    async def disconnect(self, close_code):
        # Leave dashboard group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        print(f"WebSocket Client Disconnected from {self.group_name}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            # Echo or process incoming socket messages if needed
            await self.send(text_data=json.dumps({
                'type': 'ack',
                'message': 'Received',
                'payload': data
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({'error': str(e)}))

    async def dashboard_update(self, event):
        """
        Handler for messages broadcasted to group 'dashboard_updates'
        """
        await self.send(text_data=json.dumps({
            'type': event.get('update_type', 'dashboard_update'),
            'message': event.get('message', 'Stock updated'),
            'data': event.get('data', {})
        }))
