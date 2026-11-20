# ==============================================================================
# File Path: core/background_jobs.py
# Description: Bộ chạy tác vụ nền gọn bằng ThreadPoolExecutor, lưu trạng thái & log từng job.
# Linked Files: [core/logger_setup.py, hub_core/views.py, hub_core/urls.py]
# Slice Tag: [CORE: BACKGROUND_JOBS]
# ==============================================================================

import logging
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

logger = logging.getLogger(__name__)


def _utc_now_iso() -> str:
    """Trả về mốc thời gian ISO-8601 chuẩn UTC."""
    return datetime.now(timezone.utc).isoformat()


@dataclass
class JobRecord:
    """Bản ghi trạng thái và nhật ký của một tác vụ chạy nền."""

    job_id: str
    task_type: str
    status: str = "queued"  # queued | running | completed | failed
    created_at: str = field(default_factory=_utc_now_iso)
    started_at: str | None = None
    finished_at: str | None = None
    progress: str = "Đang xếp hàng chạy nền"
    logs: list[str] = field(default_factory=list)
    result: Any = None
    error: str | None = None


class BackgroundJobManager:
    """Điều phối tác vụ nền bằng ThreadPoolExecutor và cung cấp trạng thái/log an toàn luồng."""

    def __init__(self, max_workers: int = 4, max_jobs_retained: int = 200) -> None:
        self.max_workers = max(1, max_workers)
        self.max_jobs_retained = max(20, max_jobs_retained)
        self._executor = ThreadPoolExecutor(
            max_workers=self.max_workers,
            thread_name_prefix="vnxbox_job",
        )
        self._lock = threading.Lock()
        self._jobs: dict[str, JobRecord] = {}
        self._order: list[str] = []

    def _append_log_locked(self, record: JobRecord, message: str) -> None:
        """Ghi thêm dòng log vào job (phải giữ self._lock trước khi gọi)."""
        stamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{stamp}] {message}"
        record.logs.append(line)
        if len(record.logs) > 500:
            record.logs = record.logs[-500:]

    def append_log(self, job_id: str, message: str) -> None:
        """Ghi log bổ sung từ bên trong tác vụ đang chạy."""
        with self._lock:
            record = self._jobs.get(job_id)
            if record is not None:
                self._append_log_locked(record, message)
            else:
                logger.warning("[Job %s] append_log bỏ qua vì không tìm thấy job_id", job_id)
                return
        logger.info("[Job %s] %s", job_id, message)

    def update_progress(self, job_id: str, progress: str, log_message: str | None = None) -> None:
        """Cập nhật nhãn tiến độ và tùy chọn ghi thêm log."""
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None:
                logger.warning("[Job %s] update_progress bỏ qua vì không tìm thấy job_id", job_id)
                return
            record.progress = progress
            if log_message:
                self._append_log_locked(record, log_message)
        if log_message:
            logger.info("[Job %s] %s (%s)", job_id, log_message, progress)

    def _prune_old_jobs_locked(self) -> None:
        """Giữ số lượng job trong bộ nhớ ở mức kiểm soát."""
        while len(self._order) > self.max_jobs_retained:
            oldest_id = self._order.pop(0)
            self._jobs.pop(oldest_id, None)

    def submit(
        self,
        task_type: str,
        fn: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Đưa một hàm xử lý vào ThreadPoolExecutor và trả về thông tin job khởi tạo."""
        job_id = uuid.uuid4().hex[:12]
        record = JobRecord(job_id=job_id, task_type=task_type)

        with self._lock:
            self._append_log_locked(record, f"Khởi tạo job '{task_type}' (id={job_id}).")
            self._jobs[job_id] = record
            self._order.append(job_id)
            self._prune_old_jobs_locked()

        logger.info("Đã xếp hàng job nền id=%s | type=%s", job_id, task_type)
        self._executor.submit(self._run_wrapper, job_id, fn, args, kwargs)
        return self.get_job(job_id, log_offset=0) or {}

    def _run_wrapper(
        self,
        job_id: str,
        fn: Callable[..., Any],
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> None:
        """Bao bọc thực thi tác vụ nền để luôn cập nhật trạng thái & bắt lỗi an toàn."""
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None:
                logger.error("Job nền id=%s không tồn tại trong _jobs khi bắt đầu chạy", job_id)
                return
            record.status = "running"
            record.started_at = _utc_now_iso()
            record.progress = "Đang thực thi"
            self._append_log_locked(record, "Bắt đầu chạy trong luồng nền.")

        logger.info("Bắt đầu thực thi job nền id=%s", job_id)
        try:
            call_kwargs = dict(kwargs)
            if call_kwargs.pop("_inject_job_id", False):
                call_kwargs["job_id"] = job_id
            output = fn(*args, **call_kwargs)
        except Exception as exc:
            logger.exception("Job nền id=%s gặp lỗi: %s", job_id, exc)
            with self._lock:
                record = self._jobs.get(job_id)
                if record is not None:
                    record.status = "failed"
                    record.error = str(exc)
                    record.progress = "Thất bại"
                    record.finished_at = _utc_now_iso()
                    self._append_log_locked(record, f"Lỗi thực thi: {exc}")
            return

        with self._lock:
            record = self._jobs.get(job_id)
            if record is not None:
                record.status = "completed"
                record.result = output
                record.progress = "Hoàn tất"
                record.finished_at = _utc_now_iso()
                self._append_log_locked(record, "Hoàn tất tác vụ nền.")
        logger.info("Hoàn tất job nền id=%s", job_id)

    def get_job(self, job_id: str, log_offset: int = 0) -> dict[str, Any] | None:
        """Lấy trạng thái hiện tại và log mới từ vị trí log_offset."""
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None:
                return None
            safe_offset = max(0, min(log_offset, len(record.logs)))
            sliced_logs = record.logs[safe_offset:]
            return {
                "job_id": record.job_id,
                "task_type": record.task_type,
                "status": record.status,
                "created_at": record.created_at,
                "started_at": record.started_at,
                "finished_at": record.finished_at,
                "progress": record.progress,
                "error": record.error,
                "result": record.result,
                "log_offset": safe_offset,
                "total_logs": len(record.logs),
                "logs": sliced_logs,
            }

    def list_jobs(self, limit: int = 20) -> list[dict[str, Any]]:
        """Liệt kê các job gần nhất (mới nhất trước)."""
        with self._lock:
            ids = list(reversed(self._order[-max(1, limit) :]))
            items: list[dict[str, Any]] = []
            for jid in ids:
                rec = self._jobs.get(jid)
                if rec is not None:
                    items.append(
                        {
                            "job_id": rec.job_id,
                            "task_type": rec.task_type,
                            "status": rec.status,
                            "created_at": rec.created_at,
                            "started_at": rec.started_at,
                            "finished_at": rec.finished_at,
                            "progress": rec.progress,
                            "total_logs": len(rec.logs),
                            "has_error": rec.error is not None,
                        }
                    )
            return items


_DEFAULT_MANAGER: BackgroundJobManager | None = None
_MANAGER_LOCK = threading.Lock()


def get_job_manager() -> BackgroundJobManager:
    """Lấy singleton BackgroundJobManager dùng chung cho tiến trình."""
    global _DEFAULT_MANAGER
    with _MANAGER_LOCK:
        if _DEFAULT_MANAGER is None:
            _DEFAULT_MANAGER = BackgroundJobManager(max_workers=4)
        return _DEFAULT_MANAGER