# enterprise_factory/services/orchestrator/runner.py
"""
Unified Agent Runner cho vnxBox Enterprise.
Thực thi tác vụ tập trung cho mọi nhân sự AI từ Database.
"""

import logging
from enterprise_factory.models import AgentRegistry
from .client import ask_local_agent

logger = logging.getLogger(__name__)


def execute_agent_task(agent_id: str, directive_text: str, context_data: dict = None) -> str:
    """
    Hàm thực thi thống nhất cho mọi Agent (Unified Agent Runner).
    Truy vấn thẳng hồ sơ từ DB qua Foreign Key role, lấy System Prompt động và gọi Ollama.
    """
    logger.info(f"[*] [AGENT_RUNNER] Bắt đầu thực thi tác vụ cho Agent ID: '{agent_id}' | Chỉ đạo: '{directive_text}'")
    
    try:
        agent_profile = AgentRegistry.objects.select_related('role').filter(agent_id=agent_id).first()
        
        if not agent_profile:
            logger.warning(f"[!] [AGENT_RUNNER] Không tìm thấy agent_id '{agent_id}'. Đang thử fallback về role 'BOD'...")
            agent_profile = AgentRegistry.objects.select_related('role').filter(role__role_code='BOD').first()
            
            if not agent_profile:
                err_msg = f"Hệ thống chưa khởi tạo nhân sự nào trong DB! Không tìm thấy agent_id: {agent_id} lẫn BOD fallback."
                logger.error(f"[-] [AGENT_RUNNER FATAL] {err_msg}")
                raise ValueError(err_msg)
            else:
                logger.info(f"[+] [AGENT_RUNNER] Fallback thành công. Sử dụng Agent BOD: {agent_profile.agent_id} ({agent_profile.display_name})")
        else:
            role_code = agent_profile.role.role_code if agent_profile.role else 'N/A'
            logger.info(f"[+] [AGENT_RUNNER] Đã định danh nhân sự: {agent_profile.display_name} (Role: {role_code})")

        system_prompt = agent_profile.system_prompt or f"Bạn là {agent_profile.display_name} tại vnxBox Enterprise."
        
        if context_data:
            logger.debug(f"[*] [AGENT_RUNNER] Đã đính kèm thêm bối cảnh dữ liệu (context_data) vào System Prompt.")
            system_prompt += f"\n\nBỐI CẢNH DỮ LIỆU BỔ SUNG:\n{str(context_data)}"

        logger.info(f"[*] [AGENT_RUNNER] Đang gửi yêu cầu gọi Ollama cho Agent [{agent_profile.display_name}]...")
        response = ask_local_agent(system_prompt, f"Nhiệm vụ / Chỉ đạo: {directive_text}")
        
        logger.info(f"[+] [AGENT_RUNNER] Hoàn thành tác vụ cho Agent [{agent_id}]. Phản hồi dài {len(response) if response else 0} ký tự.")
        return response

    except Exception as e:
        logger.error(f"[-] [AGENT_RUNNER ERROR] Lỗi ngoại lệ trong execute_agent_task (Agent ID: {agent_id}): {str(e)}", exc_info=True)
        raise e