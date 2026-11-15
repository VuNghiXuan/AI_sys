"""
Hybrid Semantic Router (Nâng cấp Cosine Similarity) cho vnxBox Enterprise.
Kết hợp IntentMemory Lookup, Vector Cosine Similarity (TF Vectorizer cục bộ),
Dynamic Agent Registry Routing và Regex Fallback, chạy hoàn toàn offline trên CPU,
tốc độ mili-giây, không cần PyTorch/HuggingFace và an toàn tuyệt đối.
"""

import re
import json
import math
import logging
from collections import Counter

logger = logging.getLogger(__name__)

class HybridSemanticRouter:
    """
    Bộ định tuyến thông minh ứng dụng Cosine Similarity cho phòng họp chiến lược vnxBox Enterprise.
    """

    # Các mẫu câu nguyên mẫu (Prototypes) đại diện cho từng Intent để tính Cosine Similarity
    INTENT_PROTOTYPES = {
        "MEETING_CALL": [
            "họp đi", "vào họp lẹ", "triệu tập mọi người", "điểm danh phòng họp", "bắt đầu bàn bạc công việc"
        ],
        "STATUS_CHECK": [
            "tiến độ công việc thế nào", "tổng kết báo cáo dự án", "việc giao đã làm đến đâu rồi", 
            "liệt kê các vấn đề đang vướng mắc", "thống kê kết quả thực thi"
        ],
        "DB_QUERY": [
            "danh sách nhân sự hệ thống", "có bao nhiêu nhân viên AI", "quân số phòng ban gồm những ai", 
            "nhiệm vụ của từng người là gì", "trạng thái các tháp quản trị ra sao"
        ],
        "DEEP_CODE": [
            "viết code python cho api", "tạo app django", "xây dựng luồng dag", "sửa lỗi fix bug sandbox", 
            "triển khai mô hình ollama neo4j cosine search"
        ],
        "WEB_SEARCH": [
            "tra cứu thông tin thời sự", "tìm kiếm tin tức mới nhất", "lên mạng xem giá vàng ra sao", 
            "tra mạng vụ việc scandal hot", "tìm hiểu quy chế tuyển sinh bộ giáo dục văn bản thông tư"
        ]
    }

    # Regex patterns bổ trợ nhanh cho các nhóm ngắn gọn / xã giao / hài hước
    SMALL_TALK_PATTERNS = [r"^alo", r"^chào", r"^hi\b", r"^hello", r"ơi", r"có ai không", r"cảm ơn", r"ok", r"được đấy"]
    HUMOR_PATTERNS = [r"ngáo", r"đùa", r"ghê vậy", r"bốc phét", r"chém gió", r"tếu", r"cười", r"giỡn"]

    @classmethod
    def tokenize(cls, text: str) -> list:
        return re.findall(r'\w+', text.lower())

    @classmethod
    def get_term_frequency(cls, tokens: list) -> dict:
        counts = Counter(tokens)
        total = len(tokens) if tokens else 1
        return {term: count / total for term, count in counts.items()}

    @classmethod
    def cosine_similarity(cls, vec1: dict, vec2: dict) -> float:
        """Tính khoảng cách Cosine giữa 2 véc-tơ tần suất từ vựng (TF Vector)"""
        intersection = set(vec1.keys()) & set(vec2.keys())
        numerator = sum(vec1[x] * vec2[x] for x in intersection)
        
        sum1 = sum(v ** 2 for v in vec1.values())
        sum2 = sum(v ** 2 for v in vec2.values())
        
        if sum1 == 0 or sum2 == 0:
            return 0.0
        return numerator / (math.sqrt(sum1) * math.sqrt(sum2))

    @classmethod
    def semantic_match(cls, user_message: str) -> tuple[str, float]:
        """So khớp ý nghĩa câu của Sếp với các Intent Prototypes qua Cosine Similarity"""
        user_tokens = cls.tokenize(user_message)
        user_vec = cls.get_term_frequency(user_tokens)
        
        best_intent = "LLM_CHAT"
        max_score = 0.0
        
        for intent_code, prototypes in cls.INTENT_PROTOTYPES.items():
            for proto in prototypes:
                proto_tokens = cls.tokenize(proto)
                proto_vec = cls.get_term_frequency(proto_tokens)
                score = cls.cosine_similarity(user_vec, proto_vec)
                if score > max_score:
                    max_score = score
                    best_intent = intent_code
                    
        return best_intent, max_score

    @classmethod
    def route(cls, user_message: str) -> dict:
        if not user_message:
            return {"tier": 1, "intent_code": "LLM_CHAT", "target_agent": "BOD_CEO_01", "source": "default"}

        msg_clean = user_message.strip()
        msg_lower = msg_clean.lower()

        # 0. HARD KEYWORD OVERRIDE: Ưu tiên bắt các từ khóa hành động rõ ràng cho WEB_SEARCH
        # 0. HARD KEYWORD OVERRIDE (Mở rộng toàn diện cho Tra cứu thông tin, Thi cử, Điểm chuẩn, Sự kiện)
        web_search_triggers = [
            'tra cứu', 'tra tìm', 'tìm kiếm', 'lên mạng', 'vụ', 'scandal', 'scansal', 
            'facebook', 'mạng xã hội', 'tin tức', 'giá vàng', 'thông tin', 'sự việc', 'hôm nay',
            'bão', 'lụt', 'mưa', 'thời tiết', 'tuy hoà', 'tuy hòa', 'ngập', 'thiên tai',
            'thi đại học', 'điểm chuẩn', 'sinh năm', 'trường', 'ngành', 'tuyển sinh', 'đại học'
        ]
        
        # Nếu câu lệnh chứa các từ khóa đặc thù trên, ép cứng về WEB_SEARCH hoặc LLM_CHAT thông minh
        if any(kw in msg_lower for kw in web_search_triggers):
            # Nếu hỏi về điểm chuẩn, tuyển sinh, thi cử hoặc thông tin thời sự -> Ép sang WEB_SEARCH
            if any(term in msg_lower for term in ['điểm chuẩn', 'thi đại học', 'tuyển sinh', 'trường', 'ngành', 'bão', 'lụt', 'vụ', 'tin tức']):
                logger.info(f"⚡ [Hard Keyword Override] Ép cứng sang WEB_SEARCH cho câu tra cứu: '{msg_clean}'")
                return {"tier": 3, "intent_code": "WEB_SEARCH", "target_agent": "BOD_CEO_01", "source": "hard_keyword_override"}

        # 1. TRA CỨU TRONG BỘ NHỚ HỌC TẬP (IntentMemory Cache - 0.01s)
        try:
            from enterprise_factory.models import IntentMemory
            exact_match = IntentMemory.objects.filter(query_text__iexact=msg_clean).first()
            if exact_match:
                return {
                    "tier": exact_match.tier,
                    "intent_code": exact_match.intent_code,
                    "target_agent": exact_match.target_agent,
                    "source": "memory_exact"
                }

            memories = list(IntentMemory.objects.order_by('-updated_at')[:100])
            if memories:
                best_mem = None
                best_score = 0.0
                for mem in memories:
                    score = cls.compute_bm25_score(msg_clean, mem.query_text)
                    if score > best_score:
                        best_score = score
                        best_mem = mem
                
                if best_mem and best_score > 1.2:
                    return {
                        "tier": best_mem.tier,
                        "intent_code": best_mem.intent_code,
                        "target_agent": best_mem.target_agent,
                        "source": "memory_bm25"
                    }
        except Exception as e:
            logger.debug(f"IntentMemory lookup skipped: {e}")

        # 2. ĐỊNH TUYẾN ĐỘNG THEO CHUYÊN GIA MỚI SINH
        try:
            from enterprise_factory.models import AgentRegistry
            agents = AgentRegistry.objects.all()
            for agent in agents:
                scope = agent.domain_scope.lower()
                if scope and scope in msg_lower:
                    return {
                        "tier": 2,
                        "intent_code": "EXPERT_DIRECT_QUERY",
                        "target_agent": agent.agent_id,
                        "source": "dynamic_agent_registry"
                    }
        except Exception as e:
            logger.debug(f"Dynamic agent routing lookup skipped: {e}")

        # 3. BẮT LỆNH XÃ GIAO / HÀI HƯỚC NHANH (Chỉ áp dụng khi câu thực sự ngắn dưới 5 từ)
        word_count = len(msg_lower.split())
        if word_count <= 4:
            if any(re.search(pat, msg_lower) for pat in cls.SMALL_TALK_PATTERNS):
                return {"tier": 1, "intent_code": "SMALL_TALK", "target_agent": "BOD_CEO_01", "source": "rule_small_talk"}
            if any(re.search(pat, msg_lower) for pat in cls.HUMOR_PATTERNS):
                return {"tier": 1, "intent_code": "HUMOR_CHAT", "target_agent": "BOD_CEO_01", "source": "rule_humor"}

        # 4. ĐỊNH TUYẾN THÔNG MINH BẰNG COSINE SIMILARITY (Hạ ngưỡng xuống 0.12 để nhạy hơn)
        semantic_intent, cosine_score = cls.semantic_match(msg_clean)
        logger.info(f"📐 [Cosine Semantic Match] Intent: {semantic_intent} | Score: {cosine_score:.3f} | Query: '{msg_clean}'")

        if cosine_score >= 0.12:
            tier_map = {
                "MEETING_CALL": 1,
                "STATUS_CHECK": 2,
                "DB_QUERY": 2,
                "DEEP_CODE": 3,
                "WEB_SEARCH": 3
            }
            agent_map = {
                "MEETING_CALL": "BOD_CEO_01",
                "STATUS_CHECK": "BOD_CEO_01",
                "DB_QUERY": "HR_MANAGER_01",
                "DEEP_CODE": "ALL",
                "WEB_SEARCH": "BOD_CEO_01"
            }
            return {
                "tier": tier_map.get(semantic_intent, 1),
                "intent_code": semantic_intent,
                "target_agent": agent_map.get(semantic_intent, "BOD_CEO_01"),
                "source": f"cosine_semantic_{cosine_score:.2f}"
            }

        # 5. MẶC ĐỊNH: Giao tiếp linh hoạt -> Tầng 1 (LLM Chat)
        return {"tier": 1, "intent_code": "LLM_CHAT", "target_agent": "BOD_CEO_01", "source": "rule_chat"}