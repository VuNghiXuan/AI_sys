"""
# File Path: hub_core/views.py
# Purpose: Controller views cho giao diện 3-Column Enterprise Workspace (Async Threading & Real-time SSE).
"""

import os
import uuid
import glob
import json
import time
import logging
import threading
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, StreamingHttpResponse
from .models import RequestJob, TaskExecutionLog
from .services.pipeline_service import DjangoPipelineService

logger = logging.getLogger("vnxBox.Views")

def run_pipeline_background(req_id: str, prompt: str, domain: str):
    """Hàm chạy ngầm Pipeline Multi-Agent để không làm đơ giao diện Web."""
    try:
        service = DjangoPipelineService(max_retries=2)
        service.execute_job(request_id=req_id, raw_prompt=prompt, domain=domain)
    except Exception as e:
        logger.error(f"[BACKGROUND_WORKER] Lỗi thực thi Job {req_id}: {e}")

def dashboard_view(request):
    """
    # View: dashboard_view
    # Purpose: Hiển thị giao diện 3 Cột Live War Room, kích hoạt job chạy ngầm và trả về ngay lập tức cho SSE.
    """
    if request.method == "POST":
        prompt = request.POST.get("raw_prompt", "").strip()
        domain = request.POST.get("domain", "software")
        
        if prompt:
            req_id = f"REQ_WEB_{uuid.uuid4().hex[:6].upper()}"
            logger.info(f"[WEB_VIEW] Khởi tạo Job chạy ngầm: {req_id} - Prompt: {prompt[:50]}...")
            
            # 1. Tạo bản ghi Job trong DB ngay lập tức với trạng thái RUNNING
            job = RequestJob.objects.create(
                request_id=req_id,
                raw_prompt=prompt,
                domain=domain,
                status="RUNNING"
            )
            
            # 2. Đẩy toàn bộ quá trình AI chạy sang luồng ngầm (Background Thread)
            thread = threading.Thread(
                target=run_pipeline_background,
                args=(req_id, prompt, domain),
                daemon=True
            )
            thread.start()
            
            # 3. Trả về JSON ngay lập tức (0.05s) để Frontend mở SSE theo dõi real-time
            return JsonResponse({
                "status": "STARTED", 
                "job_id": str(job.job_id), 
                "request_id": job.request_id,
                "job_status": "RUNNING"
            })

    jobs = RequestJob.objects.all().order_by('-created_at')[:20]
    
    active_job_id = request.GET.get('job_id')
    active_job = None
    task_logs = []

    if active_job_id:
        try:
            active_job = RequestJob.objects.get(job_id=active_job_id)
            task_logs = TaskExecutionLog.objects.filter(job=active_job).order_by('executed_at')
        except RequestJob.DoesNotExist:
            pass
    elif jobs.exists():
        active_job = jobs.first()
        task_logs = TaskExecutionLog.objects.filter(job=active_job).order_by('executed_at')

    # Quét danh sách file và chuẩn hóa dấu gạch chéo '/' cho Windows
    generated_files = []
    if os.path.exists("modules"):
        for f in glob.glob("modules/*.py"):
            clean_path = f.replace("\\", "/")
            generated_files.append({
                "filename": os.path.basename(f),
                "path": clean_path,
                "size": os.path.getsize(f)
            })

    context = {
        "jobs": jobs,
        "active_job": active_job,
        "task_logs": task_logs,
        "generated_files": generated_files,
    }
    return render(request, "hub_core/dashboard.html", context)


def job_detail_view(request, job_id):
    job = get_object_or_404(RequestJob, job_id=job_id)
    task_logs = TaskExecutionLog.objects.filter(job=job).order_by('executed_at')
    jobs = RequestJob.objects.all().order_by('-created_at')[:20]
    
    generated_files = []
    if os.path.exists("modules"):
        for f in glob.glob("modules/*.py"):
            generated_files.append({
                "filename": os.path.basename(f),
                "path": f.replace("\\", "/"),
            })

    context = {
        "job": job,
        "task_logs": task_logs,
        "jobs": jobs,
        "generated_files": generated_files
    }
    return render(request, "hub_core/job_detail.html", context)


def file_content_api(request):
    """API đọc nội dung file cho cột bên phải (hỗ trợ cả Windows & Linux path)."""
    filepath = request.GET.get("path", "").replace("\\", "/")
    if filepath and os.path.exists(filepath) and filepath.startswith("modules/"):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            return JsonResponse({
                "success": True, 
                "content": content, 
                "path": filepath, 
                "filename": os.path.basename(filepath)
            })
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "error": f"File not found: {filepath}"})


def job_stream_view(request, job_id):
    """Stream tiến trình thực thi của từng Agent qua SSE mỗi 0.8 giây."""
    job = get_object_or_404(RequestJob, job_id=job_id)

    def event_stream():
        while True:
            job.refresh_from_db()
            logs = list(TaskExecutionLog.objects.filter(job=job).order_by('executed_at').values(
                'task_name', 'agent_assigned', 'status', 'output_result', 'error_message'
            ))
            
            data = {
                "status": job.status,
                "attempts": job.attempts,
                "logs": logs
            }

            yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

            if job.status in ['SUCCESS', 'FAILED']:
                break

            time.sleep(0.8)

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response['Cache-Control'] = 'no-cache'
    return response

def delete_job_api(request, job_id):
    """API xóa một Job cụ thể và các log liên quan, trả về JSON chuẩn mực."""
    if request.method == "POST":
        try:
            job = get_object_or_404(RequestJob, job_id=job_id)
            job.delete()
            return JsonResponse({"success": True, "message": f"Đã xóa thành công job {job_id}"})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)
    return JsonResponse({"success": False, "error": "Invalid HTTP method"}, status=400)