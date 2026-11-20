# ==============================================================================
# File Path: core/auto_model_setup.py
# Description: Tự động kiểm tra RAM/CPU/GPU, chọn model Ollama phù hợp và cấu hình.
# Linked Files: [config/runtime_profiles.json, core/llm_client.py, core/logger_setup.py]
# Slice Tag: [CORE: AUTO_MODEL_SETUP]
# ==============================================================================

import ctypes
import json
import logging
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class HardwareProfile:
    """Thông tin phần cứng và bộ nhớ khả dụng tại thời điểm kiểm tra."""

    total_ram_gb: float
    avail_ram_gb: float
    cpu_threads: int
    vram_total_gb: float = 0.0


def get_windows_memory_gb() -> tuple[float, float]:
    """Lấy (tổng RAM GB, RAM khả dụng GB) trên Windows không cần thư viện ngoài."""
    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.c_ulong),
            ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    stat = MEMORYSTATUSEX()
    stat.dwLength = ctypes.sizeof(stat)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
    gb = 1024 ** 3
    return round(stat.ullTotalPhys / gb, 2), round(stat.ullAvailPhys / gb, 2)


def get_nvidia_vram_gb() -> float:
    """Kiểm tra tổng VRAM (GB) nếu có GPU NVIDIA và nvidia-smi."""
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
        first_line = out.strip().splitlines()[0].strip()
        return round(float(first_line) / 1024.0, 2)
    except Exception:
        return 0.0


def detect_hardware() -> HardwareProfile:
    """Tổng hợp cấu hình máy hiện tại."""
    if os.name == "nt":
        total_ram, avail_ram = get_windows_memory_gb()
    else:
        total_ram, avail_ram = 16.0, 8.0
    return HardwareProfile(
        total_ram_gb=total_ram,
        avail_ram_gb=avail_ram,
        cpu_threads=os.cpu_count() or 4,
        vram_total_gb=get_nvidia_vram_gb(),
    )


def choose_model_for_hardware(hw: HardwareProfile) -> tuple[str, int]:
    """Chọn (model_name, num_ctx) an toàn theo phần cứng."""
    if hw.vram_total_gb >= 24.0 and hw.avail_ram_gb >= 12.0:
        return "qwen3:30b-a3b", 8192
    if hw.avail_ram_gb >= 11.0:
        return "qwen2.5-coder:7b-instruct", 4096
    return "qwen2.5:3b", 4096


def ensure_ollama_model(model_name: str, auto_pull: bool = False) -> bool:
    """Kiểm tra model đã có trong Ollama chưa; tùy chọn tự pull nếu thiếu."""
    try:
        listed = subprocess.check_output(["ollama", "list"], text=True, timeout=15)
        if model_name in listed:
            logger.info("Model '%s' đã có sẵn trên Ollama.", model_name)
            return True
    except Exception as exc:
        logger.warning("Không kiểm tra được 'ollama list': %s", exc)
        return False

    if not auto_pull:
        logger.info("Model '%s' chưa có; bỏ qua tải vì auto_pull=False.", model_name)
        return False

    logger.info("Đang tải model '%s' qua ollama pull...", model_name)
    proc = subprocess.run(["ollama", "pull", model_name], text=True)
    return proc.returncode == 0


def apply_runtime_config(config_path: str, model_name: str, num_ctx: int) -> None:
    """Cập nhật model và num_ctx cho profile đang hoạt động."""
    path = Path(config_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    active = data.get("active_profile")
    if active and active in data.get("profiles", {}):
        data["profiles"][active]["model"] = model_name
        data["profiles"][active]["num_ctx"] = num_ctx
    path.write_text(json.dumps(data, indent=4, ensure_ascii=False), encoding="utf-8")
    logger.info("Đã cập nhật '%s' -> model=%s, num_ctx=%d", config_path, model_name, num_ctx)


if __name__ == "__main__":
    from core.logger_setup import setup_logger

    setup_logger()
    hw = detect_hardware()
    chosen_model, ctx = choose_model_for_hardware(hw)
    print(f"Phần cứng: RAM={hw.avail_ram_gb}/{hw.total_ram_gb}GB | CPU={hw.cpu_threads} luồng | VRAM={hw.vram_total_gb}GB")
    print(f"Đề xuất: model={chosen_model} | num_ctx={ctx}")
    # Đổi auto_pull=True nếu muốn tự tải model khi thiếu
    ready = ensure_ollama_model(chosen_model, auto_pull=False)
    if ready:
        apply_runtime_config("config/runtime_profiles.json", chosen_model, ctx)