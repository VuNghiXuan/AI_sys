"""
# File Path: core/agent_executor.py
# File Purpose: Quản lý và thực thi các Agent chuyên trách (PM, Coder, QC) thông qua OllamaClient 
#               dựa trên manifest JSON, hỗ trợ cả hàm chuyên biệt lẫn hàm tổng quát.
# Connected Files: [core/ollama_client.py, core/agent_registry.py, core/pipeline_runner.py]
# Logs: Ghi log chi tiết quá trình gọi LLM cho từng tác vụ của Agent.
"""

import logging
from typing import Dict, Any
from core.ollama_client import OllamaClient
from core.agent_registry import AgentRegistry

# Thiết lập hệ thống Logging tiêu chuẩn cho vnxBox
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] - %(message)s"
)
logger = logging.getLogger("vnxBox.AgentExecutor")

class AgentExecutor:
    """
    # Class: AgentExecutor
    # Purpose: Điều phối thực thi Multi-Agent trong hệ thống vnxBox Enterprise.
    """
    def __init__(self):
        self.ollama_client = OllamaClient()
        self.registry = AgentRegistry()
        self.registry.discover_and_register_agents()
        logger.info("[AGENT_EXECUTOR] Khởi tạo Multi-Agent Executor thành công.")

    def run_agent(self, agent_id: str, task_context: str) -> Dict[str, Any]:
        """
        # Function: run_agent
        # Purpose: Kích hoạt linh hoạt bất kỳ Agent nào dựa trên ID và ngữ cảnh nhiệm vụ.
        """
        profile = self.registry.get_agent_profile(agent_id)
        if not profile:
            logger.error(f"[AGENT_EXECUTOR] Không tìm thấy profile cho Agent ID: {agent_id}")
            return {"status": "FAILED", "output": "", "error": f"Agent {agent_id} profile missing"}

        system_prompt = profile.get("system_prompt", "Bạn là một trợ lý AI chuyên nghiệp.")
        user_prompt = f"Ngữ cảnh / Nhiệm vụ:\n{task_context}"

        logger.info(f"[AGENT_EXECUTOR] Đang kích hoạt Agent [{agent_id}] xử lý công việc qua Ollama...")
        raw_output = self.ollama_client.generate_code(system_prompt, user_prompt)

        is_error = raw_output.startswith("# Error")
        return {
            "status": "FAILED" if is_error else "SUCCESS",
            "agent_id": agent_id,
            "output": raw_output,
            "error": raw_output if is_error else None
        }

    def run_coder_agent(self, task_name: str, design_spec: str) -> Dict[str, Any]:
        """
        # Function: run_coder_agent (Wrapper tương thích ngược cho Pipeline Runner)
        # Purpose: Giữ nguyên hàm cũ nhưng bên trong gọi qua cơ chế đa agent.
        """
        task_context = (
            f"Nhiệm vụ: {task_name}\n"
            f"Đặc tả kỹ thuật:\n{design_spec}\n\n"
            f"Yêu cầu bắt buộc:\n"
            f"- Viết mã nguồn Python hoàn chỉnh.\n"
            f"- Tuân thủ Header Comment chuẩn vnxBox.\n"
            f"- Giới hạn dưới 300 dòng, chia nhỏ hàm, tuyệt đối không hardcode.\n"
            f"- Có docstring và logging đầy đủ."
        )
        res = self.run_agent("coder_agent", task_context)
        return {
            "status": res["status"],
            "source_code": res["output"],
            "error": res["error"]
        }

if __name__ == "__main__":
    logger.info("=== BẮT ĐẦU KIỂM THỬ MULTI-AGENT EXECUTOR ===")
    executor = AgentExecutor()
    
    # Test Coder Agent qua hàm tương thích
    result = executor.run_coder_agent(
        task_name="Viết module tính toán giá trị vàng theo tuổi vàng",
        design_spec="Hàm nhận vào trọng lượng (chỉ) và tuổi vàng (9999, 750)."
    )
    logger.info(f"Kết quả Coder Agent:\n{result['source_code']}")
    logger.info("=== HOÀN TẤT KIỂM THỬ MULTI-AGENT EXECUTOR ===")