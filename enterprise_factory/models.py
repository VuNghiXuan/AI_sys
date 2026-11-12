# File: enterprise_factory/models.py
"""
Mô hình dữ liệu cốt lõi cho Tập đoàn AI Tự trị vnxBox Enterprise.
Hỗ trợ quản lý đa công ty, hồ sơ nhân sự AI động, phân rã task DAG và kiểm định AST.
"""

from django.db import models

# File: enterprise_factory/models.py (Bổ sung model SystemConfig)

class SystemConfig(models.Model):
    """Bảng lưu cấu hình hệ thống / Tenant Owner động phục vụ thương mại hóa"""
    key = models.CharField(max_length=100, unique=True, verbose_name="Khóa cấu hình")
    value = models.TextField(verbose_name="Giá trị")
    description = models.TextField(blank=True, null=True, verbose_name="Mô tả")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Cập nhật lần cuối")

    def __str__(self):
        return f"{self.key} = {self.value}"

    class Meta:
        verbose_name = "Cấu hình Hệ thống"
        verbose_name_plural = "Danh mục Cấu hình Hệ thống"

        
class Company(models.Model):
    """Bảng quản lý khối ngành / tập đoàn đa lĩnh vực"""
    code = models.CharField(max_length=50, primary_key=True, help_text="Mã định danh (VD: GLOBAL, HTJ)")
    name = models.CharField(max_length=150, help_text="Tên hiển thị tập đoàn")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.code}] {self.name}"


class AgentRole(models.Model):
    """Bảng quản lý danh mục vai trò động cho tập đoàn AI"""
    role_code = models.CharField(max_length=50, primary_key=True, help_text="Mã chức vụ: BOD, HR, DEVOPS, SECURITY...")
    role_name = models.CharField(max_length=100, help_text="Tên hiển thị chức vụ: Kỹ sư DevOps, Chuyên gia Bảo mật...")
    description = models.TextField(blank=True, null=True, help_text="Mô tả chức năng nhiệm vụ của vai trò này")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.role_name} ({self.role_code})"

class AgentRegistry(models.Model):
    """Hồ sơ nhân sự AI trực chiến - Liên kết động với danh mục vai trò"""
    agent_id = models.CharField(max_length=50, primary_key=True, help_text="Mã định danh VD: BOD_CEO_01, DEVOPS_01")
    display_name = models.CharField(max_length=100, help_text="Tên hiển thị chuyên gia")
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='agents')
    
    # THAY VÌ CHOICES CỐ ĐỊNH, DÙNG FOREIGNOKEY TRỎ SANG BẢNG ROLE ĐỘNG
    role = models.ForeignKey(AgentRole, on_delete=models.SET_NULL, null=True, blank=True, related_name='agents')
    
    system_prompt = models.TextField(help_text="System Prompt chuẩn / Meta-Prompt của nhân sự")
    domain_scope = models.CharField(max_length=100, default='GENERAL', help_text="Lĩnh vực chuyên môn")
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


class DirectiveLog(models.Model):
    """Lưu vết toàn bộ chỉ đạo trực tiếp từ Sếp Vũ"""
    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True)
    directive_text = models.TextField(help_text="Nội dung chỉ đạo của Sếp")
    status = models.CharField(
        max_length=20, 
        default='PROCESSING', 
        choices=[('PROCESSING', 'Đang xử lý'), ('SUCCESS', 'Hoàn thành'), ('BLOCKED', 'Vướng ngoại lệ')]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.created_at.strftime('%H:%M:%S')}] {self.directive_text[:40]}..."


class AgentDiscussion(models.Model):
    """Nhật ký phòng họp Live War Room (Luồng thảo luận / tranh luận / báo cáo tiến độ real-time)"""
    
    SENDER_TYPES = [
        ('USER', 'Sếp (Người dùng)'),
        ('AGENT', 'Nhân sự AI'),
        ('SYSTEM', 'Hệ thống / Lệnh ngầm')
    ]

    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    directive = models.ForeignKey(DirectiveLog, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Người gửi
    sender_type = models.CharField(max_length=20, default='AGENT', choices=SENDER_TYPES, help_text="Phân loại nguồn gửi")
    agent = models.ForeignKey(AgentRegistry, on_delete=models.CASCADE, null=True, blank=True, help_text="Null nếu do Sếp hoặc System gửi")
    
    message_content = models.TextField(help_text="Nội dung phản hồi hoặc thảo luận")
    phase = models.CharField(
        max_length=50, 
        default='SMALL_TALK', 
        help_text="USER_DIRECTIVE, SMALL_TALK, CODE_DEV, GENERAL_DEBATE, DAG_DECOMPOSITION"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.sender_type == 'USER':
            sender_display = "Sếp Vũ"
        elif self.sender_type == 'SYSTEM':
            sender_display = "System Alert"
        else:
            sender_display = self.agent.display_name if self.agent else "AI Agent"
            
        return f"[{self.phase}] {sender_display}: {self.message_content[:40]}"


class CodePatchProposal(models.Model):
    """Bản vá code do Agent viết, đi kèm cơ chế Auto-Backup và duyệt 1-Click"""
    id = models.AutoField(primary_key=True)
    target_file = models.CharField(max_length=255, help_text="Đường dẫn file đích (VD: dynamic_app/services_gen.py)")
    proposed_by_agent = models.ForeignKey(AgentRegistry, on_delete=models.CASCADE)
    code_content = models.TextField(help_text="Mã nguồn AI sinh ra")
    status = models.CharField(
        max_length=20, 
        default='PENDING', 
        choices=[('PENDING', 'Chờ duyệt'), ('APPROVED', 'Đã áp dụng'), ('REJECTED', 'Từ chối')]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.status}] Patch for {self.target_file} by {self.proposed_by_agent}"


class AgentTaskDAG(models.Model):
    """Quản lý các bước công việc phân rã tự động (DAG StateGraph cho từng Directive)"""
    id = models.AutoField(primary_key=True)
    directive = models.ForeignKey(DirectiveLog, on_delete=models.CASCADE, related_name='tasks')
    assigned_agent = models.ForeignKey(AgentRegistry, on_delete=models.SET_NULL, null=True, blank=True)
    step_name = models.CharField(max_length=150, help_text="Tên bước công việc (VD: Phân tích Spec, Viết Model, Test AST)")
    step_order = models.IntegerField(default=1, help_text="Thứ tự thực hiện trong DAG")
    status = models.CharField(
        max_length=20, 
        default='PENDING', 
        choices=[('PENDING', 'Chờ chạy'), ('RUNNING', 'Đang thực thi'), ('COMPLETED', 'Đã xong'), ('FAILED', 'Lỗi')]
    )
    task_output = models.TextField(blank=True, null=True, help_text="Kết quả thực thi của bước task")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[Step {self.step_order}] {self.step_name} - {self.status}"


class ProjectNode(models.Model):
    """Bản đồ mã nguồn quét qua AST Scanner (Kiểm soát tuyệt đối định mức < 300 dòng/file)"""
    path = models.CharField(max_length=255, primary_key=True, help_text="Đường dẫn file")
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True)
    line_count = models.IntegerField(default=0, help_text="Số dòng code thực tế")
    created_by_agent = models.ForeignKey(AgentRegistry, on_delete=models.SET_NULL, null=True, blank=True)
    classes_defined = models.JSONField(default=list)
    functions_defined = models.JSONField(default=list)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.path} ({self.line_count} lines)"