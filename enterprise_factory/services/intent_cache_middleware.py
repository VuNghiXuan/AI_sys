"""
Middleware IntentMemory Cache cho vnxBox Enterprise.
Tối ưu hóa tốc độ phản hồi bằng cách tra cứu bộ nhớ cache trước khi gọi LLM/Ollama.
"""

import logging
from django.utils import timezone
from enterprise_factory.models import IntentMemory

logger = logging.getLogger(__name__)

class IntentCacheMiddleware:
    """Quản lý bộ nhớ đệm ý định (Intent Semantic & Exact Match Cache)"""

    @staticmethod
    def get_cached_response(query_text: str, intent_code: str = None) -> str:
        """
        Tra cứu xem câu hỏi đã từng xuất hiện trong IntentMemory chưa.
        Nếu có, trả về kết quả ngay lập tức (Hit Cache).
        """
        cleaned_query = query_text.strip().lower()
        logger.debug(f"[*] [INTENT CACHE] Đang kiểm tra cache cho query: '{cleaned_query}' (Intent: {intent_code})")

        try:
            # Tìm kiếm theo exact match hoặc semantic/intent match
            query_set = IntentMemory.objects.filter(query_text__iexact=cleaned_query)
            if intent_code:
                query_set = query_set.filter(intent_code=intent_code)
                
            cached_record = query_set.first()
            if cached_record:
                logger.info(f"[+] [INTENT CACHE HIT] Tìm thấy kết quả trong bộ nhớ cho: '{cleaned_query}' -> Phản hồi lập tức (0.01s)")
                return cached_record.response_payload
                
        except Exception as e:
            logger.error(f"[-] [INTENT CACHE ERROR] Lỗi tra cứu cache: {str(e)}")

        logger.debug(f"[-] [INTENT CACHE MISS] Không tìm thấy cache cho: '{cleaned_query}'. Chuyển qua xử lý LLM/Agent.")
        return None

    @staticmethod
    def save_to_cache(query_text: str, intent_code: str, target_agent: str, response_payload: str):
        """
        Lưu vết cặp câu hỏi và câu trả lời hoàn hảo vào IntentMemory (Self-Learning).
        Đảm bảo cập nhật lại intent_code nếu có sự thay đổi thông minh từ router.
        """
        cleaned_query = query_text.strip()
        try:
            # Xác định tier tự động dựa vào intent_code mới
            tier = 3 if intent_code in ['DEEP_CODE', 'WEB_SEARCH'] else (2 if intent_code in ['DB_QUERY', 'STATUS_CHECK'] else 1)
            
            obj, created = IntentMemory.objects.update_or_create(
                query_text=cleaned_query,
                defaults={
                    'intent_code': intent_code or 'GENERAL_CHAT',
                    'tier': tier, # Cập nhật đúng tier mới (để WEB_SEARCH nhận diện đúng tier 3)
                    'target_agent': target_agent or 'BOD_CEO_01',
                    'response_payload': response_payload,
                    'updated_at': timezone.now()
                }
            )
            if created:
                logger.info(f"[+] [INTENT CACHE SAVE] Đã học và lưu mới ý định vào bộ nhớ: '{cleaned_query}' (Intent: {intent_code})")
            else:
                logger.info(f"[+] [INTENT CACHE UPDATE] Đã cập nhật lại cache cho ý định: '{cleaned_query}' -> Intent mới: {intent_code}")
        except Exception as e:
            logger.error(f"[-] [INTENT CACHE SAVE ERROR] Không thể lưu cache: {str(e)}")