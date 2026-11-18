"""
# File Path: hub_core/models.py
# File Purpose: Định nghĩa Database Schema cho vnxBox Enterprise (Quản lý Job, Task Log, Agent Manifest, Workflow DAG).
# Connected Files: [hub_core/admin.py, core/pipeline_runner.py]
# Logs: Quản lý trạng thái quan hệ cơ sở dữ liệu cho toàn bộ hệ thống Multi-Agent.
"""

import uuid
from django.db import models

class AgentManifestModel(models.Model):
    """
    # Model: AgentManifestModel
    # Purpose: Lưu trữ cấu hình JSON của các Agent (Plug-and-Play cho phép thêm Agent ngành nghề mới mà không sửa code).
    """
    agent_id = models.CharField(max_length=100, unique=True, verbose_name="Mã định danh Agent")
    role_description = models.TextField(verbose_name="Mô tả vai trò")
    system_prompt = models.TextField(verbose_name="System Prompt chuyên biệt")
    domain = models.CharField(max_length=50, default="software", verbose_name="Lĩnh vực (software, legal, sales...)")
    is_active = models.BooleanField(default=True, verbose_name="Trạng thái hoạt động")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.domain.upper}] {self.agent_id}"


class RequestJob(models.Model):
    """
    # Model: RequestJob
    # Purpose: Lưu trữ thông tin từng yêu cầu lớn từ người dùng gửi vào hệ thống.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Đang chờ xử lý'),
        ('RUNNING', 'Đang thực thi chuỗi DAG'),
        ('SUCCESS', 'Nghiệm thu thành công'),
        ('FAILED', 'Thất bại / Cần con người duyệt'),
    ]

    job_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="Mã Job UUID")
    request_id = models.CharField(max_length=50, unique=True, verbose_name="Mã Request hiển thị")
    raw_prompt = models.TextField(verbose_name="Yêu cầu thô từ người dùng")
    domain = models.CharField(max_length=50, default="software", verbose_name="Lĩnh vực xử lý")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name="Trạng thái")
    attempts = models.IntegerField(default=0, verbose_name="Số lần thử nghiệm (Circuit Breaker)")
    output_file_path = models.CharField(max_length=255, blank=True, null=True, verbose_name="Đường dẫn file kết quả")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Thời gian tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Cập nhật lần cuối")

    def __str__(self):
        return f"Job {self.request_id} - Status: {self.status}"


class TaskExecutionLog(models.Model):
    """
    # Model: TaskExecutionLog
    # Purpose: Lưu chi tiết kết quả từng bước nhỏ trong sơ đồ DAG (Micro-Loop log, phục vụ việc kiểm tra và tự sửa lỗi).
    """
    job = models.ForeignKey(RequestJob, on_delete=models.CASCADE, related_name="task_logs", verbose_name="Thuộc Job")
    task_name = models.CharField(max_length=100, verbose_name="Tên tác vụ (VD: Task_1_Design)")
    agent_assigned = models.CharField(max_length=100, verbose_name="Agent phụ trách")
    status = models.CharField(max_length=20, default='PENDING', verbose_name="Trạng thái bước")
    input_payload = models.TextField(blank=True, null=True, verbose_name="Dữ liệu đầu vào / Spec")
    output_result = models.TextField(blank=True, null=True, verbose_name="Kết quả đầu ra / Code sinh ra")
    error_message = models.TextField(blank=True, null=True, verbose_name="Log lỗi (nếu có)")
    attempt_count = models.IntegerField(default=1, verbose_name="Lần chạy thứ")
    executed_at = models.DateTimeField(auto_now_add=True, verbose_name="Thời điểm thực thi")

    def __str__(self):
        return f"[{self.task_name}] Job {self.job.request_id} - Status: {self.status}"