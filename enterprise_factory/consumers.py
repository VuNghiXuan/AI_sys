"""
WebSocket Consumer cho Live War Room của vnxBox Enterprise.
Hỗ trợ @ Mention nhân sự, phân luồng action, tranh luận hội đồng BOD - DEV - HR theo thời gian thực.
"""
import logging
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from enterprise_factory.models import AgentRegistry

logger = logging.getLogger(__name__)


class WarRoomConsumer(AsyncWebsocketConsumer):
    """Kênh WebSocket quản lý phòng họp trực tuyến và trạng thái hoạt động của nhân sự AI"""

    async def connect(self):
        self.room_group_name = "live_war_room_global"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        logger.info(f"[*] [WS_CONNECT] Kết nối War Room thành công (Channel ID: {self.channel_name})")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        logger.info(f"[*] [WS_DISCONNECT] Ngắt kết nối War Room. Code: {close_code}")

    @database_sync_to_async
    def get_all_active_agents(self):
        """Lấy toàn bộ danh sách nhân sự AI trực chiến từ Database"""
        return list(AgentRegistry.objects.select_related('role').all())

    @database_sync_to_async
    def get_specific_agent(self, agent_id):
        """Lấy thông tin nhân sự cụ thể theo ID khi được @mention"""
        try:
            return AgentRegistry.objects.select_related('role').get(agent_id=agent_id)
        except AgentRegistry.DoesNotExist:
            return None

    async def receive(self, text_data):
        """Nhận chỉ đạo, tin nhắn hoặc hành động @ mention từ Sếp"""
        logger.debug(f"[DEBUG] [WS_RECEIVE] Raw payload: {text_data}")
        
        try:
            data = json.loads(text_data)
            action = data.get('action', 'chat')
            message = data.get('message', '')
            target_agent = data.get('target_agent', 'ALL')

            logger.info(f"[*] [WS_ACTION] Action: '{action}' | Target: '{target_agent}' | Nội dung: '{message}'")

            # 1. Broadcast tin nhắn chỉ đạo của Sếp xuống phòng họp
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'broadcast_message',
                    'sender': 'Sếp Vũ',
                    'target': target_agent,
                    'phase': 'DIRECTIVE',
                    'content': message,
                    'agent_status': 'LISTENING'
                }
            )

            # 2. Xử lý phản hồi đa chiều từ Hội đồng AI (BOD, DEV, HR)
            if target_agent == 'ALL' or 'app' in message.lower() or 'viết' in message.lower() or 'bán vàng' in message.lower():
                # Kịch bản phòng họp sôi động: Cả BOD, DEV và HR cùng vào tranh luận phân tích dự án
                agents = await self.get_all_active_agents()
                
                for ag in agents:
                    role_code = ag.role.role_code if ag.role else 'GENERAL'
                    content_response = self.generate_expert_response(ag.display_name, role_code, message)
                    
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'broadcast_message',
                            'sender': ag.display_name,
                            'target': 'ALL',
                            'phase': 'DEBATE_CONSENSUS',
                            'content': content_response,
                            'agent_status': 'WORKING'
                        }
                    )
            else:
                # Trường hợp Sếp gọi riêng một chuyên gia cụ thể qua @mention
                agent_obj = await self.get_specific_agent(target_agent)
                if agent_obj:
                    role_code = agent_obj.role.role_code if agent_obj.role else 'GENERAL'
                    content_response = f"Tuân lệnh Sếp! Với tư cách là {agent_obj.display_name} ({agent_obj.domain_scope}), tôi đã tiếp nhận yêu cầu: '{message}'. Tiến hành lập đồ thị DAG thực thi ngay."
                    
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'broadcast_message',
                            'sender': agent_obj.display_name,
                            'target': target_agent,
                            'phase': 'FOCUSED_TASK',
                            'content': content_response,
                            'agent_status': 'CODING'
                        }
                    )

        except Exception as e:
            logger.error(f"[-] [WS_ERROR] Lỗi xử lý message: {str(e)}", exc_info=True)

    def generate_expert_response(self, agent_name, role_type, user_msg):
        """Hàm mô phỏng chuyên gia AI phản hồi thông minh theo đúng vai trò CEO và Giám đốc Nhân sự"""
        msg_lower = user_msg.lower()
        role_upper = str(role_type).upper()
        name_lower = agent_name.lower()
        
        # 1. Giám đốc Nhân sự (HR)
        if 'hr' in role_upper or 'nhân sự' in name_lower:
            return (
                f"📊 **[Giám đốc Nhân sự]**: Dạ, tôi đã có mặt thưa Sếp! "
                f"Liên quan đến yêu cầu '{user_msg}', tôi sẽ kích hoạt ngay **HR Spawner Engine** để rà soát ma trận nhân sự, "
                f"đánh giá năng lực các Agent hiện tại và tiến hành cấp phát tài nguyên, tuyển dụng bổ sung chuyên gia nếu thiếu hụt."
            )
        
        # 2. Tổng Giám đốc / CEO (BOD)
        elif 'bod' in role_upper or 'ceo' in role_upper or 'giám đốc điều hành' in name_lower:
            return (
                f"🎯 **[CEO / Tổng Giám đốc]**: Đã tiếp nhận chỉ đạo trọng tâm của Sếp: '{user_msg}'. "
                f"Tôi yêu cầu toàn bộ ban điều hành và các phòng ban lập tức bóc tách ma trận nghiệp vụ, "
                f"phối hợp chặt chẽ với Giám đốc Nhân sự để đưa dự án vào tiến độ Sprint thực thi."
            )
        
        # 3. Các chuyên gia kỹ thuật khác (Dev, QA,...)
        elif 'dev' in role_upper or 'backend' in name_lower:
            return (
                f"💻 **[Dev Core]**: Đã nhận lệnh từ Sếp. Sẵn sàng hiện thực hóa kiến trúc Django, SQLite và Alpine.js "
                f"với chuẩn quan hệ dữ liệu N-1 cho hệ thống vận hành."
            )
        else:
            return f"🤖 **[{agent_name}]**: Đã ghi nhận chỉ đạo của Sếp và sẵn sàng phối hợp cùng Ban Tổng Giám đốc."

    async def broadcast_message(self, event):
        """Đẩy dữ liệu và trạng thái hành động xuống giao diện qua WebSocket"""
        await self.send(text_data=json.dumps({
            'status': 'broadcast',
            'sender': event.get('sender'),
            'target': event.get('target', 'ALL'),
            'phase': event.get('phase', 'GENERAL'),
            'content': event.get('content'),
            'agent_status': event.get('agent_status', 'ONLINE')
        }))