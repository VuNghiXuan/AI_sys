# File: enterprise_factory/models.py
from django.db import models

class Company(models.Model):
    """Bảng quản lý khối ngành / tập đoàn"""
    code = models.CharField(max_length=50, primary_key=True, help_text="Mã định danh (VD: GLOBAL)")
    name = models.CharField(max_length=150, help_text="Tên hiển thị")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.code}] {self.name}"


class AgentRegistry(models.Model):
    """Hồ sơ nhân sự AI trực chiến (BOD_CEO_01 & DEV_BE_01)"""
    AGENT_ROLES = [
        ('BOD', 'Ban Giám Đốc / Điều hành'),
        ('DEV_BE', 'Lập trình viên Backend')
    ]
    
    agent_id = models.CharField(max_length=50, primary_key=True, help_text="Mã định danh VD: BOD_CEO_01, DEV_BE_01")
    display_name = models.CharField(max_length=100, help_text="Tên hiển thị chuyên gia")
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='agents')
    role_type = models.CharField(max_length=20, choices=AGENT_ROLES, default='DEV_BE')
    system_prompt = models.TextField(help_text="System Prompt chuẩn của nhân sự")
    version = models.CharField(max_length=20, default='1.0.0')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.role_type}] {self.display_name} ({self.agent_id})"


class DirectiveLog(models.Model):
    """Lưu vết toàn bộ chỉ đạo trực tiếp từ Sếp"""
    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True)
    directive_text = models.TextField(help_text="Nội dung chỉ đạo của Sếp")
    status = models.CharField(max_length=20, default='PROCESSING', choices=[('PROCESSING', 'Đang xử lý'), ('SUCCESS', 'Hoàn thành')])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.created_at.strftime('%H:%M:%S')}] {self.directive_text[:40]}..."


class AgentDiscussion(models.Model):
    """Nhật ký phòng họp Viber Room (Hiển thị luồng trò chuyện / phản hồi của Agent hoặc Sếp)"""
    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    directive = models.ForeignKey(DirectiveLog, on_delete=models.SET_NULL, null=True, blank=True)
    agent = models.ForeignKey(AgentRegistry, on_delete=models.CASCADE, null=True, blank=True) # <-- Đảm bảo có null=True, blank=True
    message_content = models.TextField(help_text="Nội dung phản hồi hoặc chỉ đạo")
    phase = models.CharField(max_length=50, default='SMALL_TALK', help_text="USER_DIRECTIVE, SMALL_TALK, CODE_DEV, GENERAL_DEBATE")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        agent_name = self.agent.display_name if self.agent else "Sếp Vũ"
        return f"[{self.phase}] {agent_name}: {self.message_content[:40]}"

class CodePatchProposal(models.Model):
    """Bản vá code do DEV_BE_01 viết, chờ Sếp review và bấm Approve & Apply Code"""
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


class ProjectNode(models.Model):
    """Bản đồ mã nguồn được quét qua AST Scanner (Kiểm soát line count < 300 dòng)"""
    path = models.CharField(max_length=255, primary_key=True, help_text="Đường dẫn file")
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True)
    line_count = models.IntegerField(default=0, help_text="Số dòng code thực tế")
    created_by_agent = models.ForeignKey(AgentRegistry, on_delete=models.SET_NULL, null=True, blank=True)
    classes_defined = models.JSONField(default=list)
    functions_defined = models.JSONField(default=list)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.path} ({self.line_count} lines)"