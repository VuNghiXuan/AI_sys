# File: enterprise_factory/ast_scanner.py
import os
import ast
import logging

logger = logging.getLogger(__name__)

class ASTCodeScanner:
    def __init__(self, project_root="."):
        self.project_root = project_root

    def scan_file(self, file_path):
        """
        Quét file thông minh:
        - Nếu là file .py: Dùng AST trích xuất classes, methods, imports chi tiết cho AI học code.
        - Nếu là file khác (.html, .js, .json, v.v.): Ghi nhận metadata và nội dung thô 
          để AI có mẫu mà tham chiếu, sửa đổi sau này.
        """
        result = {
            "file_path": file_path,
            "file_type": "python" if file_path.endswith(".py") else "asset/markup",
            "classes": [],
            "functions": [],
            "imports": [],
            "raw_snippet": ""
        }
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Xử lý riêng cho file Python bằng AST
            if file_path.endswith(".py"):
                tree = ast.parse(content, filename=file_path)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                        result["classes"].append({
                            "name": node.name,
                            "methods": methods
                        })
                    elif isinstance(node, ast.FunctionDef):
                        result["functions"].append(node.name)
                    elif isinstance(node, (ast.Import, ast.ImportFrom)):
                        for alias in node.names:
                            result["imports"].append(alias.name)
                logger.info(f"Đã quét thành công Python AST: {file_path}")
            else:
                # Đối với các file non-Python (.html, .js, .css, .md...), lưu lại một phần snippet 
                # để AI nắm bắt cấu trúc mẫu khi cần tra cứu/sửa code.
                result["raw_snippet"] = content[:500] # Lưu 500 ký tự đầu làm mẫu ngữ cảnh
                logger.info(f"Đã lập chỉ mục Asset/Markup file cho AI: {file_path}")

        except Exception as e:
            # Bắt lỗi an toàn tuyệt đối, không làm sập tiến trình khởi động hệ thống khi gặp file HTML/XML đặc biệt
            logger.warning(f"Bỏ qua phân tích cú pháp sâu cho file {file_path} (Lỗi: {e})")
            
        return result

    def scan_project(self):
        """Quét toàn bộ thư mục project để lập bản đồ tri thức toàn diện cho AI codebase"""
        codebase_map = []
        try:
            for root, dirs, files in os.walk(self.project_root):
                # Bỏ qua các thư mục hệ thống, cache, môi trường ảo
                if any(p in root for p in ['.git', '__pycache__', 'env', 'migrations', 'static']):
                    continue
                for file in files:
                    # Quét toàn bộ các định dạng file phục vụ cho AI lập trình & thiết kế
                    if file.endswith((".py", ".html", ".js", ".css", ".json", ".md")):
                        full_path = os.path.join(root, file)
                        codebase_map.append(self.scan_file(full_path))
                        
            logger.info("Hoàn tất quét toàn diện project codebase (Python + Assets) thành công cho AI.")
        except Exception as e:
            logger.error(f"Lỗi quét project codebase: {e}", exc_info=True)
            
        return codebase_map