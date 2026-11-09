# Path: enterprise_factory/services.py
import os
import ast
import json
import subprocess
import requests
from .models import AgentRegistry, ProjectNode, AgentTaskDAG

OLLAMA_API_URL = "http://localhost:11434/api/generate"

class ViberEnterpriseOrchestrator:
    def __init__(self):
        # Khớp chính xác tên model từ 'ollama list' của Sếp
        self.model_code = "qwen2.5-coder:7b-instruct"
        self.model_chat = "qwen2.5:7b"

    def call_ollama(self, prompt: str, system_prompt: str = "", is_code: bool = False) -> str:
        """Gửi yêu cầu tới Ollama local với cấu hình tối ưu CPU (keep_alive, num_ctx)."""
        payload = {
            "model": self.model_code if is_code else self.model_chat,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "options": {
                "num_ctx": 4096,
                "temperature": 0.2 if is_code else 0.7
            },
            "keep_alive": -1
        }
        try:
            response = requests.post(OLLAMA_API_URL, json=payload, timeout=180) # Tăng timeout lên 3 phút cho CPU local
            if response.status_code == 200:
                return response.json().get("response", "")
        except Exception as e:
            return f"❌ Lỗi kết nối Ollama local: {str(e)}"
        return "❌ Không nhận được phản hồi từ Ollama."

    def spawn_agent_if_needed(self, domain_name: str) -> AgentRegistry:
        """[HR Spawner] Tự động tuyển dụng và sinh System Prompt cho nhân viên AI mới nếu chưa có."""
        agent_id = f"BIZ_{domain_name.upper()[:10]}_01"
        agent, created = AgentRegistry.objects.get_or_create(
            agent_id=agent_id,
            defaults={
                "display_name": f"Chuyên gia {domain_name}",
                "department": "Khối Nghiệp vụ Đa ngành",
                "role_desc": f"Phân tích chuyên sâu và cung cấp quy tắc nghiệp vụ về {domain_name}.",
                "system_prompt": f"Bạn là Chuyên gia {domain_name} thuộc Tập đoàn AI vnxBox Enterprise. Nhiệm vụ của bạn là bóc tách quy chế, định mức và cung cấp thuật toán chính xác tuyệt đối."
            }
        )
        return agent

    def run_secure_sandbox(self, file_path: str) -> dict:
        """[Secure Sandbox] Thực thi kiểm định an toàn mã Python qua ast và subprocess giới hạn."""
        if not os.path.exists(file_path):
            return {"status": "ERROR", "message": "File không tồn tại."}
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code_content = f.read()
            
            tree = ast.parse(code_content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        if alias.name in ['os', 'sys', 'subprocess', 'socket', 'requests']:
                            return {"status": "FAILED", "message": f"Phát hiện module cấm tuyệt đối trong Sandbox: {alias.name}"}
            
            result = subprocess.run(
                ["python", file_path],
                capture_output=True,
                text=True,
                timeout=3
            )
            return {
                "status": "SUCCESS" if result.returncode == 0 else "FAILED",
                "output": result.stdout,
                "error": result.stderr
            }
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}

    def run_secure_sandbox(self, file_path: str) -> dict:
        """[Secure Sandbox] Thực thi kiểm định an toàn mã Python qua ast và subprocess giới hạn."""
        if not os.path.exists(file_path):
            return {"status": "ERROR", "message": "File không tồn tại."}
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code_content = f.read()
            
            # Kiểm tra tĩnh AST chống module nguy hiểm
            tree = ast.parse(code_content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        if alias.name in ['os', 'sys', 'subprocess', 'socket', 'requests']:
                            return {"status": "FAILED", "message": f"Phát hiện module cấm tuyệt đối trong Sandbox: {alias.name}"}
            
            # Chạy thử nghiệm với giới hạn thời gian
            result = subprocess.run(
                ["python", file_path],
                capture_output=True,
                text=True,
                timeout=3
            )
            return {
                "status": "SUCCESS" if result.returncode == 0 else "FAILED",
                "output": result.stdout,
                "error": result.stderr
            }
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}