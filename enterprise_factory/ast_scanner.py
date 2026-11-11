# File: enterprise_factory/ast_scanner.py
"""
AST Scanner & Code Inspector cho vnxBox Enterprise.
Chịu trách nhiệm quét cấu trúc mã nguồn, kiểm tra định mức dưới 300 dòng/file,
trích xuất danh sách Class/Function và đồng bộ hóa vào Django ORM (ProjectNode).
"""

import ast
import os
from .models import ProjectNode, AgentRegistry


class ASTCodeScanner:
    """Bộ phân tích cú pháp trừu tượng (AST) để kiểm định chất lượng mã nguồn Vibercode"""

    @staticmethod
    def scan_file(file_path: str, company_code: str = None, agent_id: str = None) -> dict:
        """
        Quét một file mã nguồn Python, đếm số dòng, trích xuất classes/functions
        và kiểm tra xem có vi phạm giới hạn < 300 dòng hay không.
        """
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"Không tìm thấy file tại đường dẫn: {file_path}"
            }

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code_content = f.read()

            # 1. Đếm số dòng thực tế
            lines = code_content.splitlines()
            line_count = len(lines)

            # 2. Phân tích AST để lấy danh sách Class và Function
            tree = ast.parse(code_content)
            classes_defined = []
            functions_defined = []

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes_defined.append({
                        "name": node.name,
                        "lineno": node.lineno
                    })
                elif isinstance(node, ast.FunctionDef):
                    functions_defined.append({
                        "name": node.name,
                        "lineno": node.lineno
                    })

            # 3. Kiểm tra vi phạm giới hạn dòng code (< 300 dòng)
            is_oversized = line_count > 300

            # 4. Lưu hoặc cập nhật vào ProjectNode trong cơ sở dữ liệu
            agent_obj = AgentRegistry.objects.filter(agent_id=agent_id).first() if agent_id else None
            
            project_node, created = ProjectNode.objects.update_or_create(
                path=file_path,
                defaults={
                    "line_count": line_count,
                    "created_by_agent": agent_obj,
                    "classes_defined": classes_defined,
                    "functions_defined": functions_defined
                }
            )

            return {
                "success": True,
                "file_path": file_path,
                "line_count": line_count,
                "is_oversized": is_oversized,
                "warning": "⚠️ CẢNH BÁO: File vượt quá định mức 300 dòng! Cần thực hiện File Splitting." if is_oversized else None,
                "classes_count": len(classes_defined),
                "functions_count": len(functions_defined)
            }

        except SyntaxError as se:
            return {
                "success": False,
                "error_type": "SyntaxError",
                "message": f"Lỗi cú pháp Python tại dòng {se.lineno}: {se.msg}"
            }
        except Exception as e:
            return {
                "success": False,
                "error_type": type(e).__name__,
                "message": str(e)
            }