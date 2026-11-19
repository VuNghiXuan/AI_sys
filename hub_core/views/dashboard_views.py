# ==========================================
# File Path: hub_core/views/dashboard_views.py
# Module: Dashboard & Job Detail Views
# Linked Files: [hub_core/models.py, hub_core/services/pipeline_service.py, hub_core/views/stream_api_views.py]
# Purpose: Xử lý giao diện Live War Room, nhận domain/sub_domain, chạy pipeline ngầm và xem chi tiết job.
# ==========================================

import glob
import logging
import os
import threading
import uuid
from typing import Any, Dict, List, Optional

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from ..models import RequestJob, TaskExecutionLog
from ..services.pipeline_service import DjangoPipelineService

logger = logging.getLogger("vnxBox.Views.Dashboard")


def _list_generated_modules() -> List[Dict[str, Any]]:
    """Quét danh sách file module trong modules/ và generated_apps/ và chuẩn hóa đường dẫn."""
    generated_files: List[Dict[str, Any]] = []
    seen_paths = set()

    patterns = [
        ("modules/*.py", "modules"),
        ("generated_apps/*/*.py", "generated_apps"),
    ]

    for pattern, source_group in patterns:
        for filepath in glob.glob(pattern):
            if not os.path.isfile(filepath):
                continue
            clean_path = os.path.normpath(filepath).replace("\\", "/")
            if clean_path in seen_paths:
                continue
            seen_paths.add(clean_path)

            base_name = os.path.basename(clean_path)
            if source_group == "generated_apps":
                parts = clean_path.split("/")
                project_folder = parts[1] if len(parts) >= 3 else ""
                display_name = f"{project_folder}/{base_name}" if project_folder else base_name
            else:
                display_name = base_name

            generated_files.append({
                "filename": display_name,
                "path": clean_path,
                "size": os.path.getsize(clean_path),
                "source": source_group,
            })

    generated_files.sort(key=lambda item: item["path"])
    return generated_files


def run_pipeline_background(
    req_id: str,
    prompt: str,
    domain: str,
    sub_domain: Optional[str] = None,
) -> None:
    """Chạy ngầm Pipeline Multi-Agent để tránh đơ giao diện Web."""
    if sub_domain:
        logger.info(f"[BACKGROUND_WORKER] Job {req_id} chạy với sub_domain=[{sub_domain}].")
    else:
        logger.info(
            f"[BACKGROUND_WORKER] Job {req_id} không truyền sub_domain -> chạy mặc định domain=[{domain}] "
            f"(sẵn sàng nâng cấp chọn sub_domain sau)."
        )

    try:
        service = DjangoPipelineService(max_retries=2)
        service.execute_job(
            request_id=req_id,
            raw_prompt=prompt,
            domain=domain,
            sub_domain=sub_domain,
        )
    except Exception as e:
        logger.error(f"[BACKGROUND_WORKER] Lỗi thực thi Job {req_id}: {e}", exc_info=True)


def _extract_sub_domain_from_request(request) -> Optional[str]:
    """Lấy sub_domain từ POST form hoặc JSON body nếu có; nếu không có thì log nhắc nâng cấp."""
    raw_sub = request.POST.get("sub_domain")

    if not raw_sub and request.content_type and "application/json" in request.content_type:
        try:
            import json
            payload = json.loads(request.body.decode("utf-8") or "{}")
            if isinstance(payload, dict):
                raw_sub = payload.get("sub_domain")
        except Exception as e:
            logger.warning(f"[WEB_VIEW] Không đọc được JSON body để lấy sub_domain: {e}")

    cleaned = raw_sub.strip() if isinstance(raw_sub, str) and raw_sub.strip() else None
    if not cleaned:
        logger.info(
            "[WEB_VIEW] Request không kèm sub_domain -> dùng ngữ cảnh mặc định của domain "
            "(có thể bổ sung trường sub_domain ở UI/API khi nâng cấp)."
        )
    return cleaned


def dashboard_view(request):
    """Hiển thị giao diện 3 Cột Live War Room, kích hoạt job chạy ngầm và trả JSON cho SSE."""
    if request.method == "POST":
        prompt = request.POST.get("raw_prompt", "").strip()
        domain = (request.POST.get("domain") or "software").strip()
        sub_domain = _extract_sub_domain_from_request(request)

        if prompt:
            req_id = f"REQ_WEB_{uuid.uuid4().hex[:6].upper()}"
            logger.info(
                f"[WEB_VIEW] Khởi tạo Job chạy ngầm: {req_id} | Domain: {domain} | "
                f"SubDomain: {sub_domain or 'NONE'} | Prompt: {prompt[:50]}..."
            )

            job = RequestJob.objects.create(
                request_id=req_id,
                raw_prompt=prompt,
                domain=domain,
                status="RUNNING",
            )

            thread = threading.Thread(
                target=run_pipeline_background,
                args=(req_id, prompt, domain, sub_domain),
                daemon=True,
            )
            thread.start()

            return JsonResponse({
                "status": "STARTED",
                "job_id": str(job.job_id),
                "request_id": job.request_id,
                "domain": domain,
                "sub_domain": sub_domain,
                "job_status": "RUNNING",
            })

    jobs = RequestJob.objects.all().order_by("-created_at")[:20]
    active_job_id = request.GET.get("job_id")
    active_job = None
    task_logs = []

    if active_job_id:
        try:
            active_job = RequestJob.objects.get(job_id=active_job_id)
            task_logs = TaskExecutionLog.objects.filter(job=active_job).order_by("executed_at")
        except RequestJob.DoesNotExist:
            logger.warning(f"[WEB_VIEW] Không tìm thấy job_id={active_job_id}")
    elif jobs.exists():
        active_job = jobs.first()
        task_logs = TaskExecutionLog.objects.filter(job=active_job).order_by("executed_at")

    context = {
        "jobs": jobs,
        "active_job": active_job,
        "task_logs": task_logs,
        "generated_files": _list_generated_modules(),
    }
    return render(request, "hub_core/dashboard.html", context)


def job_detail_view(request, job_id):
    """Hiển thị màn hình chi tiết một Job và danh sách log thực thi."""
    job = get_object_or_404(RequestJob, job_id=job_id)
    task_logs = TaskExecutionLog.objects.filter(job=job).order_by("executed_at")
    jobs = RequestJob.objects.all().order_by("-created_at")[:20]

    context = {
        "job": job,
        "task_logs": task_logs,
        "jobs": jobs,
        "generated_files": _list_generated_modules(),
    }
    return render(request, "hub_core/job_detail.html", context)