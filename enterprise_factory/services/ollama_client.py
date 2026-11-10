# File: enterprise_factory/services/ollama_client.py
import requests
import json
import re

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5-coder"

def ask_local_agent(system_prompt, user_prompt, extract_code=False):
    """
    Gọi mô hình Ollama chạy local để Agent tư duy và viết code.
    Nếu extract_code=True, hệ thống sẽ tự động bóc tách khối mã Python trong block ```python ... ```
    """
    payload = {
        "model": MODEL_NAME,
        "prompt": f"System Persona:\n{system_prompt}\n\nTask/Directive:\n{user_prompt}",
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 2048
        }
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        if response.status_code == 200:
            raw_response = response.json().get('response', '')
            
            if extract_code:
                # Tự động tìm và bóc code bên trong block ```python ... ```
                code_match = re.search(r"```(?:python)?\s*(.*?)```", raw_response, re.DOTALL)
                if code_match:
                    return code_match.group(1).strip()
                return raw_response.strip()
                
            return raw_response
        else:
            return f"⚠️ Lỗi Ollama API Status: {response.status_code}"
    except requests.exceptions.ConnectionError:
        return "⚠️ Không thể kết nối tới Ollama. Hãy chắc chắn 'ollama serve' đang chạy ngầm trên máy."