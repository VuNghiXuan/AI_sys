# enterprise_factory/services/orchestrator/config_loader.py
"""
Dynamic Hardware & Model Inspector cho vnxBox Enterprise.
Tự động phát hiện cấu hình phần cứng, VRAM, quản lý tham số LLM
và hỗ trợ chuyển đổi mượt mà giữa CPU-only (7B) và GPU (32B+).
"""

import logging
import os
import torch
from django.conf import settings

logger = logging.getLogger(__name__)

class ModelHardwareInspector:
    """Kiểm tra và cấu hình tài nguyên phần cứng, VRAM cho Ollama & LLM Runner"""

    @staticmethod
    def get_active_hardware_profile() -> dict:
        """Kiểm tra xem hệ thống đang dùng CPU hay GPU (CUDA / MPS)"""
        has_cuda = torch.cuda.is_available()
        vram_gb = 0.0
        device_name = "CPU-only (Intel i7-14700)"

        if has_cuda:
            try:
                device_name = torch.cuda.get_device_name(0)
                vram_bytes = torch.cuda.get_device_properties(0).total_memory
                vram_gb = round(vram_bytes / (1024 ** 3), 2)
            except Exception as e:
                logger.warning(f"[!] [HARDWARE INSPECTOR] Không thể đọc chi tiết VRAM GPU: {str(e)}")

        profile = {
            "has_gpu": has_cuda,
            "device_name": device_name,
            "vram_gb": vram_gb,
            "recommended_tier": "7B" if vram_gb < 16 else ("32B" if vram_gb < 32 else "70B+")
        }
        logger.info(f"[*] [HARDWARE PROFILE]: {profile}")
        return profile

    @staticmethod
    def get_dynamic_ollama_options() -> dict:
        """Tự động cấu hình num_ctx, temperature dựa trên phần cứng hiện tại"""
        profile = ModelHardwareInspector.get_active_hardware_profile()
        
        # Cấu hình mặc định tối ưu cho lập trình Vibercode
        options = {
            "temperature": 0.2,
            "num_ctx": 4096,
        }

        # Nếu Sếp đã nâng cấp GPU VRAM >= 24GB, tự động mở rộng context window lên 8192 token
        if profile["has_gpu"] and profile["vram_gb"] >= 20:
            options["num_ctx"] = 8192
            logger.info("[+] [GPU OPTIMIZATION] Phát hiện GPU VRAM lớn. Đã nâng context window lên 8192 tokens.")

        return options

    @staticmethod
    def get_model_endpoint_and_name() -> tuple:
        """Lấy Host và Tên Model hiện hành từ Django Settings hoặc Fallback"""
        ollama_host = getattr(settings, 'OLLAMA_HOST', 'http://localhost:11434')
        
        # Cho phép ép model lớn qua biến môi trường nếu đã có GPU
        default_model = 'qwen2.5-coder:7b-instruct'
        profile = ModelHardwareInspector.get_active_hardware_profile()
        if profile["has_gpu"] and profile["vram_gb"] >= 20:
            default_model = getattr(settings, 'OLLAMA_GPU_MODEL', 'qwen2.5-coder:32b-instruct')

        model_name = getattr(settings, 'OLLAMA_MODEL', default_model)
        return ollama_host, model_name