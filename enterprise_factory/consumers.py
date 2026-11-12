# File: enterprise_factory/consumers.py
import logging
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from enterprise_factory.models import AgentRegistry, AgentDiscussion, Company
from enterprise_factory.intent_router import IntentRouter
from enterprise_factory.services.orchestrator import ask_local_agent

logger = logging.getLogger(__name__)


class WarRoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = "live_war_room_global"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        print(f"[+] [WS_CONNECT] Client đã kết nối thành công vào War Room. Channel Name: {self.channel_name}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        print(f"[-] [WS_DISCONNECT] Client ngắt kết nối. Code: {close_code}")

    @database_sync_to_async
    def get_all_active_agents(self):
        return list(AgentRegistry.objects.select_related('role').all())

    @database_sync_to_async
    def get_specific_agent(self, agent_id):
        return AgentRegistry.objects.select_related('role').filter(agent_id=agent_id).first()

    @database_sync_to_async
    def save_and_get_context(self, sender_name: str, content: str) -> str:
        """Lưu tin nhắn vào DB và in log xác nhận"""
        company = Company.objects.filter(code='GLOBAL').first()
        try:
            kwargs = {'company': company, 'message_content': content}
            if hasattr(AgentDiscussion, 'agent_name'):
                kwargs['agent_name'] = sender_name
            elif hasattr(AgentDiscussion, 'sender'):
                kwargs['sender'] = sender_name
            
            created_obj = AgentDiscussion.objects.create(**kwargs)
            print(f"[DB] Đã lưu message thành công | ID: {created_obj.id} | Sender: {sender_name} | Content: {content[:30]}...")
        except Exception as ex:
            try:
                AgentDiscussion.objects.create(company=company, message_content=content)
                print(f"[DB-Fallback] Đã lưu message không có trường sender/agent_name.")
            except Exception as e:
                logger.warning(f"[!] Không thể lưu AgentDiscussion vào DB: {e}")

        recent_msgs = AgentDiscussion.objects.order_by('-id')[:6]
        history = [f"{getattr(m, 'agent_name', getattr(m, 'sender', 'Chat'))}: {m.message_content}" for m in reversed(recent_msgs)]
        return "\n".join(history)

    @database_sync_to_async
    def call_llm_sync(self, system_prompt: str, user_prompt: str) -> str:
        print(f"[LLM] Đang gọi Ollama... Prompt length: {len(user_prompt)}")
        response = ask_local_agent(system_prompt, user_prompt, timeout_seconds=60)
        print(f"[LLM] Nhận phản hồi từ Ollama xong. Response length: {len(response) if response else 0}")
        return response

    async def receive(self, text_data):
        print(f"\n[INCOMING WS RAW] -> {text_data}")
        try:
            data = json.loads(text_data)
            message = data.get('message', '').strip()
            target_agent = data.get('target_agent', 'ALL')
            if not message:
                print("[!] Message rỗng, bỏ qua.")
                return

            # Cố định tên Sếp Vũ chuẩn xác 100%
            sender_user = 'Sếp Vũ'

            # 1. Broadcast tin nhắn của Sếp
            print(f"[BROADCAST] Đẩy tin nhắn của '{sender_user}' xuống group...")
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'broadcast_message',
                    'sender': sender_user,
                    'target': target_agent,
                    'phase': 'DIRECTIVE',
                    'content': message
                }
            )
            await self.save_and_get_context(sender_user, message)

            # --- ROUTING & DELEGATION ---
            msg_lower = message.lower()
            if target_agent == 'ALL':
                if any(kw in msg_lower for kw in ['hr', 'nhân sự', 'nhân viên', 'tuyển dụng', 'gọi hr']):
                    target_agent = 'HR_MANAGER_01'
                elif any(kw in msg_lower for kw in ['dev', 'lập trình', 'code', 'fix bug', 'lỗi']):
                    target_agent = 'DEV_BE_01'

            agent_obj = None
            if target_agent != 'ALL':
                agent_obj = await self.get_specific_agent(target_agent)
            if not agent_obj:
                agent_obj = await self.get_specific_agent('BOD_CEO_01')

            sender_name = agent_obj.display_name if agent_obj else 'BOD CEO (Tổng Giám Đốc AI)'
            agent_code = agent_obj.agent_id if agent_obj else 'BOD_CEO_01'
            domain_scope = agent_obj.domain_scope if agent_obj else 'GLOBAL_MANAGEMENT'

            print(f"[ROUTING] Target Agent được chọn: {agent_code} ({sender_name})")

            system_prompt = (
                f"Bạn là {sender_name} ({agent_code}) của tập đoàn vnxBox Enterprise.\n"
                f"Chức năng: {domain_scope}.\n"
                f"Sếp Vũ vừa chỉ đạo: '{message}'.\n"
                f"Quy tắc bắt buộc: Luôn xưng 'em' hoặc 'tôi' với Sếp Vũ, trả lời cực kỳ ngắn gọn, sắc sảo, thực tế, "
                f"không bao giờ nói 'tôi là trợ lý AI' hay 'tôi không thể giúp'."
            )

            routing = IntentRouter.route(message)
            tier = routing['tier']
            print(f"[ROUTER] Intent Tier: {tier} | Code: {routing.get('intent_code')}")

            if tier == 2:
                agents = await self.get_all_active_agents()
                agent_details = "\n".join([f"- **{ag.display_name}** (`{ag.agent_id}`): {ag.domain_scope}" for ag in agents])
                response_text = f"📊 **[Báo cáo Nhân sự]**: Hiện tại ma trận có **{len(agents)} nhân sự AI** trực chiến:\n{agent_details}"
                sender_name = 'HR Director (Giám Đốc Nhân Sự AI)'
            else:
                response_text = await self.call_llm_sync(system_prompt, message)
                if not response_text or "không thể" in response_text or "trợ lý AI" in response_text:
                    response_text = f"Dạ báo cáo Sếp, việc này để em chỉ đạo ban điều hành rà soát và báo cáo chi tiết lại ngay ạ!"

            # 2. Broadcast câu trả lời của AI
            print(f"[BROADCAST] Đẩy phản hồi của AI '{sender_name}' xuống group...")
            await self.save_and_get_context(sender_name, response_text)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'broadcast_message',
                    'sender': sender_name,
                    'target': target_agent,
                    'phase': routing.get('intent_code', 'GENERAL'),
                    'content': response_text
                }
            )

        except Exception as e:
            logger.error(f"[-] [WS_ERROR] Lỗi xử lý message: {str(e)}", exc_info=True)
            print(f"[-] [WS_ERROR EXCEPTION]: {str(e)}")

    async def broadcast_message(self, event):
        payload = {
            'status': 'broadcast',
            'sender': event.get('sender'),
            'target': event.get('target', 'ALL'),
            'phase': event.get('phase', 'GENERAL'),
            'content': event.get('content')
        }
        print(f"[WS SEND TO CLIENT] -> Sender: {payload['sender']} | Content: {payload['content'][:30]}...")
        await self.send(text_data=json.dumps(payload))