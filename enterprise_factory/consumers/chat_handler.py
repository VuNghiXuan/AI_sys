"""
WebSocket Chat Handler cho vnxBox Enterprise.
Tích hợp IntentMemory Cache, Thực thi Tool động (Web Search, DB Query, Code),
và Luồng thảo luận đa tác tử (Multi-Agent Live Progress) trên War Room.
"""

import logging
import json
import datetime
from asgiref.sync import sync_to_async
from enterprise_factory.intent_router import IntentRouter
from enterprise_factory.services.orchestrator import ask_local_agent
from enterprise_factory.services.intent_cache_middleware import IntentCacheMiddleware
from .base import BaseWarRoomConsumer
from .memory_loader import MemoryLoaderMixin

logger = logging.getLogger(__name__)


class ChatHandlerConsumer(BaseWarRoomConsumer, MemoryLoaderMixin):

    async def call_llm_sync(self, system_prompt: str, user_prompt: str) -> str:
        print(f"[LLM] Đang gọi Ollama... Prompt length: {len(user_prompt)}")
        return await sync_to_async(ask_local_agent)(system_prompt, user_prompt, timeout_seconds=120)

    async def broadcast_step(self, sender_type: str, sender: str, target: str, phase: str, content: str, title: str = '', avatar: str = ''):
        """Hàm tiện ích phát từng bước tiến trình hoặc trao đổi lên khung chat War Room"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'broadcast_message',
                'sender_type': sender_type,
                'sender': sender,
                'target': target,
                'phase': phase,
                'content': content,
                'avatar_url': avatar,
                'title_name': title
            }
        )

    async def get_last_user_query_context(self) -> str:
        """Hàm phụ trợ lấy nội dung câu hỏi có ý nghĩa gần nhất của Sếp (bỏ qua các câu ngắn như 'lên mạng tra đi')"""
        try:
            from enterprise_factory.models import ChatMessage # Hoặc tên model lưu message của Sếp
            messages = await sync_to_async(list)(
                ChatMessage.objects.filter(sender_type='USER').order_by('-created_at')[:5]
            )
            for m in messages:
                content = (getattr(m, 'message_content', None) or getattr(m, 'content', '')).strip()
                # Nếu câu trước dài hơn 4 từ và không phải là câu ra lệnh ngắn
                if len(content.split()) > 3 and not any(cmd in content.lower() for cmd in ['lên mạng tra', 'tra cứu đi', 'tìm xem', 'họp đi', 'alo']):
                    return content
        except Exception as e:
            logger.warning(f"[-] Không thể lấy lịch sử ngữ cảnh: {e}")
        return ""

    async def execute_intent_tools(self, intent_code: str, message: str, target_agent: str) -> tuple[str, str]:
        """
        Tầng thực thi công cụ thực tế trước khi đưa cho LLM tổng hợp.
        Đã tích hợp cơ chế thông minh mở rộng từ khóa nếu câu lệnh của Sếp quá ngắn.
        Trả về: (raw_data_context, execution_status_note)
        """
        raw_context = ""
        status_note = "Hoàn tất thu thập dữ liệu thuận lợi."

        # 1. THỰC THI WEB SEARCH THỰC TẾ (Lọc từ khóa thông minh bằng Regex / Phép thay thế chuẩn)
        if intent_code == 'WEB_SEARCH':
            search_query = message
            
            # Danh sách các từ ngữ ra lệnh / rác cần loại bỏ triệt để
            import re
            # Xóa các cụm từ chỉ hành động tra cứu
            cleaned_query = message.lower()
            for phrase in ['lên mạng', 'tra cứu', 'tra lại', 'tra đi', 'tìm kiếm', 'hãy tìm', 'giúp tao', 'cho tao', 'mày tra', 'đi']:
                cleaned_query = cleaned_query.replace(phrase, '')
            
            # Loại bỏ các từ đệm đứng đầu/cuối như 'lại', 'cụ', 'về', v.v. nếu cần, hoặc giữ lại thực thể chính
            cleaned_query = re.sub(r'\b(lại|đi|giúp|tao|cho|về)\b', '', cleaned_query)
            search_query = cleaned_query.strip()
            
            # Nếu sau khi lọc mà rỗng hoặc quá ngắn, fallback về nguyên văn tin nhắn của Sếp
            if len(search_query) <= 2:
                search_query = message

            logger.info(f"[*] [SMART WEB SEARCH] Từ khóa gốc: '{message}' -> Từ khóa tối ưu cho Bing: '{search_query}'")

            await self.broadcast_step(
                'AGENT', 'Chuyên viên Tra cứu (Search Specialist)', target_agent, 'PROGRESS',
                f"🔍 Đã tối ưu từ khóa. Đang kết nối công cụ Web Search với từ khóa: *'{search_query}'*...",
                'Market & Web Intelligence'
            )
            try:
                from enterprise_factory.services import web_search
                search_fn = getattr(web_search, 'search_web', None) or getattr(web_search, 'perform_web_search', None) or getattr(web_search, 'run_search', None)
                if search_fn:
                    search_res = await sync_to_async(search_fn)(search_query)
                    raw_context = str(search_res)[:3500]
                    preview = raw_context[:250].replace('\n', ' ') + "..." if len(raw_context) > 250 else raw_context
                    await self.broadcast_step(
                        'AGENT', 'Chuyên viên Tra cứu (Search Specialist)', target_agent, 'PROGRESS',
                        f"📥 **Dữ liệu thô thu được từ Internet (Từ khóa: '{search_query}'):**\n> {preview}\n\n➡️ Đang chuyển giao dữ liệu thô sang BOD để phân tích và tổng hợp báo cáo.",
                        'Market & Web Intelligence'
                    )
                else:
                    status_note = "Vướng mắc: Module web_search.py chưa định nghĩa hàm search."
                    await self.broadcast_step(
                        'SYSTEM', 'Hệ thống vnxBox', target_agent, 'PROGRESS',
                        f"⚠️ {status_note}", 'System Monitor'
                    )
            except Exception as e:
                status_note = f"Vướng mắc khi cào dữ liệu mạng: {str(e)}"
                logger.error(f"[-] [WEB_SEARCH TOOL ERROR]: {e}")

        # 2. THỰC THI TRUY VẤN DỮ LIỆU HỆ THỐNG (DB_QUERY)
        elif intent_code == 'DB_QUERY':
            await self.broadcast_step(
                'AGENT', 'HR Director (Giám Đốc Nhân Sự AI)', target_agent, 'PROGRESS',
                "📊 Đang trích xuất dữ liệu trực tiếp từ 4 Tháp Quản Trị (AgentRegistry, ToolRegistry, WorkflowBlueprint)...",
                'Giám Đốc Nhân Sự'
            )
            try:
                from enterprise_factory.models import AgentRegistry, ToolRegistry, WorkflowBlueprint
                agents_data = await sync_to_async(list)(AgentRegistry.objects.values('agent_id', 'display_name', 'domain_scope'))
                tools_count = await sync_to_async(ToolRegistry.objects.filter(is_active=True).count)()
                wf_count = await sync_to_async(WorkflowBlueprint.objects.filter(is_active=True).count)()

                raw_context = (
                    f"Tổng số nhân sự AI: {len(agents_data)}. Chi tiết: {json.dumps(agents_data, ensure_ascii=False)}. "
                    f"Số công cụ động đang bật: {tools_count}. Số quy trình DAG đang bật: {wf_count}."
                )
                await self.broadcast_step(
                    'AGENT', 'HR Director (Giám Đốc Nhân Sự AI)', target_agent, 'PROGRESS',
                    f"📥 **Dữ liệu thô từ Database:** Tìm thấy {len(agents_data)} nhân sự AI, {tools_count} tools và {wf_count} workflows. Đang tổng hợp báo cáo...",
                    'Giám Đốc Nhân Sự'
                )
            except Exception as e:
                status_note = f"Lỗi truy xuất DB: {str(e)}"

        # 3. THỰC THI KỸ THUẬT / CODE (DEEP_CODE)
        elif intent_code == 'DEEP_CODE':
            await self.broadcast_step(
                'AGENT', 'Tech Lead AI (Kiến trúc sư trưởng)', target_agent, 'PROGRESS',
                "🛠️ Đang quét cấu trúc AST Codebase và kiểm tra Sandbox để lên phương án kỹ thuật...",
                'Chief Technology Officer'
            )

        return raw_context, status_note

    async def receive(self, text_data):
        print(f"\n[INCOMING WS RAW] -> {text_data}")
        try:
            data = json.loads(text_data)
            action = data.get('action', 'chat')
            owner_name = await self.get_tenant_owner_name()

            # Xử lý nút Feedback tự học
            if action == 'feedback':
                feedback_type = data.get('feedback_type', 'LIKE')
                target_agent = data.get('target_agent', 'ALL')
                tier = data.get('tier', 1)
                intent_code = data.get('intent_code', 'LLM_CHAT')

                if feedback_type == 'CORRECT' and data.get('intent_code'):
                    intent_code = data.get('intent_code')
                    tier = 3 if intent_code in ['DEEP_CODE', 'WEB_SEARCH'] else (2 if intent_code == 'DB_QUERY' else 1)
                    target_agent = 'DEV_BE_01' if tier == 3 else ('HR_MANAGER_01' if tier == 2 else 'BOD_CEO_01')

                last_user_msg = await self.get_last_user_message()
                if last_user_msg:
                    await self.save_intent_memory(last_user_msg, intent_code, target_agent, tier, feedback_type)
                    print(f"🧠 [SELF-LEARNING] Ghi nhớ qua [{feedback_type}]: '{last_user_msg}' -> Intent: {intent_code}")
                return

            message = data.get('message', '').strip()
            target_agent = data.get('target_agent', 'ALL')
            if not message:
                return

            # 1. Lưu và hiển thị chỉ đạo của Sếp
            await self.save_and_get_context('USER', message, agent_obj=None)
            await self.broadcast_step('USER', owner_name, target_agent, 'DIRECTIVE', message, 'Chủ sở hữu hệ thống')

            # 2. Định tuyến ý định (HybridSemanticRouter với Cosine Similarity)
            routing = IntentRouter.route(message)
            tier = routing.get('tier', 1)
            intent_code = routing.get('intent_code', 'GENERAL')
            target_agent = routing.get('target_agent', target_agent)

            if len(message) > 250 and intent_code in ['SMALL_TALK', 'MEETING_CALL']:
                intent_code = 'DEEP_CODE'
                tier = 3
                target_agent = 'ALL'

            print(f"🎯 [INTENT RESOLVED] Code: {intent_code} | Tier: {tier} | Target: {target_agent}")

            # 3. KIỂM TRA CACHE TỐC ĐỘ CAO (IntentMemory Cache - 0.01s)
            if intent_code not in ['WEB_SEARCH']:  # Tin tức/giá cả thời gian thực luôn cần quét mới
                cached_reply = await sync_to_async(IntentCacheMiddleware.get_cached_response)(message, intent_code)
                if cached_reply:
                    await self.broadcast_step(
                        'SYSTEM', 'Hệ thống vnxBox', target_agent, 'PROGRESS',
                        '⚡ [INTENT CACHE HIT]: Truy xuất kết quả đã kiểm chứng từ bộ nhớ trong 0.01s!', 'Fast Memory'
                    )
                    await self.broadcast_step(
                        'AGENT', 'BOD CEO (Tổng Giám Đốc AI)', target_agent, intent_code,
                        cached_reply, 'Tổng Giám Đốc Điều Hành'
                    )
                    return

            # 4. Xác định nhân sự phụ trách
            bod_agent = await self.get_specific_agent('BOD_CEO_01')
            assigned_agent = (target_agent != 'ALL' and await self.get_specific_agent(target_agent)) or bod_agent
            sender_name = assigned_agent.display_name if assigned_agent else 'BOD CEO (Tổng Giám Đốc AI)'
            sender_title = getattr(assigned_agent, 'title_name', 'AI Specialist') if assigned_agent else 'Tổng Giám Đốc'

            # Xử lý phản hồi tức thì cho chào hỏi / gọi họp
            if intent_code in ['SMALL_TALK', 'MEETING_CALL']:
                quick_msg = f"Dạ em nghe thưa Sếp {owner_name}! Ban điều hành và các phòng ban AI đã tề tựu đầy đủ, sẵn sàng nhận chỉ đạo ạ."
                await self.save_and_get_context('AGENT', quick_msg, agent_obj=bod_agent)
                await self.broadcast_step(
                    'AGENT', bod_agent.display_name if bod_agent else 'BOD CEO', target_agent, intent_code,
                    quick_msg, 'Tổng Giám Đốc Điều Hành', bod_agent.avatar_url if bod_agent else ''
                )
                return

            # 5. BOD ĐIỀU PHỐI & GIAO VIỆC TRỰC TIẾP TRÊN KHUNG CHAT
            await self.broadcast_step(
                'AGENT', 'BOD CEO (Tổng Giám Đốc AI)', target_agent, 'PROGRESS',
                f"📋 **[BOD Phân công nhiệm vụ]** Nhận diện ý định `{intent_code}`. Giao đầu mối **{sender_name}** chủ trì thực thi và thu thập dữ liệu...",
                'Tổng Giám Đốc Điều Hành'
            )

            # 6. THỰC THI TOOL LẤY DỮ LIỆU THÔ (Raw Data)
            raw_data_context, status_note = await self.execute_intent_tools(intent_code, message, target_agent)

            # 7. TỔNG HỢP BÁO CÁO QUA OLLAMA (Cấu hình Timeout động & Map-Reduce cho Prompt dài)
            all_agents = await self.get_all_active_agents()
            agent_roster_str = "\n".join([f"- {ag.display_name} ({ag.agent_id}): {ag.domain_scope}" for ag in all_agents])
            historical_summary = await self.get_historical_context_summary()
            now_str = datetime.datetime.now().strftime("%H:%M:%S ngày %d/%m/%Y")

            system_prompt = (
                f"Bạn là {sender_name} ({assigned_agent.agent_id if assigned_agent else 'BOD_CEO_01'}) của tập đoàn vnxBox Enterprise.\n"
                f"Chuyên môn: {assigned_agent.domain_scope if assigned_agent else 'GLOBAL'}.\n"
                f"Thời gian hiện tại: {now_str}.\n"
                f"Ký ức phiên trước: [{historical_summary}].\n"
                f"Danh sách nhân sự hiện tại:\n{agent_roster_str}\n\n"
                f"DỮ LIỆU THÔ THỰC TẾ TỪ INTERNET / DATABASE:\n"
                f"{raw_data_context if raw_data_context else 'Không có dữ liệu thô bên ngoài.'}\n"
                f"TRẠNG THÁI THỰC THI: {status_note}\n\n"
                f"🛡️ QUY CHUẨN BÁO CÁO (ANTI-HALLUCINATION & PRAGMATIC RULES):\n"
                f"1. Luôn thưa 'Dạ Sếp {owner_name}' và xưng 'em'.\n"
                f"2. Dựa vào [DỮ LIỆU THÔ] ở trên để tổng hợp thông tin trả lời Sếp. Tuyệt đối không bịa đặt số liệu hay sự việc không có trong dữ liệu thô.\n"
                f"3. Nếu dữ liệu thô quá ít hoặc không đủ thông tin, hãy báo cáo trung thực: 'Dạ Sếp, em đã tra cứu nhưng dữ liệu hiện tại chưa có thông tin chi tiết về vấn đề này' và tóm tắt những gì tìm được (nếu có).\n"
                f"4. Trình bày rõ ràng, mạch lạc, chuyên nghiệp theo phong cách báo cáo điều hành của Tổng Giám Đốc AI."
            )

            await self.broadcast_step(
                'SYSTEM', 'Hệ thống vnxBox', target_agent, 'PROGRESS',
                f"🧠 [{sender_name}] đang tổng hợp dữ liệu và soạn thảo báo cáo trình Sếp...", 'AI Synthesis'
            )

            llm_timeout = 480 if intent_code == 'DEEP_CODE' else 120

            # Kích hoạt bộ xử lý Map-Reduce thông minh nếu prompt/spec dài hơn 2000 ký tự
            from enterprise_factory.services.long_prompt_handler import LongPromptHandler
            if len(message) > 2000:
                await self.broadcast_step(
                    'SYSTEM', 'Hệ thống vnxBox', target_agent, 'PROGRESS',
                    f"🧩 [LONG PROMPT CHUNKER] Phát hiện bản đặc tả lớn ({len(message)} ký tự). Đang bóc tách và chạy Map-Reduce...", 'Chunking Engine'
                )
                response_text = await LongPromptHandler.process_long_spec_via_map_reduce(system_prompt, message, timeout=llm_timeout)
            else:
                response_text = await self.call_llm_sync(system_prompt, message, timeout=llm_timeout)

            is_error_reply = False
            if not response_text or "[Lỗi:" in response_text or "TIMEOUT" in response_text or "timed out" in response_text:
                is_error_reply = True
                if not response_text or "timed out" in response_text:
                    response_text = f"Dạ báo cáo Sếp {owner_name}, tác vụ xử lý trên CPU mất nhiều thời gian nên Ollama đã đạt ngưỡng giới hạn thời gian chờ ({llm_timeout}s). Trạng thái: {status_note}"

            # 8. Lưu vào DB, chỉ cập nhật IntentMemory Cache nếu thành công và câu lệnh ngắn (<= 200 ký tự)
            await self.save_and_get_context('AGENT', response_text, agent_obj=assigned_agent)
            if not is_error_reply and intent_code not in ['WEB_SEARCH'] and len(message) <= 200:
                await sync_to_async(IntentCacheMiddleware.save_to_cache)(
                    query_text=message,
                    intent_code=intent_code,
                    target_agent=assigned_agent.agent_id if assigned_agent else 'BOD_CEO_01',
                    response_payload=response_text
                )

            await self.broadcast_step(
                'AGENT', sender_name, target_agent, intent_code,
                response_text, sender_title, assigned_agent.avatar_url if assigned_agent else ''
            )

        except Exception as e:
            logger.error(f"[-] [WS_ERROR] Lỗi xử lý message: {str(e)}", exc_info=True)
            await self.broadcast_step(
                'SYSTEM', 'Hệ thống vnxBox', 'ALL', 'PROGRESS',
                f"❌ [LỖI HỆ THỐNG]: {str(e)}", 'Exception Interceptor'
            )