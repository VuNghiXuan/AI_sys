# enterprise_factory/consumers/memory_loader.py
import logging
from channels.db import database_sync_to_async
from enterprise_factory.models import AgentDiscussion, Company, IntentMemory, SystemConfig

logger = logging.getLogger(__name__)

class MemoryLoaderMixin:
    
    @database_sync_to_async
    def save_and_get_context(self, sender_type: str, content: str, agent_obj=None) -> str:
        company = Company.objects.filter(code='GLOBAL').first()
        owner_name = SystemConfig.objects.filter(key="TENANT_OWNER_NAME").first()
        owner_str = owner_name.value if owner_name else "Người dùng"

        try:
            created_obj = AgentDiscussion.objects.create(
                company=company,
                sender_type=sender_type,
                agent=agent_obj,
                message_content=content,
                phase='USER_DIRECTIVE' if sender_type == 'USER' else 'AGENT_RESPONSE'
            )
            sender_display = owner_str if sender_type == 'USER' else (agent_obj.display_name if agent_obj else "AI Agent")
            print(f"[DB] Lưu message | ID: {created_obj.id} | Type: {sender_type} | Sender: {sender_display}")
        except Exception as e:
            logger.warning(f"[!] Không thể lưu AgentDiscussion: {e}")

        # Lấy lịch sử gần đây (Sliding Window kết hợp lịch sử dài hạn)
        recent_msgs = AgentDiscussion.objects.select_related('agent').order_by('-id')[:8]
        history = []
        for m in reversed(recent_msgs):
            if m.sender_type == 'USER':
                name = owner_str
            elif m.sender_type == 'SYSTEM':
                name = "Hệ thống"
            else:
                name = m.agent.display_name if m.agent else "AI Agent"
            history.append(f"{name}: {m.message_content}")
        return "\n".join(history)

    @database_sync_to_async
    def get_historical_context_summary(self) -> str:
        """Lục lại các quyết định và chỉ đạo quan trọng từ các phiên trước để phục hồi ngữ cảnh"""
        try:
            past_directives = AgentDiscussion.objects.filter(sender_type='USER').order_by('-id')[1:6]
            summaries = [m.message_content[:100] for m in past_directives if m.message_content]
            if summaries:
                return " | ".join(summaries)
        except Exception:
            pass
        return "Chưa có dữ liệu ghi nhớ trước đó."

    @database_sync_to_async
    def save_intent_memory(self, query_text: str, intent_code: str, target_agent: str, tier: int, feedback_type: str):
        query_normalized = query_text.lower().strip()
        IntentMemory.objects.update_or_create(
            query_text=query_normalized,
            defaults={
                'intent_code': intent_code,
                'target_agent': target_agent,
                'tier': tier,
                'feedback_type': feedback_type
            }
        )