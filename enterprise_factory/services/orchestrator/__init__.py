# enterprise_factory/services/orchestrator.py
"""
Orchestration & Ollama Client Service cho vnxBox Enterprise.
File cầu nối tổng hợp các module con trong thư mục orchestrator/ phục vụ toàn hệ thống.
"""

from .config_loader import ModelHardwareInspector
from .client import ask_local_agent
from .runner import execute_agent_task

__all__ = [
    'ModelHardwareInspector',
    'ask_local_agent',
    'execute_agent_task',
]