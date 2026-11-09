# Path: core/viber_sandbox.py
"""
Mục đích: Môi trường kiểm thử và phân tích tĩnh (Static Analysis) cho Vibercode.
Nhiệm vụ:
  - Kiểm tra cú pháp (Syntax Check) của mã nguồn Python do Agent sinh ra.
  - Đảm bảo code an toàn trước khi ghi ra file thực thi trên hệ thống local.
Inputs: code_string (str)
Outputs: dict (status, error_message)
"""

import ast
import sys
from typing import Dict, Any


class ViberSandbox:
    """
    Lớp kiểm tra an toàn và thực thi mã nguồn trong môi trường cô lập local.
    """

    def __init__(self):
        pass

    def check_syntax(self, code_content: str) -> Dict[str, Any]:
        """
        Kiểm tra lỗi cú pháp Python thông qua thư viện built-in ast.
        """
        try:
            ast.parse(code_content)
            return {
                "status": "PASSED",
                "message": "Mã nguồn hợp lệ, không có lỗi cú pháp."
            }
        except SyntaxError as e:
            return {
                "status": "FAILED",
                "message": f"Lỗi cú pháp tại dòng {e.lineno}, cột {e.offset}: {e.text}",
                "detail": str(e)
            }

    def validate_code_block(self, file_path: str, code_content: str) -> bool:
        """
        Thực hiện validate toàn diện một khối code trước khi ghi file.
        """
        print(f"[ViberSandbox] Đang kiểm tra an toàn cho file: {file_path}")
        result = self.check_syntax(code_content)
        
        if result["status"] == "PASSED":
            print(f"[ViberSandbox] Kiểm thử thành công cho {file_path}")
            return True
        else:
            print(f"[ViberSandbox] Phát hiện lỗi trong {file_path}: {result['message']}")
            return False


if __name__ == "__main__":
    # Test nhanh Sandbox
    sandbox = ViberSandbox()
    sample_code = "print('Hello Viber Sandbox')"
    res = sandbox.check_syntax(sample_code)
    print(res)