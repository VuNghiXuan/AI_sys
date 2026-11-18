"""
# File Path: core/ollama_client.py
# File Purpose: Giao tiếp trực tiếp với Ollama Local API để truyền prompt và nhận phản hồi sinh mã 
#               từ Local LLM với timeout được cấu hình tối ưu cho CPU.
# Connected Files: [core/agent_executor.py, agents/coder_agent.json]
# Logs: Ghi log trạng thái kết nối Ollama, thời gian phản hồi và nội dung sinh mã.
"""

import logging
import requests
from typing import Dict, Any, Optional

# Thiết lập hệ thống Logging tiêu chuẩn cho vnxBox
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] - %(message)s"
)
logger = logging.getLogger("vnxBox.OllamaClient")

class OllamaClient:
    """
    # Class: OllamaClient
    # Purpose: Quản lý kết nối HTTP tới Ollama API chạy local-first (port 11434).
    """
    def __init__(self, base_url: str = "http://localhost:11434", default_model: str = "qwen2.5-coder"):
        self.base_url = base_url
        self.default_model = default_model
        logger.info(f"[OLLAMA_CLIENT] Khởi tạo kết nối Ollama tại {base_url} với model mặc định: {default_model}")

    def generate_code(self, system_prompt: str, user_prompt: str, model: Optional[str] = None) -> str:
        """
        # Function: generate_code
        # Purpose: Gửi yêu cầu sinh mã nguồn tới Ollama API với timeout 300s.
        """
        target_model = model or self.default_model
        url = f"{self.base_url}/api/generate"
        
        combined_prompt = f"System: {system_prompt}\n\nUser: {user_prompt}"
        
        payload = {
            "model": target_model,
            "prompt": combined_prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_ctx": 4096
            }
        }
        
        logger.info(f"[OLLAMA_CLIENT] Đang gửi yêu cầu tới Ollama (Model: {target_model})...")
        
        try:
            # Tăng timeout lên 300 giây để phù hợp với phần cứng CPU-only
            response = requests.post(url, json=payload, timeout=300)
            if response.status_code == 200:
                data = response.json()
                generated_text = data.get("response", "")
                logger.info("[OLLAMA_CLIENT] Nhận phản hồi thành công từ Ollama Local LLM.")
                return generated_text
            else:
                err_msg = f"Ollama Error Status {response.status_code}: {response.text}"
                logger.error(f"[OLLAMA_CLIENT] {err_msg}")
                return f"# Error: {err_msg}"
        except requests.exceptions.ConnectionError:
            err_msg = "Không thể kết nối tới Ollama server tại http://localhost:11434. Hãy đảm bảo ứng dụng Ollama đang chạy."
            logger.error(f"[OLLAMA_CLIENT] {err_msg}")
            return f"# Error: {err_msg}"
        except Exception as e:
            logger.error(f"[OLLAMA_CLIENT] Lỗi ngoại lệ khi gọi Ollama: {e}")
            return f"# Error: {str(e)}"