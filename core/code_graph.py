"""
# File Path: core/code_graph.py
# File Purpose: Tự động quét cấu trúc mã nguồn dự án, phân tích file/class/hàm 
#               và xây dựng Code Graph bằng NetworkX phục vụ cơ chế JIT Context.
# Connected Files: [core/hardware_detector.py, PROJECT_MAP.md, PROJECT_MAP.json]
# Logs: Ghi log chi tiết quá trình quét file, thêm node, edge và lưu bản đồ đồ thị.
"""

import logging
import json
import os
import ast
from typing import Dict, List, Any
import networkx as nx

# Thiết lập hệ thống Logging tiêu chuẩn cho vnxBox
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] - %(message)s"
)
logger = logging.getLogger("vnxBox.CodeGraph")

class ProjectCodeGraph:
    """
    # Class: ProjectCodeGraph
    # Purpose: Quản lý và tự động quét đồ thị mã nguồn bằng NetworkX và AST (Abstract Syntax Tree).
    """
    def __init__(self, root_dir: str = ".", map_file_path: str = "PROJECT_MAP.json"):
        self.root_dir = root_dir
        self.map_file_path = map_file_path
        self.graph = nx.DiGraph()
        logger.info(f"[CODE_GRAPH] Khởi tạo ProjectCodeGraph quét thư mục: {root_dir}")

    def scan_project_directory(self) -> None:
        """
        # Function: scan_project_directory
        # Purpose: Tự động quét toàn bộ file Python trong dự án, trích xuất class/hàm và lập đồ thị.
        # Input: None
        # Output: None
        """
        logger.info("[CODE_GRAPH] Bắt đầu tự động quét cấu trúc tệp mã nguồn...")
        
        for dirpath, _, filenames in os.walk(self.root_dir):
            # Bỏ qua thư mục môi trường ảo và thư mục ẩn
            if "venv" in dirpath or ".git" in dirpath or "__pycache__" in dirpath:
                continue
                
            for filename in filenames:
                if filename.endswith(".py"):
                    file_path = os.path.join(dirpath, filename)
                    relative_path = os.path.relpath(file_path, self.root_dir)
                    self._parse_python_file(relative_path, file_path)

    def _parse_python_file(self, relative_path: str, absolute_path: str) -> None:
        """
        # Function: _parse_python_file
        # Purpose: Sử dụng AST (Abstract Syntax Tree) để đọc nội dung file Python mà không cần thực thi,
        #          tự động bóc tách các Class và Hàm bên trong để đưa vào Code Graph.
        # Input: relative_path (str), absolute_path (str)
        # Output: None
        """
        module_id = relative_path.replace(os.sep, ".")
        self.graph.add_node(module_id, type="module", file_path=relative_path)
        logger.info(f"[CODE_GRAPH] Phát hiện Module: {module_id} ({relative_path})")

        try:
            with open(absolute_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=absolute_path)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_id = f"{module_id}.{node.name}"
                    self.graph.add_node(class_id, type="class", name=node.name, file_path=relative_path)
                    self.graph.add_edge(module_id, class_id, relation="defines_class")
                    logger.info(f"   └── [CLASS] {node.name}")
                    
                elif isinstance(node, ast.FunctionDef):
                    # Chỉ lấy hàm cấp cao hoặc phương thức trong class cơ bản
                    func_id = f"{module_id}.{node.name}"
                    self.graph.add_node(func_id, type="function", name=node.name, file_path=relative_path)
                    self.graph.add_edge(module_id, func_id, relation="defines_function")
                    logger.info(f"   └── [FUNC] {node.name}()")
                    
        except Exception as e:
            logger.error(f"[CODE_GRAPH] Lỗi khi phân tích cú pháp file {relative_path}: {e}")

    def save_graph_to_disk(self) -> None:
        """
        # Function: save_graph_to_disk
        # Purpose: Lưu trạng thái đồ thị ra đĩa dưới định dạng JSON cấu trúc chuẩn.
        # Input: None
        # Output: None
        """
        data = nx.node_link_data(self.graph)
        with open(self.map_file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logger.info(f"[CODE_GRAPH] Đã cập nhật và lưu Code Graph tự động thành công vào {self.map_file_path}")


if __name__ == "__main__":
    logger.info("=== BẮT ĐẦU TỰ ĐỘNG QUÉT CẤU TRÚC CODE GRAPH ===")
    code_graph = ProjectCodeGraph(root_dir=".")
    code_graph.scan_project_directory()
    code_graph.save_graph_to_disk()
    logger.info("=== HOÀN TẤT TỰ ĐỘNG LẬP BẢN ĐỒ DỰ ÁN ===")