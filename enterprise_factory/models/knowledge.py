# enterprise_factory/models/knowledge.py
"""
Mô hình quản lý bản đồ mã nguồn AST (ProjectNode) và bộ nhớ ý định động (IntentMemory) cho vnxBox Enterprise.
"""

from django.db import models
from .base import Company
from .agent import AgentRegistry

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

class IntentMemory(models.Model):
    """Bảng lưu trữ bộ nhớ mẫu động (Dynamic Few-Shot Learning & Hybrid Intent Memory)"""
    id = models.AutoField(primary_key=True)
    query_text = models.TextField(unique=True, help_text="Câu hỏi gốc của Sếp")
    intent_code = models.CharField(max_length=50, help_text="Mã ý định: DB_QUERY, DEEP_CODE, LLM_CHAT...")
    target_agent = models.CharField(max_length=50, default='ALL', help_text="Agent phụ trách")
    response_payload = models.JSONField(null=True, blank=True)
    tier = models.IntegerField(default=1, help_text="Phân tầng xử lý (1, 2, 3)")
    feedback_type = models.CharField(
        max_length=20, 
        default='LIKE', 
        help_text="LOVE (❤️), LIKE (👍), DISLIKE (👎), CORRECT (🎯)"
    )
    vector_json = models.TextField(blank=True, null=True, help_text="Lưu Vector embedding dạng chuỗi JSON để tính Cosine Similarity offline")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"[{self.intent_code}] {self.query_text[:30]} ({self.feedback_type})"