# Path: core/viber_orchestrator.py
"""
Mục đích: Bộ điều phối trung tâm (Viber Orchestrator) tích hợp Ollama Local LLM.
Nhiệm vụ:
  - Giao tiếp trực tiếp với Ollama (qwen2.5-coder:7b-instruct).
  - Phân rã tác vụ và điều phối agent tự động sinh mã nguồn.
Inputs: user_prompt (str)
Outputs: dict (execution_plan, ai_response)
"""

import os
import json
import requests
from typing import Dict, List, Any


class ViberOrchestrator:
    """
    Class điều phối Multi-Agent kết nối Ollama local-first.
    """

    def __init__(self, project_map_path: str = "PROJECT_MAP.md", ollama_host: str = "http://localhost:11434"):
        self.project_map_path = project_map_path
        self.agents_dir = "agents"
        self.ollama_host = ollama_host
        self.model_name = "qwen2.5-coder:7b-instruct"

    def load_project_map(self) -> str:
        """Đọc bản đồ dự án PROJECT_MAP.md"""
        if not os.path.exists(self.project_map_path):
            return "PROJECT_MAP.md chưa được khởi tạo."
        with open(self.project_map_path, "r", encoding="utf-8") as f:
            return f.read()

    def call_ollama(self, system_prompt: str, user_prompt: str) -> str:
        """
        Gửi request tới Ollama API local (CPU-only) để lấy phản hồi từ LLM.
        """
        url = f"{self.ollama_host}/api/generate"
        payload = {
            "model": self.model_name,
            "prompt": f"System: {system_prompt}\n\nUser: {user_prompt}",
            "stream": False
        }
        
        try:
            response = requests.post(url, json=payload, timeout=60)
            if response.status_code == 200:
                return response.json().get("response", "Không nhận được phản hồi từ mô hình.")
            else:
                return f"Lỗi kết nối Ollama API: {response.status_code}"
        except requests.exceptions.ConnectionError:
            return "Không thể kết nối tới Ollama. Hãy đảm bảo service Ollama đang chạy trên máy local."

    def run_workflow(self, user_prompt: str) -> Dict[str, Any]:
        """
        Kích hoạt luồng xử lý thông qua BOD_CEO_01 kết hợp Ollama.
            """
        print(f"[ViberOrchestrator] Đang chuyển yêu cầu tới BOD_CEO_01 qua model {self.model_name}...")
        
        ceo_system_prompt = (
            "Bạn là BOD_CEO_01, Giám đốc điều hành Tập đoàn AI tự trị. "
            "Nhiệm vụ của bạn là tiếp nhận yêu cầu, phân rã công việc thành các bước cụ thể "
            "và chỉ định rõ Agent thực hiện (ENG_VIBER_DEV_01, QA_VIBER_TESTER_01, BIZ_*) ngắn gọn, súc tích."
        )
        
        ai_plan = self.call_ollama(ceo_system_prompt, user_prompt)
        
        return {
            "status": "SUCCESS",
            "user_prompt": user_prompt,
            "handled_by": "BOD_CEO_01",
            "model": self.model_name,
            "execution_plan_generated": ai_plan
        }


if __name__ == "__main__":
    orchestrator = ViberOrchestrator()
    result = orchestrator.run_workflow("Xây dựng thêm tính năng quản lý kho vàng miếng")
    print(json.dumps(result, ensure_ascii=False, indent=2))