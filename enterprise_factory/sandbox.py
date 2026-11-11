# File: enterprise_factory/sandbox.py
"""
Secure Python Sandbox Engine cho vnxBox Enterprise.
Thực thi mã Python trong môi trường cô lập, giới hạn thời gian (Timeout),
giới hạn bộ nhớ và chặn hoàn toàn các module độc hại (os, sys, subprocess, socket).
"""

import sys
import io
import contextlib
import signal
import resource
import restricted_python  # Hoặc cơ chế RestrictedPython tiêu chuẩn
from RestrictedPython import compile_restricted, safe_builtins

class SandboxExecutionError(Exception):
    """Lỗi phát sinh khi thực thi mã trong Sandbox"""
    pass


class PythonSandbox:
    """Bộ thực thi mã nguồn Python an toàn cấp độ AGI Local-First"""

    def __init__(self, timeout_seconds=3, max_memory_mb=128):
        self.timeout_seconds = timeout_seconds
        self.max_memory_mb = max_memory_mb * 1024 * 1024  # Chuyển sang Bytes

    def _set_security_limits(self):
        """Thiết lập giới hạn tài nguyên hệ thống trước khi chạy code (Linux/Unix limits)"""
        try:
            # Giới hạn bộ nhớ RAM ảo (AS)
            resource.setrlimit(resource.RLIMIT_AS, (self.max_memory_mb, self.max_memory_mb))
            # Chặn không cho tạo file quá lớn (FSIZE)
            resource.setrlimit(resource.RLIMIT_FSIZE, (1024 * 1024, 1024 * 1024))
        except (ValueError, AttributeError):
        # Bỏ qua nếu chạy trên môi trường không hỗ trợ (ví dụ Windows một số giới hạn RLIMIT)
            pass

    def execute(self, code_string: str, input_context: dict = None) -> dict:
        """
        Thực thi đoạn mã code truyền vào và trả về kết quả hoặc lỗi chi tiết.
        input_context: Dữ liệu đầu vào dạng từ điển (nếu có).
        """
        if input_context is None:
            input_context = {}

        # 1. Biên soạn code qua RestrictedPython để kiểm soát cú pháp nguy hiểm
        try:
            byte_code = compile_restricted(code_string, filename='<sandbox_code>', mode='exec')
        except Exception as e:
            return {
                "success": False,
                "error_type": "SyntaxOrRestrictedError",
                "message": str(e),
                "output": None
            }

        # 2. Thiết lập môi trường Builtins an toàn (chặn os, sys, import độc hại)
        safe_globals = {
            '__builtins__': safe_builtins,
            '_print': print,
            '_getattr__': getattr,
            'context': input_context
        }
        
        local_scope = {}

        # 3. Bắt luồng Standard Output để lấy kết quả print từ code sinh ra
        stdout_buffer = io.StringIO()

        def timeout_handler(signum, frame):
            raise TimeoutError("Mã nguồn thực thi quá thời gian cho phép (Timeout).")

        # Đăng ký cơ chế ngắt thời gian (Chỉ hỗ trợ trên luồng chính Unix)
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(self.timeout_seconds)

        try:
            self._set_security_limits()
            with contextlib.redirect_stdout(stdout_buffer):
                # Thực thi byte code trong không gian cô lập
                exec(byte_code, safe_globals, local_scope)
            
            # Tắt báo thức sau khi chạy xong an toàn
            signal.alarm(0)

            execution_output = stdout_buffer.getvalue()
            # Lấy giá trị biến 'result' từ scope nội bộ nếu có
            return_value = local_scope.get('result', execution_output.strip())

            return {
                "success": True,
                "error_type": None,
                "message": "Thực thi thành công qua Secure Sandbox.",
                "output": return_value
            }

        except TimeoutError as te:
            signal.alarm(0)
            return {
                "success": False,
                "error_type": "TimeoutError",
                "message": str(te),
                "output": None
            }
        except Exception as ex:
            signal.alarm(0)
            return {
                "success": False,
                "error_type": type(ex).__name__,
                "message": str(ex),
                "output": stdout_buffer.getvalue()
            }
        finally:
            # Khôi phục signal handler ban đầu
            signal.signal(signal.SIGALRM, old_handler)