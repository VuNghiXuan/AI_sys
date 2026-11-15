"""
Intent Planner & Decomposer cho vnxBox Enterprise.
Chuyên phân tích các câu lệnh phức tạp, prompt dài hoặc chứa nhiều ý định lồng nhau
thành các tác vụ con (sub-tasks) để định tuyến chính xác tuyệt đối.
"""

import json
import logging
from asgiref.sync import sync_to_async
from enterprise_factory.services.orchestrator import ask_local_agent

logger = logging.getLogger(__name__)

class IntentPlanner:
    
    @classmethod
    async def decompose_directive(cls, user_message: str) -> list[dict]:
        """
        Sử dụng Qwen 7B làm bộ não phân rã câu lệnh của Sếp thành danh sách các sub-tasks.
        Trả về danh sách dạng: [{'intent': 'WEB_SEARCH', 'query': '...'}, {'intent': 'DB_QUERY', 'query': '...'}]
        """
        # Nếu câu lệnh ngắn hoặc đơn giản, chuyển qua HybridSemanticRouter truyền thống để tối ưu tốc độ (0.01s)
        if len(user_message.strip().split()) <= 6:
            from enterprise_factory.intent_router import IntentRouter
            single_route = IntentRouter.route(user_message)
            return [{
                "intent": single_route.get("intent_code", "LLM_CHAT"),
                "target_agent": single_route.get("target_agent", "BOD_CEO_01"),
                "query": user_message
            }]

        planner_system_prompt = (
            "Bạn là bộ điều phối ý định (Intent Planner) của vnxBox Enterprise.\n"
            "Nhiệm vụ của bạn là phân tích câu lệnh của Sếp (có thể dài hoặc chứa nhiều yêu cầu lồng nhau).\n"
            "Hãy phân rã câu lệnh thành tối đa 3 tác vụ con (sub-tasks) thuộc các loại sau:\n"
            "- WEB_SEARCH: Tra cứu thông tin thời sự, điểm chuẩn, giá cả, sự kiện ngoài internet.\n"
            "- DB_QUERY: Truy xuất dữ liệu nhân sự, công cụ, workflow nội bộ hệ thống.\n"
            "- DEEP_CODE: Viết code, sửa lỗi, phân tích cấu trúc mã nguồn.\n"
            "- LLM_CHAT: Trò chuyện chung, giải đáp kiến thức tổng quát, phân tích logic.\n\n"
            "BẮT BUỘC TRẢ VỀ ĐỊNH DẠNG JSON RAW CHUẨN (không kèm markdown thừa):\n"
            "[\n"
            "  {\"intent\": \"WEB_SEARCH\", \"target_agent\": \"BOD_CEO_01\", \"query\": \"từ khóa hoặc nội dung cần tra cứu\"},\n"
            "  {\"intent\": \"LLM_CHAT\", \"target_agent\": \"BOD_CEO_01\", \"query\": \"nội dung cần giải đáp\"}\n"
            "]"
        )

        try:
            logger.info(f"🧩 [INTENT PLANNER] Đang phân rã câu lệnh phức tạp ({len(user_message)} ký tự)...")
            response = await sync_to_async(ask_local_agent)(planner_system_prompt, user_message, timeout_seconds=30)
            
            # Làm sạch JSON output từ LLM
            clean_json_str = response.strip()
            if clean_json_str.startswith("```json"):
                clean_json_str = clean_json_str[7:]
            if clean_json_str.endswith("```"):
                clean_json_str = clean_json_str[:-3]
            clean_json_str = clean_json_str.strip()

            tasks = json.loads(clean_json_str)
            if isinstance(tasks, list) and len(tasks) > 0:
                logger.info(f"✅ [INTENT PLANNER SUCCESS] Đã phân rã thành {len(tasks)} sub-tasks.")
                return tasks
        except Exception as e:
            logger.warning(f"[-] [INTENT PLANNER FALLBACK] Lỗi parse JSON từ planner ({e}), fallback về router chuẩn.")

        # Fallback an toàn về Router chuẩn nếu LLM planner gặp sự cố
        from enterprise_factory.intent_router import IntentRouter
        fallback_route = IntentRouter.route(user_message)
        return [{
            "intent": fallback_route.get("intent_code", "LLM_CHAT"),
            "target_agent": fallback_route.get("target_agent", "BOD_CEO_01"),
            "query": user_message
        }]