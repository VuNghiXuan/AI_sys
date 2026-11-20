import os
from django.apps import AppConfig


class HubCoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "hub_core"

    def ready(self) -> None:
        # Tránh chạy 2 lần khi Django autoreload bật trên Windows
        if os.environ.get("RUN_MAIN") != "true":
            return
        from core.auto_model_setup import (
            apply_runtime_config,
            choose_model_for_hardware,
            detect_hardware,
            ensure_ollama_model,
        )

        hw = detect_hardware()
        model_name, num_ctx = choose_model_for_hardware(hw)
        if ensure_ollama_model(model_name, auto_pull=False):
            apply_runtime_config("config/runtime_profiles.json", model_name, num_ctx)