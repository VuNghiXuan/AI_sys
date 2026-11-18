"""
# File Path: hub_core/services/sandbox_executor.py
# Purpose: Thực thi tệp pytest tự động trong môi trường cách ly và trả về kết quả chi tiết.
"""

import subprocess
import logging

logger = logging.getLogger("vnxBox.SandboxExecutor")

class SandboxExecutor:
    @staticmethod
    def run_pytest_on_module(test_file_path: str) -> dict:
        """
        Chạy pytest trên tệp kiểm thử chỉ định và trả về trạng thái cùng output chi tiết.
        """
        logger.info(f"[SANDBOX] Đang chạy kiểm thử Pytest trên tệp: {test_file_path}")
        try:
            result = subprocess.run(
                ["pytest", test_file_path, "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            output_log = result.stdout + "\n" + result.stderr
            if result.returncode == 0:
                logger.info(f"[SANDBOX] Pytest PASSED cho tệp {test_file_path}")
                return {"success": True, "output": output_log}
            else:
                logger.warning(f"[SANDBOX] Pytest FAILED cho tệp {test_file_path} (Exit code: {result.returncode})")
                return {"success": False, "output": output_log}
                
        except subprocess.TimeoutExpired:
            logger.error(f"[SANDBOX] Pytest bị quá thời gian (Timeout) trên tệp {test_file_path}")
            return {"success": False, "output": "Lỗi Timeout: Đoạn mã chạy quá thời gian giới hạn (15s) hoặc bị kẹt vòng lặp vô hạn."}
        except Exception as e:
            logger.error(f"[SANDBOX] Lỗi hệ thống khi chạy subprocess pytest: {e}")
            return {"success": False, "output": str(e)}