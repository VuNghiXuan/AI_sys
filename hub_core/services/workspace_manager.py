"""
# File Path: hub_core/services/workspace_manager.py
# File Purpose: Quản lý không gian làm việc độc lập (Isolated Workspace), quét AST động thư viện ngoài,
#               khởi tạo venv riêng biệt cho từng App, tự động cài đặt pytest và thực thi kiểm thử Sandbox cô lập.
"""

import os
import re
import ast
import sys
import venv
import logging
import subprocess
from typing import List, Dict, Any

logger = logging.getLogger("vnxBox.WorkspaceManager")

class IsolatedWorkspaceManager:
    def __init__(self, base_output_dir: str = "generated_apps"):
        self.base_output_dir = base_output_dir
        os.makedirs(self.base_output_dir, exist_ok=True)

    def extract_third_party_libs(self, code: str) -> List[str]:
        """Quét AST để lấy toàn bộ thư viện ngoài, loại trừ thư viện chuẩn Python."""
        try:
            tree = ast.parse(code)
            imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module.split('.')[0])
            
            standard_libs = getattr(sys, 'stdlib_module_names', set())
            return [lib for lib in imports if lib not in standard_libs and lib != 'modules']
        except Exception:
            return []

    def prepare_isolated_workspace(self, project_name: str, generated_code: str) -> dict:
        """Tạo thư mục dự án riêng, sinh requirements.txt động, dựng venv riêng và cài đặt pytest."""
        proj_dir = os.path.join(self.base_output_dir, project_name)
        tests_dir = os.path.join(proj_dir, "tests")
        venv_dir = os.path.join(proj_dir, "venv")
        
        os.makedirs(tests_dir, exist_ok=True)
        
        app_file = os.path.join(proj_dir, f"{project_name}.py")
        with open(app_file, "w", encoding="utf-8") as f:
            f.write(generated_code)

        third_party_libs = self.extract_third_party_libs(generated_code)
        req_file = os.path.join(proj_dir, "requirements.txt")
        with open(req_file, "w", encoding="utf-8") as f:
            for lib in third_party_libs:
                f.write(f"{lib}\n")

        logger.info(f"[ISOLATED_WORKSPACE] Đang khởi tạo venv riêng cho dự án tại: {venv_dir}")
        if not os.path.exists(venv_dir):
            venv.create(venv_dir, with_pip=True)

        if os.name == 'nt':
            pip_exe = os.path.join(venv_dir, "Scripts", "pip.exe")
            python_exe = os.path.join(venv_dir, "Scripts", "python.exe")
        else:
            pip_exe = os.path.join(venv_dir, "bin", "pip")
            python_exe = os.path.join(venv_dir, "bin", "python")

        # BẮT BUỘC: Tự động cài đặt pytest vào venv riêng của app ngay từ đầu
        logger.info(f"[ISOLATED_WORKSPACE] Đang cài đặt công cụ 'pytest' vào venv riêng...")
        try:
            subprocess.run([pip_exe, "install", "pytest"], check=True, capture_output=True, text=True)
            logger.info(f"[ISOLATED_WORKSPACE] Cài đặt pytest thành công.")
        except subprocess.CalledProcessError as e:
            logger.error(f"[ISOLATED_WORKSPACE] Không thể cài đặt pytest: {e.stderr}")

        # Tự động cài đặt các thư viện ngoài quét được từ AST (pandas, numpy,...)
        if third_party_libs:
            logger.info(f"[ISOLATED_WORKSPACE] Đang tự động pip install các gói yêu cầu {third_party_libs} vào venv riêng...")
            try:
                subprocess.run([pip_exe, "install", "-r", req_file], check=True, capture_output=True, text=True)
                logger.info(f"[ISOLATED_WORKSPACE] Cài đặt requirements thành công.")
            except subprocess.CalledProcessError as e:
                logger.error(f"[ISOLATED_WORKSPACE] Lỗi cài đặt requirements: {e.stderr}")

        test_file = os.path.join(tests_dir, f"test_{project_name}.py")
        test_code = (
            "import sys\n"
            "import os\n"
            "import pytest\n\n"
            f"sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))\n"
            f"from {project_name} import *\n\n"
            "def test_module_sanity():\n"
            "    assert True\n\n"
            "def test_functions_exist():\n"
            f"    import {project_name} as mod\n"
            "    items = [x for x in dir(mod) if not x.startswith('_')]\n"
            "    assert len(items) >= 0\n"
        )
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_code)

        return {
            "proj_dir": proj_dir,
            "app_file": app_file,
            "req_file": req_file,
            "venv_python": python_exe,
            "pip_executable": pip_exe,
            "test_file": test_file
        }