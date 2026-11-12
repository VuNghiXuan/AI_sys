# File: enterprise_factory/intent_router.py
import re
import logging

logger = logging.getLogger(__name__)

class IntentRouter:
    """
    Bộ định tuyến ý định thông minh tối giản:
    - Tier 2 (DB_QUERY): Truy vấn dữ liệu nhân sự/trạng thái trực tiếp từ SQLite (0ms).
    - Tier 3 (DEEP_CODE): Chỉ đạo lập trình, kiến trúc, sửa lỗi -> Chạy DAG & Sandbox.
    - Tier 1 (LLM_CHAT): Mọi câu hỏi giao tiếp, gõ sai chính tả, hỏi ngoài lề -> Gọi Ollama trả lời tự nhiên.
    """

    DB_PATTERNS = [
        r"nhân sự", r"nhân viên", r"bao nhiêu người", r"mấy người", r"nao nhiêu",
        r"thành phần", r"có ai", r"nhiệm vụ", r"ai làm gì", r"danh sách", r"trạng thái"
    ]

    CODE_PATTERNS = [
        r"viết code", r"lập trình", r"tạo app", r"xây dựng", r"sửa lỗi", r"fix bug",
        r"model", r"database", r"api", r"dag", r"neo4j", r"cosine", r"search", r"vibercode", r"triển khai"
    ]

    @classmethod
    def route(cls, user_message: str) -> dict:
        if not user_message:
            return {"tier": 1, "intent_code": "LLM_CHAT", "intent_type": "LLM_CHAT"}

        msg_lower = user_message.lower().strip()

        # 1. Ưu tiên bắt lệnh lập trình / kỹ thuật chuyên sâu -> Tầng 3
        if any(re.search(pat, msg_lower) for pat in cls.CODE_PATTERNS):
            return {"tier": 3, "intent_code": "DEEP_CODE", "intent_type": "DEEP_CODE"}

        # 2. Bắt truy vấn dữ liệu nhân sự / hệ thống -> Tầng 2
        if any(re.search(pat, msg_lower) for pat in cls.DB_PATTERNS):
            return {"tier": 2, "intent_code": "DB_QUERY", "intent_type": "DB_QUERY"}

        # 3. Toàn bộ các câu hỏi còn lại (chào hỏi, gõ sai chính tả, hỏi thời tiết, thảo luận tự do) -> Tầng 1 (Gọi Ollama)
        return {"tier": 1, "intent_code": "LLM_CHAT", "intent_type": "LLM_CHAT"}

    @classmethod
    def classify(cls, user_message: str) -> dict:
        return cls.route(user_message)

    # Thêm đoạn này vào cuối file enterprise_factory/intent_router.py

def classify_user_intent(user_message: str) -> str:
    """Hàm wrapper tương thích ngược cho views.py hoặc các module cũ."""
    result = IntentRouter.route(user_message)
    return result.get("intent_type", "DEEP_CODE")