"""
# File Path: hub_core/services/domain_injector.py
# File Purpose: Quản lý và cung cấp tri thức chuyên ngành (Domain Context, Sub-Domain & Code Skeleton)
#               theo cơ chế JIT Context cho các AI Agent trong vnxBox.
# Connected Files: [hub_core/services/pipeline_service.py, hub_core/domains/gold_silver.json, hub_core/domains/accounting_reconciliation.json]
# Logs: Ghi log cảnh báo/lỗi khi đọc file domain, chọn sub_domain hoặc rút gọn ngữ cảnh.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger("vnxBox.DomainInjector")

DEFAULT_FALLBACK_CONTEXT = (
    "[NGỮ CẢNH CHUNG]: Viết mã nguồn Python sạch, chia hàm rõ ràng, "
    "mỗi file dưới 300 dòng, có docstring giải thích đầu vào/đầu ra."
)


class DomainContextInjector:
    """Cung cấp ngữ cảnh nghiệp vụ, mảng nghiệp vụ con (sub_domain) và khung code mẫu."""

    @staticmethod
    def _load_domain_data(domain_key: str) -> Optional[Dict[str, Any]]:
        """Đọc và parse file cấu hình JSON của domain nếu tồn tại."""
        safe_key = os.path.basename(domain_key.strip())
        file_path = os.path.join("hub_core", "domains", f"{safe_key}.json")

        if not os.path.exists(file_path):
            logger.warning(f"[DOMAIN_INJECTOR] Không tìm thấy file domain: {file_path}")
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                logger.warning(f"[DOMAIN_INJECTOR] Dữ liệu JSON không phải object ở {file_path}")
                return None
            return data
        except json.JSONDecodeError as e:
            logger.error(f"[DOMAIN_INJECTOR] Lỗi định dạng JSON ở {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"[DOMAIN_INJECTOR] Lỗi đọc file domain {domain_key}: {e}")
            return None

    @staticmethod
    def _extract_sub_domain_section(
        data: Dict[str, Any],
        sub_domain: Optional[str],
    ) -> tuple[str, Optional[str]]:
        """Trích xuất quy tắc riêng của sub_domain và tên skeleton tham chiếu (nếu có)."""
        if not sub_domain:
            return "", None

        sub_domains = data.get("sub_domains")
        if not isinstance(sub_domains, dict):
            logger.warning("[DOMAIN_INJECTOR] Domain không có cấu trúc sub_domains hợp lệ.")
            return "", None

        sub_info = sub_domains.get(sub_domain)
        if not isinstance(sub_info, dict):
            logger.warning(f"[DOMAIN_INJECTOR] Không tìm thấy sub_domain '{sub_domain}' trong domain.")
            return "", None

        title = sub_info.get("title", sub_domain)
        sub_rules = sub_info.get("rules", [])
        skeleton_ref = sub_info.get("skeleton_ref")

        lines: List[str] = [f"Mảng nghiệp vụ trọng tâm ({title}):"]
        if isinstance(sub_rules, list) and sub_rules:
            lines.extend(f"- {r}" for r in sub_rules)

        logger.info(f"[DOMAIN_INJECTOR] Đã kích hoạt sub_domain: [{sub_domain}] (skeleton_ref={skeleton_ref}).")
        return "\n".join(lines), skeleton_ref if isinstance(skeleton_ref, str) else None

    @staticmethod
    def _format_skeletons(skeletons: Any, preferred_ref: Optional[str] = None) -> str:
        """Định dạng khung code mẫu, ưu tiên skeleton khớp `preferred_ref` nếu có."""
        if not skeletons:
            return ""

        blocks: List[str] = []
        if isinstance(skeletons, dict):
            ordered_keys = list(skeletons.keys())
            if preferred_ref and preferred_ref in skeletons:
                ordered_keys = [preferred_ref] + [k for k in ordered_keys if k != preferred_ref]

            for name in ordered_keys:
                code_snippet = skeletons[name]
                blocks.append(f"# --- Skeleton: {name} ---\n{code_snippet}")
        elif isinstance(skeletons, list):
            for idx, item in enumerate(skeletons, start=1):
                if isinstance(item, dict):
                    title = item.get("name", f"Skeleton_{idx}")
                    code_snippet = item.get("code", "")
                    blocks.append(f"# --- Skeleton: {title} ---\n{code_snippet}")
                else:
                    blocks.append(str(item))

        return "\n\n".join(blocks)

    @classmethod
    def get_domain_context(
        cls,
        domain_key: str,
        sub_domain: Optional[str] = None,
        include_skeletons: bool = True,
        max_chars: int = 3500,
    ) -> str:
        """
        Trả về ngữ cảnh nghiệp vụ cho Agent theo domain và sub_domain (tùy chọn).
        Tự rút gọn nếu vượt `max_chars` để giữ prompt gọn cho local LLM.
        """
        data = cls._load_domain_data(domain_key)
        if not data:
            return DEFAULT_FALLBACK_CONTEXT

        domain_title = data.get("domain_name", domain_key)
        sections: List[str] = [f"[NGỮ CẢNH NGHIỆP VỤ: {domain_title}]"]

        rules = data.get("rules", [])
        if isinstance(rules, list) and rules:
            rules_str = "\n".join(f"- {r}" for r in rules)
            sections.append(f"Quy tắc nghiệp vụ chung:\n{rules_str}")

        sub_section_text, skeleton_ref = cls._extract_sub_domain_section(data, sub_domain)
        if sub_section_text:
            sections.append(sub_section_text)

        standards = data.get("code_standards", [])
        if isinstance(standards, list) and standards:
            standards_str = "\n".join(f"- {s}" for s in standards)
            sections.append(f"Tiêu chuẩn mã nguồn:\n{standards_str}")

        if include_skeletons:
            skeleton_str = cls._format_skeletons(data.get("code_skeletons"), preferred_ref=skeleton_ref)
            if skeleton_str:
                sections.append(
                    "Khung hàm / công thức mẫu tham chiếu (ưu tiên kế thừa đúng cấu trúc & công thức):\n"
                    f"```python\n{skeleton_str}\n```"
                )

        context_text = "\n\n".join(sections)
        if len(context_text) > max_chars:
            logger.info(
                f"[DOMAIN_INJECTOR] Cắt gọn context domain '{domain_key}' "
                f"từ {len(context_text)} xuống {max_chars} ký tự."
            )
            context_text = context_text[:max_chars].rstrip() + "\n... [Đã rút gọn ngữ cảnh]"

        return context_text