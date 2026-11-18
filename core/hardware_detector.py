"""
# File Path: core/hardware_detector.py
# File Purpose: Tự động phát hiện và cấu hình thiết bị phần cứng (CPU/GPU/MPS) cho vnxBox Enterprise,
#               sử dụng 100% thư viện chuẩn Python (Built-in) không phụ thuộc gói ngoài.
# Connected Files: [core/dag_engine.py, core/router.py] - Cung cấp thông tin phần cứng để phân bổ tài nguyên AI.
# Logs: Ghi log chi tiết trạng thái phát hiện phần cứng tại thời điểm khởi động hệ thống.
"""

import logging
import platform
import os
from typing import Dict, Any

# Thiết lập hệ thống Logging tiêu chuẩn cho vnxBox
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] - %(message)s"
)
logger = logging.getLogger("vnxBox.HardwareDetector")

def check_system_environment() -> Dict[str, Any]:
    """
    # Function: check_system_environment
    # Purpose: Kiểm tra thông tin hệ điều hành và số luồng CPU khả dụng bằng Python built-in.
    # Input: None
    # Output: Dict chứa thông tin tổng quan về phần cứng cơ bản.
    """
    sys_info = {
        "platform": platform.system(),
        "release": platform.release(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count(),
    }
    logger.info(f"[SYSTEM] Khởi chạy trên môi trường: {sys_info['platform']} {sys_info['release']} | CPU Cores/Threads: {sys_info['cpu_count']}")
    return sys_info

def get_optimal_device() -> str:
    """
    # Function: get_optimal_device
    # Purpose: Kiểm tra thiết bị tối ưu để chạy mô hình AI/Ollama hoặc tính toán cục bộ.
    # Input: None
    # Output: Trả về chuỗi định danh thiết bị ('cuda', 'mps', hoặc 'cpu').
    """
    device = "cpu"
    try:
        import torch
        if torch.cuda.is_available():
            device = "cuda"
            gpu_name = torch.cuda.get_device_name(0)
            logger.info(f"[HARDWARE] Phát hiện GPU NVIDIA độc lập. Thiết bị tối ưu: CUDA ({gpu_name})")
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            device = "mps"
            logger.info("[HARDWARE] Phát hiện Apple Silicon GPU. Thiết bị tối ưu: MPS")
        else:
            logger.info("[HARDWARE] Không phát hiện GPU rời. Chế độ tối ưu: CPU-only (Tối ưu hóa đa luồng).")
    except ImportError:
        logger.warning("[HARDWARE] PyTorch chưa được cài đặt. Mặc định sử dụng thiết bị: CPU")
        
    return device

if __name__ == "__main__":
    # Điểm kiểm thử độc lập cho module
    logger.info("=== BẮT ĐẦU KIỂM TRA PHẦN CỨNG VNXBOX ==   ")
    check_system_environment()
    optimal_device = get_optimal_device()
    logger.info(f"=== KẾT QUẢ: HỆ THỐNG SẴN SÀNG TRÊN THIẾT BỊ [{optimal_device.upper()}] ===")