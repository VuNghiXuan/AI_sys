"""
Mô hình quản lý chỉ đạo (Directive), phòng họp Live War Room, bản vá code, 
DAG Task, Kho quy trình (WorkflowBlueprint) và Kho công cụ (ToolRegistry) cho vnxBox Enterprise.
"""

from django.db import models
from .base import Company
from .agent import AgentRegistry

class DirectiveLog(models.Model):
    """Lưu vết toàn bộ chỉ đạo trực tiếp từ Người dùng / Sếp"""
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
        ('USER', 'Người dùng (Sếp)'),
        ('AGENT', 'Nhân sự AI'),
        ('SYSTEM', 'Hệ thống / Lệnh ngầm')
    ]

    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    directive = models.ForeignKey(DirectiveLog, on_delete=models.SET_NULL, null=True, blank=True)
    
    sender_type = models.CharField(max_length=20, default='AGENT', choices=SENDER_TYPES, help_text="Phân loại nguồn gửi")
    agent = models.ForeignKey(AgentRegistry, on_delete=models.CASCADE, null=True, blank=True, help_text="Null nếu do Sếp hoặc System gửi")
    
    message_content = models.TextField(help_text="Nội dung phản hồi hoặc thảo luận")
    phase = models.CharField(
        max_length=50, 
        default='SMALL_TALK', 
        help_text="USER_DIRECTIVE, SMALL_TALK, CODE_DEV, GENERAL_DEBATE, DAG_DECOMPOSITION"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def get_sender_display_name(self):
        """Lấy tên hiển thị linh hoạt theo loại nguồn gửi (Chuẩn Enterprise SaaS)"""
        if self.sender_type == 'USER':
            return "Sếp Vũ" 
        elif self.sender_type == 'SYSTEM':
            return "Hệ thống vnxBox"
        else:
            return self.agent.display_name if self.agent else "AI Agent"


class CodePatchProposal(models.Model):
    """Bản vá code do Agent viết, đi kèm cơ chế Auto-Backup và duyệt 1-Click"""
    id = models.AutoField(primary_key=True)
    target_file = models.CharField(max_length=255, help_text="Đường dẫn file đích (VD: enterprise_factory/services/sandbox.py)")
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
        return f"[Step {self.step_order}] {self.step_name} - Status: {self.status}"


# --- 🚀 BỔ SUNG THÁP 1 & THÁP 2: KHO CÔNG CỤ & KHO QUY TRÌNH ĐỘNG ---

class ToolRegistry(models.Model):
    """Tháp 1: Kho tàng công cụ động (Database-Driven Tools cho AI Agent sử dụng)"""
    tool_name = models.CharField(max_length=100, unique=True, help_text="Tên định danh công cụ (VD: web_search_tool, sql_query_tool)")
    display_name = models.CharField(max_length=150, help_text="Tên hiển thị tiếng Việt")
    description = models.TextField(help_text="Mô tả chức năng để Agent biết khi nào nên gọi tool này")
    parameters_schema = models.JSONField(default=dict, help_text="Schema định nghĩa tham số đầu vào (JSON)")
    python_code_snippet = models.TextField(help_text="Đoạn mã Python thực thi code động (JIT Generated)")
    is_active = models.BooleanField(default=True, help_text="Trạng thái kích hoạt công cụ")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Tool: {self.tool_name} ({'Active' if self.is_active else 'Disabled'})"


class WorkflowBlueprint(models.Model):
    """Tháp 2: Bản đồ quy trình DAG động (Tái sử dụng các chuỗi nghiệp vụ phức tạp)"""
    workflow_code = models.CharField(max_length=100, unique=True, help_text="Mã quy trình (VD: HIRE_NEW_AI_EXPERT, CODE_REVIEW_PIPELINE)")
    workflow_name = models.CharField(max_length=200, help_text="Tên quy trình nghiệp vụ")
    dag_steps_json = models.JSONField(default=list, help_text="Cấu trúc các bước DAG dưới dạng danh sách JSON")
    is_active = models.BooleanField(default=True, help_text="Trạng thái hiệu lực của quy trình")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Workflow: {self.workflow_code} - {self.workflow_name}"