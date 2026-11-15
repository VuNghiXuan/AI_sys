# enterprise_factory/models/agent.py
"""
Mô hình quản lý vai trò, hồ sơ nhân sự AI động và yêu cầu tuyển dụng (HR Spawner) cho vnxBox Enterprise.
"""

from django.db import models
from .base import Company

class AgentRole(models.Model):
    """Bảng quản lý danh mục vai trò động cho tập đoàn AI"""
    role_code = models.CharField(max_length=50, primary_key=True, help_text="Mã chức vụ: BOD, HR, DEVOPS, SECURITY...")
    role_name = models.CharField(max_length=100, help_text="Tên hiển thị chức vụ: Kỹ sư DevOps, Chuyên gia Bảo mật...")
    description = models.TextField(blank=True, null=True, help_text="Mô tả chức năng nhiệm vụ của vai trò này")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.role_name} ({self.role_code})"


class AgentRegistry(models.Model):
    """Hồ sơ nhân sự AI trực chiến - Liên kết động với danh mục vai trò, hỗ trợ mở rộng Avatar, Profile"""
    agent_id = models.CharField(max_length=50, primary_key=True, help_text="Mã định danh VD: BOD_CEO_01, DEVOPS_01")
    display_name = models.CharField(max_length=100, help_text="Tên hiển thị chuyên gia")
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='agents')
    
    role = models.ForeignKey(AgentRole, on_delete=models.SET_NULL, null=True, blank=True, related_name='agents')
    
    system_prompt = models.TextField(help_text="System Prompt chuẩn / Meta-Prompt của nhân sự")
    domain_scope = models.CharField(max_length=100, default='GENERAL', help_text="Lĩnh vực chuyên môn")
    
    avatar_url = models.CharField(max_length=255, blank=True, null=True, help_text="Đường dẫn ảnh đại diện / Avatar")
    title_name = models.CharField(max_length=150, blank=True, null=True, help_text="Chức danh chi tiết (VD: Tổng Giám Đốc Điều Hành)")
    
    risk_threshold = models.CharField(
        max_length=30, 
        default='HITL_REQUIRED', 
        choices=[('AUTO_APPLY', 'Tự động áp dụng (Rủi ro thấp)'), ('HITL_REQUIRED', 'Chờ Sếp duyệt (Rủi ro cao)')]
    )
    version = models.CharField(max_length=20, default='1.0.0')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        role_code = self.role.role_code if self.role else "UNKNOWN"
        return f"[{role_code}] {self.display_name} ({self.agent_id})"


class JobOpening(models.Model):
    """Bảng quản lý vị trí tuyển dụng AI tự động (HR Agent Spawner & Recruitment Profile)"""
    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='job_openings')
    position_title = models.CharField(max_length=150, help_text="Tên vị trí cần tuyển (VD: Chuyên gia Blockchain / Senior DBA)")
    job_description = models.TextField(help_text="Mô tả công việc (JD) do BOD/HR định nghĩa khi hệ thống thiếu chuyên môn")
    required_domain = models.CharField(max_length=100, help_text="Lĩnh vực chuyên môn yêu cầu")
    suggested_prompt = models.TextField(help_text="Gợi ý System Prompt / Profile khởi tạo cho nhân sự AI mới")
    status = models.CharField(
        max_length=20,
        default='PENDING_APPROVAL',
        choices=[('PENDING_APPROVAL', 'Chờ Sếp duyệt tuyển'), ('ACTIVE', 'Đã tuyển & Kích hoạt'), ('REJECTED', 'Từ chối')]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.status}] Tuyển vị trí: {self.position_title}"