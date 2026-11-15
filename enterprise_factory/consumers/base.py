# enterprise_factory/consumers/base.py
import logging
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from enterprise_factory.models import AgentRegistry, AgentDiscussion, Company, IntentMemory, SystemConfig

logger = logging.getLogger(__name__)

class BaseWarRoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = "live_war_room_global"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        print(f"[+] [WS_CONNECT] Client kết nối War Room thành công. Channel: {self.channel_name}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        print(f"[-] [WS_DISCONNECT] Client ngắt kết nối. Code: {close_code}")

    @database_sync_to_async
    def get_tenant_owner_name(self) -> str:
        cfg = SystemConfig.objects.filter(key="TENANT_OWNER_NAME").first()
        return cfg.value if cfg else "Sếp"

    @database_sync_to_async
    def get_all_active_agents(self):
        return list(AgentRegistry.objects.select_related('role').all())

    @database_sync_to_async
    def get_specific_agent(self, agent_id):
        return AgentRegistry.objects.select_related('role').filter(agent_id=agent_id).first()

    @database_sync_to_async
    def get_last_user_message(self) -> str:
        last_msg = AgentDiscussion.objects.filter(sender_type='USER', message_content__isnull=False).exclude(message_content='').order_by('-id').first()
        return last_msg.message_content if last_msg else ""

    async def broadcast_message(self, event):
        payload = {
            'status': 'broadcast',
            'sender_type': event.get('sender_type', 'AGENT'),
            'sender': event.get('sender'),
            'target': event.get('target', 'ALL'),
            'phase': event.get('phase', 'GENERAL'),
            'content': event.get('content'),
            'avatar_url': event.get('avatar_url', ''),
            'title_name': event.get('title_name', '')
        }
        await self.send(text_data=json.dumps(payload))