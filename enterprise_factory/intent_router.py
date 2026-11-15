# File: enterprise_factory/intent_router.py
import logging
from enterprise_factory.services.semantic_router import HybridSemanticRouter

logger = logging.getLogger(__name__)


class IntentRouter:
    @classmethod
    def route(cls, user_message: str) -> dict:
        return HybridSemanticRouter.route(user_message)

    @classmethod
    def classify(cls, user_message: str) -> dict:
        return cls.route(user_message)


def classify_user_intent(user_message: str) -> str:
    result = HybridSemanticRouter.route(user_message)
    return result.get("intent_code", "LLM_CHAT")