"""
# File Path: core/agent_registry.py
# File Purpose: Quản lý đăng ký động (Dynamic Registry) các Agent thông qua tệp Manifest JSON,
#               thực hiện kiến trúc Plug-and-Play cho vnxBox Enterprise.
# Connected Files: [agents/coder_agent.json, core/dag_engine.py]
# Logs: Ghi log chi tiết quá trình quét thư mục agents/, nạp Manifest và khởi tạo Agent profile.
"""

import logging
import json
import os
from typing import Dict, Any

# Thiết lập hệ thống Logging tiêu chuẩn cho vnxBox
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] - %(message)s"
)
logger = logging.getLogger("vnxBox.AgentRegistry")

class AgentRegistry:
    """
    # Class: AgentRegistry
    # Purpose: Tự động quét và đăng ký các Agent Manifest từ thư mục /agents/ vào hệ thống.
    """
    def __init__(self, agents_dir: str = "agents"):
        self.agents_dir = agents_dir
        self.registry: Dict[str, Dict[str, Any]] = {}
        logger.info(f"[AGENT_REGISTRY] Khởi tạo Agent Registry với thư mục: {agents_dir}")

    def discover_and_register_agents(self) -> None:
        """
        # Function: discover_and_register_agents
        # Purpose: Quét toàn bộ file JSON trong thư mục agents/ và nạp vào bộ nhớ động.
        # Input: None
        # Output: None
        """
        if not os.path.exists(self.agents_dir):
            logger.warning(f"[AGENT_REGISTRY] Thư mục {self.agents_dir} không tồn tại. Đang tiến hành tạo mới...")
            os.makedirs(self.agents_dir, exist_ok=True)
            return

        logger.info("[AGENT_REGISTRY] Bắt đầu quét các Agent Manifest...")
        
        for filename in os.listdir(self.agents_dir):
            if filename.endswith(".json"):
                file_path = os.path.join(self.agents_dir, filename)
                self._load_agent_manifest(file_path)

    def _load_agent_manifest(self, file_path: str) -> None:
        """
        # Function: _load_agent_manifest
        # Purpose: Đọc tệp JSON Manifest của từng Agent và đăng ký vào registry.
        # Input: file_path (str)
        # Output: None
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
                
            agent_id = manifest.get("agent_id")
            if agent_id:
                self.registry[agent_id] = manifest
                logger.info(f"   + Đăng ký thành công Agent [ID: {agent_id}] từ tệp {file_path}")
            else:
                logger.error(f"   X Tệp manifest {file_path} thiếu trường 'agent_id' bắt buộc.")
        except Exception as e:
            logger.error(f"   X Lỗi khi đọc manifest {file_path}: {e}")

    def get_agent_profile(self, agent_id: str) -> Dict[str, Any]:
        """
        # Function: get_agent_profile
        # Purpose: Lấy thông tin cấu hình profile của một Agent theo ID.
        # Input: agent_id (str)
        # Output: Dict chứa thông tin manifest của Agent hoặc thông báo lỗi nếu không tìm thấy.
        """
        profile = self.registry.get(agent_id)
        if not profile:
            logger.warning(f"[AGENT_REGISTRY] Không tìm thấy Agent với ID: {agent_id}")
        return profile or {}


if __name__ == "__main__":
    logger.info("=== BẮT ĐẦU KIỂM THỬ ĐỘC LẬP AGENT REGISTRY ===")
    
    registry = AgentRegistry(agents_dir="agents")
    registry.discover_and_register_agents()
    
    # Kiểm tra profile của coder_agent vừa nạp
    coder_profile = registry.get_agent_profile("coder_agent")
    logger.info(f"Thông tin cấu hình Coder Agent đã nạp: {coder_profile}")
    
    logger.info("=== HOÀN TẤT KIỂM THỬ AGENT REGISTRY ===")