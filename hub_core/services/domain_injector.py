"""
# File Path: hub_core/services/domain_injector.py
# Purpose: Quản lý và cung cấp tri thức chuyên ngành (Domain Context) cho các AI Agent.
"""

import json
import os
import logging

logger = logging.getLogger("vnxBox.DomainInjector")

class DomainContextInjector:
    @staticmethod
    def get_domain_context(domain_key: str) -> str:
        """Đọc quy tắc nghiệp vụ chuyên ngành dựa vào key domain được truyền lên."""
        file_path = os.path.join("hub_core", "domains", f"{domain_key}.json")
        if not os.path.exists(file_path):
            return "[NGỮ CẢNH CHUNG]: Viết mã nguồn Python sạch, modular, dưới 300 dòng, tuân thủ tiêu chuẩn kỹ thuật."
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            rules_str = "\n".join([f"- {r}" for r in data.get("rules", [])])
            standards_str = "\n".join([f"- {s}" for s in data.get("code_standards", [])])
            
            return f"""
[NGỮ CẢNH NGHIỆP VỤ CHUYÊN SÂU: {data.get('domain_name', domain_key)}]
Các quy tắc nghiệp vụ bắt buộc tuân thủ:
{rules_str}

Tiêu chuẩn mã nguồn:
{standards_str}
"""
        except Exception as e:
            logger.error(f"[DOMAIN_INJECTOR] Lỗi đọc file domain {domain_key}: {e}")
            return "[NGỮ CẢNH CHUNG]: Viết mã nguồn Python sạch, modular."