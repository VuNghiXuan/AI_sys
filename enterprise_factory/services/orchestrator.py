# File: enterprise_factory/services/orchestrator.py
import requests
import json
import hashlib
from django.core.cache import cache

OLLAMA_HOST = "http://localhost:11434"
MODEL_NAME = "qwen2.5-coder:7b-instruct"  # Hoặc "qwen2.5:7b" tùy Sếp cấu hình

def ask_local_agent(system_prompt, user_prompt, timeout_seconds=180):
    """
    Gửi prompt qua API /api/chat của Ollama Local-First với:
    1. Định dạng messages chuẩn (System + User).
    2. Cấu hình context & temperature tối ưu cho lập trình.
    3. Tích hợp Django Cache & Timeout linh hoạt (mặc định 180s).
    """
    url = f"{OLLAMA_HOST}/api/chat"
    
    # Tạo mã hash từ system_prompt và user_prompt làm key cache
    cache_key = "ollama_chat_cache_" + hashlib.md5((system_prompt + user_prompt).encode('utf-8')).hexdigest()
    
    # Kiểm tra cache (lưu trong 1 giờ)
    cached_response = cache.get(cache_key)
    if cached_response:
        print("[*] [CACHE HIT] Lấy phản hồi có sẵn từ cache, không gọi lại Ollama!")
        return cached_response

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "options": {
            "num_ctx": 4096,
            "temperature": 0.2
        },
        "stream": False
    }

    try:
        print(f"[*] [OLLAMA CHAT] Đang gửi yêu cầu tới model {MODEL_NAME} (Timeout: {timeout_seconds}s)...")
        response = requests.post(url, json=payload, timeout=timeout_seconds)
        
        if response.status_code == 200:
            result = response.json()
            content = result.get('message', {}).get('content', '').strip()
            
            if content:
                # Lưu vào cache để tối ưu cho các lần hỏi tương tự
                cache.set(cache_key, content, timeout=3600)
                return content
            else:
                return "[Lỗi: Nhận được phản hồi rỗng từ Ollama]"
        else:
            return f"[Lỗi Ollama API: HTTP {response.status_code}]"
            
    except requests.exceptions.Timeout:
        return f"[Lỗi: Ollama xử lý quá thời gian cho phép ({timeout_seconds}s). Yêu cầu quá dài, Sếp hãy chia nhỏ lệnh nhé!]"
    except requests.exceptions.ConnectionError:
        return "[Lỗi kết nối: Không thể kết nối tới Ollama local. Hãy đảm bảo ứng dụng Ollama đang chạy!]"
    except Exception as e:
        return f"[Lỗi hệ thống khi gọi LLM: {str(e)}]"