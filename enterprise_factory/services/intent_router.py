"""
Intent Router Service cho vnxBox Enterprise.
Phân loại ý định của Sếp (Directive / Chat / Meeting / HR / Small Talk) 
để định tuyến phản hồi nhanh mà không cần qua DAG nặng nề nếu không cần thiết.
"""
import logging
import json
from enterprise_factory.services.orchestrator import ask_local_agent

logger = logging.getLogger(__name__)


class IntentRouter:
    """Bộ định tuyến ý định động cho BOD CEO"""

    INTENT_CATEGORIES = {
        "SMALL_TALK": "Chào hỏi, trò chuyện phím, hỏi thăm xã giao.",
        "MEETING_CALL": "Triệu tập họp, gọi nhân viên, điểm danh hoặc mở phòng họp.",
        "HR_RECRUIT": "Tuyển dụng nhân sự mới, kiểm tra danh sách chuyên gia.",
        "BUSINESS_DEBATE": "Tranh luận nghiệp vụ, phân tích chiến lược, yêu cầu phân rã công việc.",
        "CODE_TASK": "Yêu cầu viết code, sửa bug, tạo app hoặc phân tích kỹ thuật."
    }

    @staticmethod
    def classify(directive_text: str) -> dict:
        """
        Sử dụng LLM phân tích nhanh ý định của Sếp dựa trên bộ danh mục.
        Trả về JSON gồm intent_code và action_hint.
        """
        logger.info(f"[*] [INTENT_ROUTER] Đang phân tích ý định cho câu lệnh: '{directive_text}'")
        
        system_prompt = (
            "Bạn là Intent Router của vnxBox Enterprise.\n"
            "Nhiệm vụ: Phân loại ý định của Sếp vào một trong các mã sau:\n"
            f"{json.dumps(IntentRouter.INTENT_CATEGORIES, ensure_ascii=False, indent=2)}\n\n"
            "BẮT BUỘC TRẢ VỀ ĐỊNH DẠNG JSON CHUẨN (KHÔNG KÈM MARKDOWN NÀO KHÁC):\n"
            "{\n"
            "  \"intent_code\": \"SMALL_TALK | MEETING_CALL | HR_RECRUIT | BUSINESS_DEBATE | CODE_TASK\",\n"
            "  \"target_agent_hint\": \"Mã agent cần gọi nếu có (VD: BOD_CEO_01, HR_MANAGER_01, ALL hoặc NONE)\",\n"
            "  \"quick_response\": \"Câu trả lời ngắn gọn nếu là chào hỏi/phím, hoặc để trống nếu cần thực thi DAG\"\n"
            "}"
        )

        try:
            raw_resp = ask_local_agent(system_prompt, f"Chỉ đạo từ Sếp: {directive_text}")
            cleaned = raw_resp.strip()
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned:
                cleaned = cleaned.split("```")[1].split("```")[0].strip()

            result = json.loads(cleaned)
            logger.info(f"[+] [INTENT_ROUTER] Phân tích thành công Intent: {result.get('intent_code')}")
            return result
        except Exception as e:
            logger.error(f"[-] [INTENT_ROUTER ERROR] Lỗi phân loại intent, fallback về BUSINESS_DEBATE: {str(e)}", exc_info=True)
            return {
                "intent_code": "BUSINESS_DEBATE",
                "target_agent_hint": "BOD_CEO_01",
                "quick_response": ""
            }

# Bổ sung ở cuối file intent_router.py
def classify_user_intent(directive_text: str) -> dict:
    return IntentRouter.classify(directive_text)