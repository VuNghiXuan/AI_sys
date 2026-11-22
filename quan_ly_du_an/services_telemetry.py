# ============================================================================
# File Path: quan_ly_du_an/services_telemetry.py
# Module: Telemetry & Ollama Models Inspector
# Linked Files: views_telemetry.py, workbench_studio.js
# Purpose: Lay thong so CPU/RAM/GPU thuc te tren may va danh sach model Ollama.
# ============================================================================

import json
import logging
import os
import platform
import shutil
import subprocess
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")


def lay_thong_tin_cpu() -> dict:
    """Lay so luong/nhan va % su dung CPU thuc te."""
    logical_threads = os.cpu_count() or 1
    cpu_name = platform.processor() or platform.machine() or "CPU"
    usage_pct = None

    try:
        import psutil  # type: ignore

        usage_pct = round(float(psutil.cpu_percent(interval=0.15)), 1)
    except Exception:
        # Fallback khi chua cai psutil: doc load average tren Unix neu co
        try:
            load_1m, _, _ = os.getloadavg()
            usage_pct = round(min(100.0, max(0.0, (load_1m / logical_threads) * 100.0)), 1)
        except Exception:
            usage_pct = None

    return {
        "name": cpu_name,
        "threads": logical_threads,
        "usage_pct": usage_pct,
    }


def lay_thong_tin_ram() -> dict:
    """Lay dung luong RAM tong va dang su dung (GB, %)."""
    try:
        import psutil  # type: ignore

        vm = psutil.virtual_memory()
        total_gb = round(vm.total / (1024 ** 3), 1)
        used_gb = round(vm.used / (1024 ** 3), 1)
        return {
            "total_gb": total_gb,
            "used_gb": used_gb,
            "usage_pct": round(float(vm.percent), 1),
        }
    except Exception as exc:
        logger.warning("Khong doc duoc RAM qua psutil: %s", exc)
        return {
            "total_gb": None,
            "used_gb": None,
            "usage_pct": None,
        }


def lay_thong_tin_gpu() -> dict:
    """Kiem tra GPU roi qua nvidia-smi neu co; neu khong co thi bao ro chay CPU/RAM."""
    nvidia_smi = shutil.which("nvidia-smi")
    if not nvidia_smi:
        return {
            "has_gpu": False,
            "label": "Không có GPU rời",
            "detail": "Chạy local trên CPU & RAM hệ thống.",
        }

    try:
        proc = subprocess.run(
            [
                nvidia_smi,
                "--query-gpu=name,utilization.gpu,memory.used,memory.total",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        lines = [line.strip() for line in (proc.stdout or "").splitlines() if line.strip()]
        if proc.returncode == 0 and lines:
            parts = [p.strip() for p in lines[0].split(",")]
            gpu_name = parts[0] if len(parts) > 0 else "GPU"
            gpu_util = parts[1] if len(parts) > 1 else "?"
            mem_used = parts[2] if len(parts) > 2 else "?"
            mem_total = parts[3] if len(parts) > 3 else "?"
            return {
                "has_gpu": True,
                "label": gpu_name,
                "detail": f"Tải GPU: {gpu_util}% · VRAM: {mem_used}/{mem_total} MB",
            }
    except Exception as exc:
        logger.warning("Loi khi kiem tra GPU qua nvidia-smi: %s", exc)

    return {
        "has_gpu": False,
        "label": "Không phát hiện GPU rời",
        "detail": "Đang dùng CPU & RAM hệ thống.",
    }


def _goi_json_ollama(path: str, timeout: float = 1.5) -> dict | None:
    url = f"{OLLAMA_BASE_URL}{path}"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return json.loads(raw)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        logger.debug("Khong truy van duoc Ollama %s: %s", url, exc)
        return None


def lay_danh_sach_model_ollama() -> dict:
    """Lay danh sach model da cai (/api/tags) va model dang chay (/api/ps) tren Ollama."""
    tags_data = _goi_json_ollama("/api/tags")
    ps_data = _goi_json_ollama("/api/ps")

    if tags_data is None and ps_data is None:
        return {
            "online": False,
            "running_models": [],
            "installed_models": [],
            "message": "Chưa kết nối được Ollama (127.0.0.1:11434).",
        }

    running_models = []
    for item in (ps_data or {}).get("models", []):
        name = item.get("name") or item.get("model") or ""
        size_vram = item.get("size_vram") or 0
        size_total = item.get("size") or 0
        mem_gb = round((size_total or size_vram) / (1024 ** 3), 1) if (size_total or size_vram) else 0
        if name:
            running_models.append({
                "name": name,
                "mem_gb": mem_gb,
            })

    installed_models = []
    for item in (tags_data or {}).get("models", []):
        name = item.get("name") or item.get("model") or ""
        size_bytes = item.get("size") or 0
        size_gb = round(size_bytes / (1024 ** 3), 1) if size_bytes else 0
        if name:
            installed_models.append({
                "name": name,
                "size_gb": size_gb,
            })

    return {
        "online": True,
        "running_models": running_models,
        "installed_models": installed_models,
        "message": "Ollama đang hoạt động.",
    }


def thu_thap_telemetry_thuc_te() -> dict:
    """Tong hop CPU, RAM, GPU va danh sach model Ollama thuc te."""
    return {
        "cpu": lay_thong_tin_cpu(),
        "ram": lay_thong_tin_ram(),
        "gpu": lay_thong_tin_gpu(),
        "ollama": lay_danh_sach_model_ollama(),
    }