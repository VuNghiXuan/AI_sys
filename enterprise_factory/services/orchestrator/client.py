# enterprise_factory/services/orchestrator/client.py
"""
Ollama Client Service cho vnxBox Enterprise.
Tích hợp Django Cache, xử lý timeout, options tối ưu cho code và logging chi tiết.
"""

import logging
import requests
import hashlib
from django.core.cache import cache
from .config_loader import ModelHardwareInspector

logger = logging.getLogger(__name__)


def ask_local_agent(system_prompt: str, user_prompt: str, timeout_seconds: int = 180) -> str:
    """
    Gửi prompt qua API /api/chat của Ollama Local-First với:
    1. Định dạng messages chuẩn (System + User).
    2. Cấu hình context & temperature tối ưu từ ModelHardwareInspector.
    3. Tích hợp Django Cache & Timeout linh hoạt.
    """
    ollama_host, model_name = ModelHardwareInspector.get_model_endpoint_and_name()
    url = f"{ollama_host}/api/chat"
    
    # Tạo mã hash từ system_prompt và user_prompt làm key cache
    cache_key = "ollama_chat_cache_" + hashlib.md5((system_prompt + user_prompt).encode('utf-8')).hexdigest()
    
    cached_response = cache.get(cache_key)
    if cached_response:
        logger.info(f"[+] [CACHE HIT] Lấy phản hồi có sẵn từ cache cho key: {cache_key[:10]}...")
        return cached_response

    options = ModelHardwareInspector.get_dynamic_ollama_options()
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "options": options,
        "stream": False
    }

    try:
        logger.info(f"[*] [OLLAMA CHAT] Đang gửi yêu cầu tới model {model_name} (Host: {ollama_host}, Timeout: {timeout_seconds}s)...")
        response = requests.post(url, json=payload, timeout=timeout_seconds)
        
        if response.status_code == 200:
            result = response.json()
            content = result.get('message', {}).get('content', '').strip()
            
            if content:
                cache.set(cache_key, content, timeout=3600)
                logger.info(f"[+] [OLLAMA SUCCESS] Nhận phản hồi thành công từ Ollama ({len(content)} ký tự). Đã cache kết quả.")
                return content
            else:
                logger.warning(f"[!] [OLLAMA WARNING] Ollama trả về status 200 nhưng nội dung phản hồi rỗng.")
                return "[Lỗi: Nhận được phản hồi rỗng từ Ollama]"
        else:
            err_msg = f"[Lỗi Ollama API: HTTP {response.status_code} - {response.text}]"
            logger.error(f"[-] [OLLAMA ERROR] {err_msg}")
            return err_msg
            
    except requests.exceptions.Timeout:
        err_msg = f"[Lỗi: Ollama xử lý quá thời gian cho phép ({timeout_seconds}s). Yêu cầu quá dài, Sếp hãy chia nhỏ lệnh nhé!]"
        logger.error(f"[-] [OLLAMA TIMEOUT] {err_msg}", exc_info=True)
        return err_msg
        
    except requests.exceptions.ConnectionError:
        err_msg = f"[Lỗi kết nối: Không thể kết nối tới Ollama local tại {ollama_host}!]"
        logger.error(f"[-] [OLLAMA CONNECTION ERROR] {err_msg}", exc_info=True)
        return err_msg
        
    except Exception as e:
        err_msg = f"[Lỗi hệ thống khi gọi LLM: {str(e)}]"
        logger.error(f"[-] [OLLAMA EXCEPTION] {err_msg}", exc_info=True)
        return err_msg