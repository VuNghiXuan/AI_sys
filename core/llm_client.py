# ==============================================================================
# File Path: core/llm_client.py
# Description: Client gọi model local (Ollama / llama-server) theo runtime_profiles.json.
# Linked Files: [config/runtime_profiles.json, core/logger_setup.py]
# Slice Tag: [CORE: LLM_RUNTIME_CLIENT]
# ==============================================================================

import json
import logging
from pathlib import Path
import requests

logger = logging.getLogger(__name__)


class LocalLLMClient:
    """Gọi endpoint chat local theo profile cấu hình, không hardcode model/URL."""

    def __init__(
        self,
        config_path: str = "config/runtime_profiles.json",
        profile_name: str | None = None,
    ) -> None:
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.profile_name = profile_name or self.config.get(
            "active_profile", "local_cpu_moe_default"
        )
        self.profile = self._resolve_profile(self.profile_name)

    def _load_config(self) -> dict:
        """Đọc file cấu hình runtime profiles."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Không tìm thấy file cấu hình: {self.config_path}")
        with self.config_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _resolve_profile(self, name: str) -> dict:
        """Lấy profile cấu hình theo tên."""
        profiles = self.config.get("profiles", {})
        if name not in profiles:
            raise KeyError(f"Profile '{name}' không tồn tại trong {self.config_path}")
        return profiles[name]

    def chat(
        self,
        messages: list[dict[str, str]],
        model_override: str | None = None,
        temperature_override: float | None = None,
    ) -> str:
        """Gửi hội thoại tới local engine và trả về nội dung phản hồi."""
        base_url = self.profile.get("base_url", "http://localhost:11434/v1").rstrip("/")
        model = model_override or self.profile.get("model", "")
        fallback_model = self.profile.get("fallback_model", "")
        temperature = (
            temperature_override
            if temperature_override is not None
            else float(self.profile.get("temperature", 0.2))
        )
        timeout = int(self.profile.get("timeout_seconds", 180))
        num_ctx = int(self.profile.get("num_ctx", 16384))

        url = f"{base_url}/chat/completions"
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "options": {"num_ctx": num_ctx},
        }
        if "keep_alive" in self.profile:
            payload["keep_alive"] = self.profile["keep_alive"]

        logger.info(
            "Gửi request tới %s | profile=%s | model=%s | num_ctx=%d",
            url,
            self.profile_name,
            model,
            num_ctx,
        )

        try:
            resp = requests.post(url, json=payload, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            logger.info("Nhận phản hồi thành công từ model '%s' (%d ký tự).", model, len(content))
            return content
        except Exception as exc:
            logger.warning("Lỗi gọi model '%s': %s", model, exc)
            if fallback_model and fallback_model != model:
                logger.info("Thử chuyển sang fallback_model='%s'...", fallback_model)
                payload["model"] = fallback_model
                resp = requests.post(url, json=payload, timeout=timeout)
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            raise