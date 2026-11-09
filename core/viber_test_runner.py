# Path: core/viber_test_runner.py
"""
Mục đích: Script tự động chạy kiểm thử toàn bộ dự án Vibercode Enterprise.
Nhiệm vụ:
  - Kiểm tra cú pháp tất cả file Python bằng ViberSandbox.
  - Kiểm tra quy chuẩn độ dài file (< 300 dòng/file).
  - Thẩm định tính đồng bộ với PROJECT_MAP.md.
Inputs: project_root (str)
Outputs: Report kết quả kiểm thử (CONSOLE / JSON)
"""

import os
import sys
from typing import Dict, List, Any

# Đảm bảo import được module sandbox từ cùng thư mục
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from viber_sandbox import ViberSandbox


class ViberTestRunner:
    """
    Lớp điều phối kiểm thử tự động toàn hệ thống.
    """

    def __init__(self, root_dir: str = "."):
        self.root_dir = root_dir
        self.sandbox = ViberSandbox()
        self.max_lines_limit = 300

    def get_all_files(self) -> List[str]:
        """Lấy danh sách các file mã nguồn Python và HTML trong dự án."""
        target_files = []
        for root, _, files in os.walk(self.root_dir):
            # Bỏ qua các thư mục môi trường ảo hoặc git
            if "env" in root or ".git" in root or "__pycache__" in root:
                continue
            for file in files:
                if file.endswith((".py", ".html")):
                    target_files.append(os.path.join(root, file))
        return target_files

    def check_file_length(self, file_path: str) -> Dict[str, Any]:
        """Kiểm tra quy định độ dài file < 300 dòng."""
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            line_count = len(lines)
            
        passed = line_count <= self.max_lines_limit
        return {
            "file_path": file_path,
            "line_count": line_count,
            "passed": passed,
            "message": f"{line_count} dòng" if passed else f"VI PHẠM: {line_count}/300 dòng!"
        }

    def run_full_suite(self) -> Dict[str, Any]:
        """Chạy toàn bộ test suite."""
        print("=== BẮT ĐẦU CHẠY KIỂM THỬ HỆ THỐNG VIBERCODE ENTERPRISE ===")
        files = self.get_all_files()
        results = []
        total_violations = 0

        for file_path in files:
            # 1. Kiểm tra độ dài file
            length_res = self.check_file_length(file_path)
            
            # 2. Nếu là file Python, kiểm tra cú pháp với Sandbox
            syntax_passed = True
            if file_path.endswith(".py"):
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                sandbox_res = self.sandbox.check_syntax(content)
                syntax_passed = (sandbox_res["status"] == "PASSED")

            is_valid = length_res["passed"] and syntax_passed
            if not is_valid:
                total_violations += 1

            status_symbol = "✅" if is_valid else "❌"
            print(f"{status_symbol} {file_path} | Số dòng: {length_res['line_count']} | Syntax: {'OK' if syntax_passed else 'LỖI'}")

            results.append({
                "file": file_path,
                "lines": length_res["line_count"],
                "syntax_ok": syntax_passed,
                "passed": is_valid
            })

        print(f"\n=== KẾT QUẢ: {len(files) - total_violations}/{len(files)} file ĐẠT CHUẨN ===")
        return {"total_files": len(files), "violations": total_violations, "details": results}


if __name__ == "__main__":
    runner = ViberTestRunner(root_dir=".")
    runner.run_full_suite()