# ==============================================================================
# File Path: core/logger_setup.py
# Description: Thiết lập logging chuẩn cho toàn bộ hệ thống vnxbox.
# Linked Files: [config/runtime_profiles.json, core/router.py, core/llm_client.py]
# Slice Tag: [CORE: LOGGER_SETUP]
# ==============================================================================

import logging
from pathlib import Path


def setup_logger(name: str = "vnxbox", log_dir: str = "logs", level: int = logging.INFO) -> logging.Logger:
    """Khởi tạo logger ghi ra console và file log theo tên module/luồng."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(level)
    logger.propagate = False

    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    log_file = log_path / f"{name}.log"

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.info("Khởi tạo logger '%s' thành công -> %s", name, log_file)
    return logger