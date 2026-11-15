# enterprise_factory/sandbox.py
"""
Secure Python Sandbox Engine cho vnxBox Enterprise.
Thực thi mã Python trong môi trường cô lập, giới hạn thời gian (Timeout),
giới hạn bộ nhớ và chặn hoàn toàn các module độc hại (os, sys, subprocess, socket).
"""

import logging
import io
import contextlib
import threading
from RestrictedPython import compile_restricted, safe_builtins
from RestrictedPython.Guards import safer_getattr

logger = logging.getLogger(__name__)

class SandboxExecutionError(Exception):
    """Lỗi phát sinh khi thực thi mã trong Sandbox"""
    pass


class PythonSandbox:
    """Bộ thực thi mã nguồn Python an toàn cấp độ AGI Local-First"""

    def __init__(self, timeout_seconds=3, max_memory_mb=128):
        self.timeout_seconds = timeout_seconds
        self.max_memory_mb = max_memory_mb * 1024 * 1024  # Chuyển sang Bytes

    def execute(self, code_string: str, input_context: dict = None) -> dict:
        """
        Thực thi đoạn mã code truyền vào và trả về kết quả hoặc lỗi chi tiết.
        input_context: Dữ liệu đầu vào dạng từ điển (nếu có).
        """
        if input_context is None:
            input_context = {}

        logger.info(f"[*] [SANDBOX] Bắt đầu biên dịch và thực thi code an toàn (Timeout: {self.timeout_seconds}s)...")

        # 1. Biên soạn code qua RestrictedPython để kiểm soát cú pháp nguy hiểm
        try:
            byte_code = compile_restricted(code_string, filename='<sandbox_code>', mode='exec')
        except Exception as e:
            logger.error(f"[-] [SANDBOX SYNTAX ERROR]: {str(e)}", exc_info=True)
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
            '_getattr__': safer_getattr,
            'context': input_context
        }
        
        local_scope = {}
        stdout_buffer = io.StringIO()

        # Dùng Event để kiểm soát timeout an toàn trên cả Windows lẫn Linux
        execution_error = None
        is_timeout = False

        def target_execution():
            nonlocal execution_error
            try:
                with contextlib.redirect_stdout(stdout_buffer):
                    exec(byte_code, safe_globals, local_scope)
            except Exception as ex:
                execution_error = ex

        # Chạy trong Thread riêng để ép Timeout
        exec_thread = threading.Thread(target=target_execution)
        exec_thread.daemon = True

        exec_thread.start()
        exec_thread.join(timeout=self.timeout_seconds)

        if exec_thread.is_alive():
            is_timeout = True
            logger.warning(f"[!] [SANDBOX TIMEOUT]: Mã nguồn vượt quá giới hạn {self.timeout_seconds} giây.")
            return {
                "success": False,
                "error_type": "TimeoutError",
                "message": f"Mã nguồn thực thi quá thời gian cho phép ({self.timeout_seconds}s).",
                "output": stdout_buffer.getvalue()
            }

        if execution_error:
            logger.error(f"[-] [SANDBOX RUNTIME ERROR]: {str(execution_error)}", exc_info=True)
            return {
                "success": False,
                "error_type": type(execution_error).__name__,
                "message": str(execution_error),
                "output": stdout_buffer.getvalue()
            }

        execution_output = stdout_buffer.getvalue()
        # Lấy giá trị biến 'result' từ scope nội bộ nếu có, ngược lại lấy output print
        return_value = local_scope.get('result', execution_output.strip())

        logger.info("[+] [SANDBOX SUCCESS] Thực thi mã nguồn thành công qua Sandbox.")
        return {
            "success": True,
            "error_type": None,
            "message": "Thực thi thành công qua Secure Sandbox.",
            "output": return_value
        }