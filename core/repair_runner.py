# ==============================================================================
# File Path: core/repair_runner.py
# Description: Điều phối vòng lặp tự sửa có Circuit Breaker, JIT Context và tự chọn model local.
# Linked Files: [core/auto_model_setup.py, core/circuit_breaker.py, core/jit_context.py, core/llm_client.py, core/logger_setup.py]
# Slice Tag: [CORE: REPAIR_RUNNER]
# ==============================================================================

import logging
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from core.auto_model_setup import (
    apply_runtime_config,
    choose_model_for_hardware,
    detect_hardware,
    ensure_ollama_model,
)
from core.circuit_breaker import BreakerStatus, RepairCircuitBreaker
from core.jit_context import JITContextBuilder
from core.llm_client import LocalLLMClient

logger = logging.getLogger(__name__)


@dataclass
class RepairRunResult:
    """Kết quả tổng hợp sau khi chạy vòng lặp tự sửa."""

    target_file: str
    success: bool
    breaker_status: BreakerStatus
    context_files: list[str] = field(default_factory=list)
    last_output: str = ""


class RepairLoopRunner:
    """Chạy kiểm thử/lệnh, gom JIT Context và điều phối sửa lỗi qua Circuit Breaker."""

    def __init__(
        self,
        project_root: str = ".",
        config_path: str = "config/runtime_profiles.json",
        map_file: str = "PROJECT_MAP.json",
    ) -> None:
        self.project_root = Path(project_root).resolve()
        self.config_path = config_path
        self.map_file = map_file
        self.breaker = RepairCircuitBreaker(config_path=config_path)
        self.context_builder = JITContextBuilder(
            project_root=str(self.project_root),
            map_file=map_file,
        )

    def prepare_model_if_needed(self, auto_pull: bool = False) -> None:
        """Dò phần cứng hiện tại, kiểm tra model Ollama và cập nhật runtime profile."""
        logger.info("Đang dò cấu hình phần cứng để chuẩn bị model local...")
        hw = detect_hardware()
        model_name, num_ctx = choose_model_for_hardware(hw)
        logger.info(
            "Phần cứng: RAM=%.2f/%.2fGB | CPU=%d luồng | VRAM=%.2fGB -> đề xuất %s (num_ctx=%d)",
            hw.avail_ram_gb,
            hw.total_ram_gb,
            hw.cpu_threads,
            hw.vram_total_gb,
            model_name,
            num_ctx,
        )
        if ensure_ollama_model(model_name, auto_pull=auto_pull):
            apply_runtime_config(self.config_path, model_name, num_ctx)
        else:
            logger.warning(
                "Model đề xuất '%s' chưa sẵn sàng (auto_pull=%s); giữ cấu hình hiện tại trong %s.",
                model_name,
                auto_pull,
                self.config_path,
            )

    def run_command(self, cmd: list[str], timeout_sec: int = 60) -> tuple[bool, str]:
        """Thực thi lệnh kiểm thử/kiểm tra và trả về (passed, combined_output)."""
        logger.info("Thực thi lệnh kiểm tra: %s", " ".join(cmd))
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout_sec,
            )
            combined = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
            passed = proc.returncode == 0
            logger.info("Kết quả lệnh (returncode=%d): passed=%s", proc.returncode, passed)
            return passed, combined.strip()
        except Exception as exc:
            logger.exception("Lỗi khi chạy lệnh %s: %s", cmd, exc)
            return False, str(exc)

    def _default_llm_patcher(self, prompt_text: str) -> str:
        """Gọi LocalLLMClient nếu cấu hình sẵn sàng; trả về mô tả phương án sửa."""
        client = LocalLLMClient(config_path=self.config_path)
        messages = [
            {
                "role": "system",
                "content": (
                    "Bạn là kỹ sư sửa lỗi Python. Chỉ đề xuất hướng sửa gọn, "
                    "đúng trọng tâm theo ngữ cảnh được cung cấp, giữ file dưới 300 dòng."
                ),
            },
            {"role": "user", "content": prompt_text},
        ]
        return client.chat(messages=messages)

    def run_loop(
        self,
        target_file: str,
        verify_cmd: list[str],
        apply_fix_fn: Callable[[str, str], str] | None = None,
        use_llm_suggestion: bool = False,
    ) -> RepairRunResult:
        """Chạy vòng lặp kiểm tra -> gom ngữ cảnh -> sửa -> kiểm tra lại tới khi đạt hoặc ngắt mạch."""
        logger.info("Bắt đầu RepairLoopRunner cho '%s' (use_llm_suggestion=%s)", target_file, use_llm_suggestion)
        if use_llm_suggestion:
            self.prepare_model_if_needed(auto_pull=False)

        ctx = self.context_builder.build_context(target_file=target_file, depth=1)
        last_output = ""

        while self.breaker.status.state == "CLOSED":
            passed, output = self.run_command(verify_cmd)
            last_output = output

            if passed:
                self.breaker.mark_recovered(action_summary=f"Lệnh {' '.join(verify_cmd)} đã pass.")
                return RepairRunResult(
                    target_file=target_file,
                    success=True,
                    breaker_status=self.breaker.status,
                    context_files=ctx["included_files"],
                    last_output=last_output,
                )

            if self.breaker.status.attempts_used + 1 >= self.breaker.max_retries:
                # Ghi nhận lần thất bại cuối cùng để kích hoạt TRIPPED theo đúng max_retries
                self.breaker.record_failure(
                    error_message=output[-1500:] or "Verify command failed",
                    action_summary="Chạm ngưỡng lượt sửa tối đa trước khi áp dụng thêm bản vá.",
                )
                break

            suggestion = ""
            if use_llm_suggestion:
                prompt_text = (
                    f"File đích: {target_file}\n"
                    f"Lỗi kiểm thử:\n{output[-2000:]}\n\n"
                    f"Ngữ cảnh liên quan:\n{ctx['context_text']}"
                )
                try:
                    suggestion = self._default_llm_patcher(prompt_text)
                except Exception as exc:
                    logger.warning("Không gọi được LLM cục bộ lúc này: %s", exc)
                    suggestion = ""

            action_note = "Không có hàm apply_fix_fn tự động."
            if apply_fix_fn is not None:
                action_note = apply_fix_fn(output, suggestion)

            ctx = self.context_builder.build_context(
                target_file=target_file,
                depth=1,
                extra_notes=f"Lần thử #{self.breaker.status.attempts_used + 1}\n{action_note}\n{suggestion[:1000]}",
            )
            self.breaker.record_failure(
                error_message=output[-1500:] or "Verify command failed",
                action_summary=action_note,
            )

        logger.warning(
            "Kết thúc RepairLoopRunner cho '%s': success=False | state=%s | reason=%s",
            target_file,
            self.breaker.status.state,
            self.breaker.status.trip_reason,
        )
        return RepairRunResult(
            target_file=target_file,
            success=False,
            breaker_status=self.breaker.status,
            context_files=ctx["included_files"],
            last_output=last_output,
        )


if __name__ == "__main__":
    from core.logger_setup import setup_logger

    setup_logger()
    runner = RepairLoopRunner(".")
    res = runner.run_loop(
        target_file="slices/doc_reconcile/core.py",
        verify_cmd=[
            sys.executable,
            "-m",
            "pytest",
            "--import-mode=importlib",
            "slices/doc_reconcile/test_doc_reconcile.py",
        ],
        use_llm_suggestion=False,
    )
    print("Success:", res.success, "| Breaker:", res.breaker_status.state)