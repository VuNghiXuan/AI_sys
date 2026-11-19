# ==========================================
# File Path: hub_core/views/stream_api_views.py
# Module: File Content, SSE Stream & Job Delete APIs
# Linked Files: [hub_core/models.py, hub_core/views/dashboard_views.py]
# Purpose: Cung cấp API đọc nội dung file sinh ra, stream log real-time qua SSE và xóa job.
# ==========================================

import json
import logging
import os
import time

from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404

from ..models import RequestJob, TaskExecutionLog

logger = logging.getLogger("vnxBox.Views.StreamAPI")


ALLOWED_PREVIEW_PREFIXES = ("modules/", "generated_apps/")


def _is_safe_preview_path(filepath: str) -> bool:
    """Kiểm tra đường dẫn file nằm trong thư mục được phép xem nhanh và chống path traversal."""
    normalized = os.path.normpath(filepath).replace("\\", "/")
    if not normalized or normalized.startswith("../") or "/../" in normalized:
        return False
    if not normalized.startswith(ALLOWED_PREVIEW_PREFIXES):
        return False
    if "/venv/" in f"/{normalized}/" or "/__pycache__/" in f"/{normalized}/":
        return False
    return os.path.isfile(normalized)


def file_content_api(request):
    """API đọc nội dung file cho cột bên phải (hỗ trợ modules/ và generated_apps/, cả Windows & Linux path)."""
    raw_path = request.GET.get("path", "").strip()
    filepath = os.path.normpath(raw_path).replace("\\", "/") if raw_path else ""

    if filepath and _is_safe_preview_path(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            logger.info(f"[FILE_API] Đọc file thành công: {filepath}")
            return JsonResponse({
                "success": True,
                "content": content,
                "path": filepath,
                "filename": os.path.basename(filepath),
            })
        except Exception as e:
            logger.error(f"[FILE_API] Lỗi đọc file {filepath}: {e}", exc_info=True)
            return JsonResponse({"success": False, "error": str(e)})

    logger.warning(f"[FILE_API] Không tìm thấy hoặc đường dẫn không hợp lệ: {filepath}")
    return JsonResponse({"success": False, "error": f"File not found: {filepath}"})


def job_stream_view(request, job_id):
    """Stream tiến trình thực thi của từng Agent qua SSE mỗi 0.8 giây."""
    job = get_object_or_404(RequestJob, job_id=job_id)

    def event_stream():
        while True:
            job.refresh_from_db()
            logs = list(
                TaskExecutionLog.objects.filter(job=job)
                .order_by("executed_at")
                .values("task_name", "agent_assigned", "status", "output_result", "error_message")
            )

            data = {
                "status": job.status,
                "attempts": job.attempts,
                "logs": logs,
            }

            yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

            if job.status in ["SUCCESS", "FAILED"]:
                logger.info(f"[SSE_STREAM] Kết thúc stream cho job {job_id} với trạng thái {job.status}.")
                break

            time.sleep(0.8)

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    return response


def delete_job_api(request, job_id):
    """API xóa một Job cụ thể và các log liên quan, trả về JSON chuẩn mực."""
    if request.method == "POST":
        try:
            job = get_object_or_404(RequestJob, job_id=job_id)
            job.delete()
            logger.info(f"[DELETE_JOB_API] Đã xóa job {job_id} thành công.")
            return JsonResponse({"success": True, "message": f"Đã xóa thành công job {job_id}"})
        except Exception as e:
            logger.error(f"[DELETE_JOB_API] Lỗi khi xóa job {job_id}: {e}", exc_info=True)
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    return JsonResponse({"success": False, "error": "Invalid HTTP method"}, status=400)