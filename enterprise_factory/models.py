# File: enterprise_factory/models.py
from django.db import models

class Company(models.Model):
    """Bảng quản lý danh sách Công ty con / Khối ngành trong Tập đoàn"""
    code = models.CharField(max_length=50, primary_key=True, help_text="Mã công ty/khối ngành (VD: GOLD_CORP, FIN_CORP)")
    name = models.CharField(max_length=150, help_text="Tên hiển thị công ty")
    domain = models.CharField(max_length=100, help_text="Lĩnh vực hoạt động (Vàng bạc, Kế toán, Xây dựng...)")
    description = models.TextField(blank=True, null=True, help_text="Mô tả phạm vi nghiệp vụ")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.code}] {self.name}"


class AgentRegistry(models.Model):
    """Bảng quản lý hồ sơ nhân viên AI trong tập đoàn"""
    agent_id = models.CharField(max_length=50, primary_key=True, help_text="Mã định danh VD: BIZ_TAX_ACC_01")
    display_name = models.CharField(max_length=100, help_text="Tên hiển thị chuyên gia")
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='agents', help_text="Công ty thuộc về (Null = Cấp Tập đoàn)")
    department = models.CharField(max_length=100, help_text="Khối phòng ban")
    role_desc = models.TextField(help_text="Mô tả nhiệm vụ chuyên sâu")
    system_prompt = models.TextField(help_text="System Prompt chuẩn cho LLM")
    status = models.CharField(max_length=20, default='READY', help_text="Trạng thái hoạt động")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        comp_str = self.company.code if self.company else "GLOBAL"
        return f"[{comp_str}][{self.agent_id}] {self.display_name}"


class ProjectNode(models.Model):
    """Bảng lưu bản đồ mã nguồn và cấu trúc tệp (Thay thế PROJECT_MAP.md tĩnh)"""
    path = models.CharField(max_length=255, primary_key=True, help_text="Đường dẫn file/thư mục tương đối")
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='project_nodes')
    node_type = models.CharField(max_length=10, choices=[('DIR', 'Directory'), ('FILE', 'File')], default='FILE')
    purpose = models.TextField(help_text="Mục đích chức năng của file")
    line_count = models.IntegerField(default=0, help_text="Kiểm soát giới hạn < 300 dòng")
    ast_symbols = models.JSONField(default=list, help_text="Danh sách Class/Function trích xuất qua AST")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.path


class AgentTaskDAG(models.Model):
    """Bảng quản lý sơ đồ công việc DAG do BOD phân rã"""
    task_id = models.CharField(max_length=50, primary_key=True)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=200)
    assigned_agent = models.ForeignKey(AgentRegistry, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, default='PENDING', choices=[
        ('PENDING', 'Chờ thực thi'),
        ('RUNNING', 'Đang xử lý'),
        ('SUCCESS', 'Thành công'),
        ('FAILED', 'Thất bại')
    ])
    dependencies = models.JSONField(default=list, help_text="Danh sách task ID phải hoàn thành trước")
    result_output = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.task_id} - {self.title} ({self.status})"


class ExecutionLog(models.Model):
    """Bảng lưu vết toàn bộ tiến trình chạy của LangGraph và Ollama để AI đọc lại lỗi"""
    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True)
    node_name = models.CharField(max_length=100, help_text="Tên node trong LangGraph (VD: BA, Architect, Dev, QA)")
    prompt_sent = models.TextField(help_text="Prompt gửi vào Ollama")
    response_received = models.TextField(help_text="Phản hồi nhận được từ Ollama hoặc lỗi")
    status = models.CharField(max_length=20, default='SUCCESS', choices=[('SUCCESS', 'Thành công'), ('FAILED', 'Thất bại')])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        time_str = self.created_at.strftime('%H:%M:%S') if self.created_at else ""
        return f"[{time_str}] Node: {self.node_name} - {self.status}"