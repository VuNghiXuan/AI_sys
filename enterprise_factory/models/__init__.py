# enterprise_factory/models.py
"""
Khởi tạo package models cho vnxBox Enterprise, gom nhóm toàn bộ mô hình dữ liệu
để Django ORM nhận diện và migration hoàn toàn trơn tru.
"""

from .base import SystemConfig, Company
from .agent import AgentRole, AgentRegistry, JobOpening
from .workflow import DirectiveLog, AgentDiscussion, CodePatchProposal, AgentTaskDAG, ToolRegistry, WorkflowBlueprint
from .knowledge import ProjectNode, IntentMemory

__all__ = [
    'SystemConfig',
    'Company',
    'AgentRole',
    'AgentRegistry',
    'JobOpening',
    'DirectiveLog',
    'AgentDiscussion',
    'CodePatchProposal',
    'AgentTaskDAG',
    'ProjectNode',
    'IntentMemory',
    'ToolRegistry', 
    'WorkflowBlueprint'
]