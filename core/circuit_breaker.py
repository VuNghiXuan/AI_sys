# ==============================================================================
# File Path: core/circuit_breaker.py
# Description: Cầu chì ngắt mạch (Circuit Breaker) cho vòng lặp tự sửa lỗi.
# Linked Files: [config/runtime_profiles.json, core/logger_setup.py]
# Slice Tag: [CORE: CIRCUIT_BREAKER]
# ==============================================================================

import hashlib
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class RepairAttempt:
    """Ghi nhận 1 lượt tự sửa lỗi."""

    attempt_number: int
    error_signature: str
    error_message: str
    action_summary: str
    passed: bool


@dataclass
class BreakerStatus:
    """Trạng thái hiện tại của cầu chì ngắt mạch."""

    state: str = "CLOSED"  # CLOSED (đang chạy bình thường) | TRIPPED (đã ngắt mạch)
    attempts_used: int = 0
    max_retries: int = 4
    trip_reason: str = ""
    history: list[RepairAttempt] = field(default_factory=list)


class RepairCircuitBreaker:
    """Kiểm soát số lượt tự sửa lỗi và ngắt mạch khi chạm giới hạn hoặc lặp lỗi."""

    def __init__(self, config_path: str = "config/runtime_profiles.json") -> None:
        cb_cfg = self._load_breaker_config(config_path)
        self.max_retries = int(cb_cfg.get("max_retries", 4))
        self.stop_on_repeated_error = bool(cb_cfg.get("stop_on_repeated_error", True))
        self.status = BreakerStatus(state="CLOSED", max_retries=self.max_retries)

    def _load_breaker_config(self, config_path: str) -> dict:
        """Đọc cấu hình circuit_breaker từ file config."""
        path = Path(config_path)
        if not path.exists():
            return {"max_retries": 4, "stop_on_repeated_error": True}
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("circuit_breaker", {"max_retries": 4, "stop_on_repeated_error": True})

    @staticmethod
    def make_error_signature(error_message: str) -> str:
        """Tạo mã băm ngắn gọn để nhận diện lỗi lặp lại."""
        normalized = " ".join((error_message or "").strip().split())
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]

    def record_failure(self, error_message: str, action_summary: str) -> BreakerStatus:
        """Ghi nhận 1 lần sửa chưa đạt và quyết định tiếp tục hay ngắt mạch."""
        self.status.attempts_used += 1
        sig = self.make_error_signature(error_message)

        attempt = RepairAttempt(
            attempt_number=self.status.attempts_used,
            error_signature=sig,
            error_message=error_message.strip(),
            action_summary=action_summary.strip(),
            passed=False,
        )
        self.status.history.append(attempt)

        repeated_count = sum(1 for item in self.status.history if item.error_signature == sig)

        if self.status.attempts_used >= self.max_retries:
            self.status.state = "TRIPPED"
            self.status.trip_reason = (
                f"Đã đạt giới hạn tối đa {self.max_retries} lượt tự sửa nhưng lỗi vẫn chưa hết."
            )
            logger.error("CIRCUIT BREAKER TRIPPED: %s", self.status.trip_reason)
        elif self.stop_on_repeated_error and repeated_count >= 3:
            self.status.state = "TRIPPED"
            self.status.trip_reason = (
                f"Lỗi giống nhau (sig={sig}) lặp lại {repeated_count} lần — dừng để tránh sửa vòng vo."
            )
            logger.warning("CIRCUIT BREAKER TRIPPED (repeated error): %s", self.status.trip_reason)
        else:
            logger.info(
                "Vòng lặp tự sửa lượt %d/%d chưa đạt (sig=%s) -> cho phép thử lượt tiếp.",
                self.status.attempts_used,
                self.max_retries,
                sig,
            )

        return self.status

    def mark_recovered(self, action_summary: str = "Đã khắc phục và kiểm thử đạt.") -> BreakerStatus:
        """Đánh dấu đã sửa thành công, reset bộ đếm và giữ mạch ở trạng thái CLOSED."""
        logger.info("Vòng lặp tự sửa thành công sau %d lượt: %s", self.status.attempts_used, action_summary)
        self.status.state = "CLOSED"
        self.status.attempts_used = 0
        self.status.trip_reason = ""
        return self.status