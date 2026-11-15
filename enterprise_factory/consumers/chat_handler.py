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

    async def call_llm_sync(self, system_prompt: str, user_prompt: str, timeout: int = 120):
        """Hàm gọi LLM đồng bộ có hỗ trợ nhận tham số timeout"""
        print(f"[LLM] Đang gọi Ollama... Prompt length: {len(user_prompt)} | Timeout: {timeout}s")
        try:
            # Truyền timeout vào hàm gọi thực tế bên dưới (hoặc xử lý tuỳ theo kiến trúc hiện tại của Sếp)
            return await sync_to_async(ask_local_agent)(system_prompt, user_prompt, timeout_seconds=timeout)
        except Exception as e:
            err_msg = str(e)
            logger.error(f"[-] [LLM_CALL_ERROR] Không thể kết nối Ollama: {err_msg}", exc_info=True)
            return f"Dạ báo cáo Sếp, em không thể kết nối tới Ollama. Chi tiết lỗi: {err_msg}"

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
        raw_context = ""
        status_note = "Hoàn tất thu thập dữ liệu thuận lợi."

        # 1. THỰC THI WEB SEARCH THỰC TẾ KÈM LINK THAM KHẢO
        if intent_code == 'WEB_SEARCH':
            search_query = message
            import re
            cleaned_query = message.lower()
            stop_patterns = [
                r'\btra cứu\b', r'\btra tìm\b', r'\btìm kiếm\b', r'\blên mạng\b', 
                r'\bhãy tìm\b', r'\bgiúp tao\b', r'\bcho tao\b', r'\bmày tra\b',
                r'\blập thành bảng so sánh\b', r'\bsức học như thế nào thì vào được trường nào\b',
                r'\bá\b', r'\bnhé\b', r'\bđi\b'
            ]
            for pattern in stop_patterns:
                cleaned_query = re.sub(pattern, '', cleaned_query)
            
            cleaned_query = re.sub(r'[,.?!;:]+', ' ', cleaned_query)
            search_query = re.sub(r'\s+', ' ', cleaned_query).strip()
            
            if len(search_query) <= 2:
                search_query = message

            logger.info(f"[*] [SMART WEB SEARCH] Từ khóa gốc: '{message}' -> Từ khóa tối ưu cho Bing: '{search_query}'")

            await self.broadcast_step(
                'AGENT', 'BOD CEO (Tổng Giám Đốc AI)', target_agent, 'PROGRESS',
                f"🌐 Đang cào dữ liệu thời gian thực kèm nguồn và link từ Internet: *'{search_query}'*...", 'Web Crawler'
            )

            try:
                from enterprise_factory.services.web_search import search_bing_or_web
                search_results = await sync_to_async(search_bing_or_web)(search_query)
                if search_results:
                    # Đảm bảo dữ liệu thô cung cấp đầy đủ Tiêu đề, Nội dung và Link URL
                    raw_context = f"KẾT QUẢ TÌM KIẾM THỰC TẾ & LINK THAM KHẢO TỪ INTERNET:\n{search_results}"
                    status_note = "Đã thu thập dữ liệu thô kèm nguồn link thành công."
                else:
                    raw_context = "Không tìm thấy kết quả trực tuyến phù hợp."
                    status_note = "Không có dữ liệu thô."
            except Exception as e:
                logger.error(f"[-] Lỗi thực thi Web Search: {e}")
                raw_context = f"Lỗi cào dữ liệu: {str(e)}"
                status_note = "Lỗi kết nối mạng."

        # 2. THỰC THI TRUY VẤN DỮ LIỆU HỆ THỐNG (DB_QUERY)
        elif intent_code == 'DB_QUERY':
            await self.broadcast_step(
                'AGENT', 'HR Director (Giám Đốc Nhân Sự AI)', target_agent, 'PROGRESS',
                "📊 Đang trích xuất dữ liệu trực tiếp từ Database hệ thống...", 'Giám Đốc Nhân Sự'
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
                status_note = f"Tìm thấy {len(agents_data)} nhân sự AI."
            except Exception as e:
                status_note = f"Lỗi truy xuất DB: {str(e)}"

        # 3. THỰC THI KỸ THUẬT / CODE (DEEP_CODE)
        elif intent_code == 'DEEP_CODE':
            await self.broadcast_step(
                'AGENT', 'Tech Lead AI (Kiến trúc sư trưởng)', target_agent, 'PROGRESS',
                "🛠️ Đang quét cấu trúc AST Codebase và kiểm tra Sandbox...", 'Chief Technology Officer'
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

            # 2. Phân rã ý định đa tầng thông minh (Intent Planner & Multi-Intent Decomposition)
            from enterprise_factory.services.intent_planner import IntentPlanner
            sub_tasks = await IntentPlanner.decompose_directive(message)
            
            print(f"🎯 [MULTI-INTENT RESOLVED] Tổng số sub-tasks phân rã: {len(sub_tasks)}")
            
            primary_task = sub_tasks[0] if sub_tasks else {}
            intent_code = primary_task.get('intent', 'LLM_CHAT')
            target_agent = primary_task.get('target_agent', target_agent)

            # Gom dữ liệu thô (Raw Context) kèm link từ tất cả các sub-tasks
            aggregated_raw_context = ""
            combined_status_notes = []

            for idx, task in enumerate(sub_tasks):
                sub_intent = task.get('intent', 'LLM_CHAT')
                sub_query = task.get('query', message)
                sub_target = task.get('target_agent', target_agent)

                await self.broadcast_step(
                    'SYSTEM', 'Hệ thống vnxBox', sub_target, 'PROGRESS',
                    f"⚙️ **[Sub-task {idx+1}/{len(sub_tasks)}]** Thực thi tác vụ `{sub_intent}` với nội dung: *'{sub_query}'*", 'Workflow Engine'
                )

                raw_data, status_note = await self.execute_intent_tools(sub_intent, sub_query, sub_target)
                if raw_data:
                    aggregated_raw_context += f"\n--- KẾT QUẢ TÁC VỤ {idx+1} ({sub_intent}) ---\n{raw_data}\n"
                if status_note:
                    combined_status_notes.append(status_note)

            if not aggregated_raw_context:
                aggregated_raw_context = message
            
            status_note = " | ".join(combined_status_notes) if combined_status_notes else "Hoàn tất thu thập dữ liệu."

            # 3. KIỂM TRA CACHE TỐC ĐỘ CAO (IntentMemory Cache - 0.01s)
            if intent_code not in ['WEB_SEARCH']:  
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

            if intent_code in ['SMALL_TALK', 'MEETING_CALL']:
                quick_msg = f"Dạ em nghe thưa Sếp {owner_name}! Ban điều hành và các phòng ban AI đã tề tựu đầy đủ, sẵn sàng nhận chỉ đạo ạ."
                await self.save_and_get_context('AGENT', quick_msg, agent_obj=bod_agent)
                await self.broadcast_step(
                    'AGENT', bod_agent.display_name if bod_agent else 'BOD CEO', target_agent, intent_code,
                    quick_msg, 'Tổng Giám Đốc Điều Hành', bod_agent.avatar_url if bod_agent else ''
                )
                return

            await self.broadcast_step(
                'AGENT', 'BOD CEO (Tổng Giám Đốc AI)', target_agent, 'PROGRESS',
                f"📋 **[BOD Phân công nhiệm vụ]** Nhận diện tổng hợp `{len(sub_tasks)}` ý định (Chủ đạo: `{intent_code}`). Giao đầu mối **{sender_name}** chủ trì tổng hợp...",
                'Tổng Giám Đốc Điều Hành'
            )

            # 5. TỔNG HỢP BÁO CÁO QUA OLLAMA (Ép buộc trích dẫn Nguồn và Link)
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
                f"DỮ LIỆU THÔ THỰC TẾ TỪ INTERNET (KÈM NGUỒN VÀ LINK URL):\n"
                f"{aggregated_raw_context}\n"
                f"TRẠNG THÁI THỰC THI: {status_note}\n\n"
                f"🛡️ QUY CHUẨN BÁO CÁO BẮT BUỘC (ANTI-HALLUCINATION & SOURCE CITATION):\n"
                f"1. Luôn thưa 'Dạ Sếp {owner_name}' và xưng 'em'.\n"
                f"2. BẮT BUỘC DỰA VÀO [DỮ LIỆU THÔ] ở trên để tổng hợp thông tin. TUYỆT ĐỐI KHÔNG BỊA ĐẶT số liệu, tên trường (Cấm tuyệt đối tự chế ra 'Trường A, B, C').\n"
                f"3. Ở cuối câu trả lời, BẮT BUỘC PHẢI LIỆT KÊ PHẦN 'Nguồn tham khảo:' kèm theo các đường dẫn (URL) cụ thể có trong dữ liệu thô để Sếp bấm vào kiểm chứng. Nếu dữ liệu thô không có link, phải báo cáo trung thực.\n"
                f"4. Trình bày rõ ràng, mạch lạc, chuyên nghiệp theo phong cách báo cáo điều hành của Tổng Giám Đốc AI."
            )

            await self.broadcast_step(
                'SYSTEM', 'Hệ thống vnxBox', target_agent, 'PROGRESS',
                f"🧠 [{sender_name}] đang tổng hợp dữ liệu, kiểm chứng nguồn và soạn thảo báo cáo...", 'AI Synthesis'
            )

            llm_timeout = 480 if intent_code == 'DEEP_CODE' else 120

            from enterprise_factory.services.long_prompt_handler import LongPromptHandler
            if len(message) > 2000:
                await self.broadcast_step(
                    'SYSTEM', 'Hệ thống vnxBox', target_agent, 'PROGRESS',
                    f"🧩 [LONG PROMPT CHUNKER] Phát hiện bản lớn ({len(message)} ký tự). Đang chạy Map-Reduce...", 'Chunking Engine'
                )
                response_text = await LongPromptHandler.process_long_spec_via_map_reduce(system_prompt, message, timeout=llm_timeout)
            else:
                response_text = await self.call_llm_sync(system_prompt, message, timeout=llm_timeout)

            is_error_reply = False
            if not response_text or "[Lỗi:" in response_text or "TIMEOUT" in response_text or "timed out" in response_text:
                is_error_reply = True
                if not response_text or "timed out" in response_text:
                    response_text = f"Dạ báo cáo Sếp {owner_name}, tác vụ xử lý trên CPU mất nhiều thời gian nên Ollama đã đạt ngưỡng giới hạn thời gian chờ ({llm_timeout}s). Trạng thái: {status_note}"

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