# File: enterprise_factory/utils/ast_scanner.py
import os
import ast
from enterprise_factory.models import ProjectNode, AgentRegistry

def scan_and_register_file(file_path, company=None, agent_id=None):
    """
    Quét mã nguồn Python bằng AST (Abstract Syntax Tree):
    1. Đếm số dòng (kiểm soát quy chuẩn kiến trúc < 300 dòng).
    2. Trích xuất danh sách Class và Function để quản lý và chống trùng lặp.
    3. Cập nhật / Đồng bộ vào bảng ProjectNode của hệ thống.
    """
    if not os.path.exists(file_path):
        return None

    # Đọc nội dung file và đếm dòng
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.splitlines()
        line_count = len(lines)

    classes_defined = []
    functions_defined = []

    # Phân tích cú pháp AST tĩnh
    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes_defined.append(node.name)
            elif isinstance(node, ast.FunctionDef):
                functions_defined.append(node.name)
    except SyntaxError:
        # Nếu file code có lỗi cú pháp, vẫn ghi nhận line count nhưng bỏ qua phân tích AST chi tiết
        pass

    agent = AgentRegistry.objects.filter(agent_id=agent_id).first() if agent_id else None

    # Cập nhật hoặc tạo mới ProjectNode
    project_node, created = ProjectNode.objects.update_or_create(
        path=file_path,
        defaults={
            'company': company,
            'node_type': 'FILE',
            'purpose': f'Module tự sinh qua Vibercode Engine',
            'line_count': line_count,
            'created_by_agent': agent,
            'classes_defined': classes_defined,
            'functions_defined': functions_defined,
            'is_locked': False
        }
    )

    return project_node