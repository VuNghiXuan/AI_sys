# File: enterprise_factory/intent_router.py
"""
Intent Router & Orchestrator cho vnxBox Enterprise (Build 2026).
Điều phối định tuyến đa tầng từ Lớp 0 (Intent Planner) đến Lớp 3 (Deep Reasoning).
"""

import logging
from enterprise_factory.services.semantic_router import HybridSemanticRouter
from enterprise_factory.services.intent_planner import IntentPlanner

logger = logging.getLogger(__name__)


class IntentRouter:
    """
    Tổng chỉ huy định tuyến ý định, tích hợp chiến thuật đa tầng theo AGI Spec.
    """

    @classmethod
    async def route_async(cls, user_message: str) -> list[dict]:
        """
        Định tuyến bất đồng bộ thông minh (Hỗ trợ phân rã Multi-Intent qua Lớp 0 - Intent Planner).
        Dùng cho luồng WebSocket thực chiến tại chat_handler.py.
        """
        return await IntentPlanner.decompose_directive(user_message)

    @classmethod
    def route(cls, user_message: str) -> dict:
        """
        Định tuyến đồng bộ truyền thống (Dùng cho các module gọi nhanh qua Hybrid Router).
        """
        return HybridSemanticRouter.route(user_message)

    @classmethod
    def classify(cls, user_message: str) -> dict:
        return cls.route(user_message)


def classify_user_intent(user_message: str) -> str:
    result = HybridSemanticRouter.route(user_message)
    return result.get("intent_code", "LLM_CHAT")