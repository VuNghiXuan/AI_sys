"""
Orchestration & Ollama Client Service cho vnxBox Enterprise.
Tích hợp Django Cache, xử lý timeout, options tối ưu cho code (temperature=0.2),
Unified Agent Runner và Hệ thống Logging chuẩn Enterprise.
"""
import logging
import requests
import json
import hashlib
from django.core.cache import cache
from django.conf import settings
from enterprise_factory.models import AgentRegistry

# Khởi tạo logger chuyên dụng cho module orchestrator
logger = logging.getLogger(__name__)

# Lấy cấu hình từ settings hoặc fallback về giá trị mặc định chuẩn Local-First
OLLAMA_HOST = getattr(settings, 'OLLAMA_HOST', 'http://localhost:11434')
MODEL_NAME = getattr(settings, 'OLLAMA_MODEL', 'qwen2.5-coder:7b-instruct')


def ask_local_agent(system_prompt: str, user_prompt: str, timeout_seconds: int = 180) -> str:
    """
    Gửi prompt qua API /api/chat của Ollama Local-First với:
    1. Định dạng messages chuẩn (System + User).
    2. Cấu hình context & temperature tối ưu cho lập trình.
    3. Tích hợp Django Cache & Timeout linh hoạt (mặc định 180s).
    4. Logging toàn diện để trace lỗi kết nối/Ollama.
    """
    url = f"{OLLAMA_HOST}/api/chat"
    
    # Tạo mã hash từ system_prompt và user_prompt làm key cache
    cache_key = "ollama_chat_cache_" + hashlib.md5((system_prompt + user_prompt).encode('utf-8')).hexdigest()
    
    # Kiểm tra cache (lưu trong 1 giờ)
    cached_response = cache.get(cache_key)
    if cached_response:
        logger.info(f"[+] [CACHE HIT] Lấy phản hồi có sẵn từ cache cho key: {cache_key[:10]}..., không gọi lại Ollama.")
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
        logger.info(f"[*] [OLLAMA CHAT] Đang gửi yêu cầu tới model {MODEL_NAME} (Host: {OLLAMA_HOST}, Timeout: {timeout_seconds}s)...")
        logger.debug(f"[DEBUG] System Prompt length: {len(system_prompt)} chars | User Prompt length: {len(user_prompt)} chars")
        
        response = requests.post(url, json=payload, timeout=timeout_seconds)
        
        if response.status_code == 200:
            result = response.json()
            content = result.get('message', {}).get('content', '').strip()
            
            if content:
                # Lưu vào cache để tối ưu cho các lần hỏi tương tự (1 giờ)
                cache.set(cache_key, content, timeout=3600)
                logger.info(f"[+] [OLLAMA SUCCESS] Nhận phản hồi thành công từ Ollama ({len(content)} ký tự). Đã cache kết quả.")
                return content
            else:
                logger.warning(f"[!] [OLLAMA WARNING] Ollama trả về status 200 nhưng nội dung phản hồi rỗng (content is empty).")
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
        err_msg = "[Lỗi kết nối: Không thể kết nối tới Ollama local. Hãy đảm bảo ứng dụng Ollama đang chạy tại " + OLLAMA_HOST + "!]"
        logger.error(f"[-] [OLLAMA CONNECTION ERROR] {err_msg}", exc_info=True)
        return err_msg
        
    except Exception as e:
        err_msg = f"[Lỗi hệ thống khi gọi LLM: {str(e)}]"
        logger.error(f"[-] [OLLAMA EXCEPTION] {err_msg}", exc_info=True)
        return err_msg


def execute_agent_task(agent_id: str, directive_text: str, context_data: dict = None) -> str:
    """
    Hàm thực thi thống nhất cho mọi Agent (Unified Agent Runner).
    Truy vấn thẳng hồ sơ từ DB qua Foreign Key role, lấy System Prompt động và gọi Ollama.
    Kèm theo hệ thống ghi log chi tiết từng bước.
    """
    logger.info(f"[*] [AGENT_RUNNER] Bắt đầu thực thi tác vụ cho Agent ID: '{agent_id}' | Chỉ đạo: '{directive_text}'")
    
    try:
        # 1. Truy vấn thẳng hồ sơ từ Database (Không hardcode)
        logger.debug(f"[*] [AGENT_RUNNER] Đang truy vấn hồ sơ AgentRegistry cho ID: {agent_id}...")
        agent_profile = AgentRegistry.objects.select_related('role').filter(agent_id=agent_id).first()
        
        if not agent_profile:
            logger.warning(f"[!] [AGENT_RUNNER] Không tìm thấy agent_id '{agent_id}'. Đang thử fallback về role 'BOD'...")
            # Fallback về BOD thông qua role động
            agent_profile = AgentRegistry.objects.select_related('role').filter(role__role_code='BOD').first()
            
            if not agent_profile:
                err_msg = f"Hệ thống chưa khởi tạo nhân sự nào trong DB! Không tìm thấy agent_id: {agent_id} lẫn BOD fallback."
                logger.error(f"[-] [AGENT_RUNNER FATAL] {err_msg}")
                raise ValueError(err_msg)
            else:
                logger.info(f"[+] [AGENT_RUNNER] Fallback thành công. Sử dụng Agent BOD: {agent_profile.agent_id} ({agent_profile.display_name})")
        else:
            role_code = agent_profile.role.role_code if agent_profile.role else 'N/A'
            logger.info(f"[+] [AGENT_RUNNER] Đã định danh nhân sự thành công: {agent_profile.display_name} (Role: {role_code})")

        # 2. Lấy System Prompt chuẩn của chính nhân sự đó từ DB
        system_prompt = agent_profile.system_prompt or f"Bạn là {agent_profile.display_name} tại vnxBox Enterprise."
        
        if context_data:
            logger.debug(f"[*] [AGENT_RUNNER] Đã đính kèm thêm bối cảnh dữ liệu (context_data) vào System Prompt.")
            system_prompt += f"\n\nBỐI CẢNH DỮ LIỆU BỔ SUNG:\n{str(context_data)}"

        # 3. Thực thi qua LLM local
        logger.info(f"[*] [AGENT_RUNNER] Đang gửi yêu cầu gọi Ollama cho Agent [{agent_profile.display_name}]...")
        response = ask_local_agent(system_prompt, f"Nhiệm vụ / Chỉ đạo: {directive_text}")
        
        logger.info(f"[+] [AGENT_RUNNER] Hoàn thành tác vụ cho Agent [{agent_id}]. Phản hồi nhận được dài {len(response) if response else 0} ký tự.")
        return response

    except Exception as e:
        logger.error(f"[-] [AGENT_RUNNER ERROR] Lỗi ngoại lệ trong execute_agent_task (Agent ID: {agent_id}): {str(e)}", exc_info=True)
        raise e