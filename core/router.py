# ==============================================================================
# File Path: core/router.py
# Description: Bộ định tuyến 2 lớp (Mode + Domain/Sub-domain) có hỗ trợ @tao-app và @mo-rong.
# Linked Files: [config/domains.json, core/logger_setup.py, slices/doc_reconcile/ui_view.py, hub_core/views.py]
# Slice Tag: [CORE: TWO_LAYER_ROUTER]
# ==============================================================================

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class RouteDecision:
    """Kết quả định tuyến 2 lớp cho một yêu cầu đầu vào."""

    raw_prompt: str
    mode: str = "conversational"
    domain: str = "general"
    sub_domain: str = "utility_app"
    matched_keywords: list[str] = field(default_factory=list)
    default_tolerance: str = "0"


class TwoLayerRouter:
    """Phân loại Lớp 1 (Mode) và Lớp 2 (Domain/Sub-domain) từ file cấu hình + quy tắc @tag."""

    TAG_MODE_MAP: dict[str, tuple[str, str, str]] = {
        "@tao-app": ("code_module", "slice_scaffold", "new_slice"),
        "@scaffold": ("code_module", "slice_scaffold", "new_slice"),
        "@mo-rong": ("code_module", "slice_expand", "expand_slice"),
        "@mở-rộng": ("code_module", "slice_expand", "expand_slice"),
        "@tu-sua": ("code_module", "repair_loop", "pytest_circuit_breaker"),
        "@tự-sửa": ("code_module", "repair_loop", "pytest_circuit_breaker"),
        "@repair": ("code_module", "repair_loop", "pytest_circuit_breaker"),
    }

    def __init__(self, domains_config_path: str = "config/domains.json") -> None:
        self.config_path = Path(domains_config_path)
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """Đọc cấu hình domains/modes từ JSON, có fallback an toàn nếu thiếu file."""
        if not self.config_path.exists():
            logger.warning("[Router] Không tìm thấy %s, dùng cấu hình mặc định tạm thời.", self.config_path)
            return {
                "default_domain": "general",
                "default_sub_domain": "utility_app",
                "modes": {
                    "code_module": {
                        "keywords": ["@tao-app", "@mo-rong", "@tu-sua", "tạo app", "mở rộng", "giao diện", "đối soát", "code", "sửa lỗi"]
                    },
                    "chit_chat": {"keywords": ["chào", "ngủ ngon", "tán gẫu"]},
                },
                "domains": {},
            }
        try:
            with self.config_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info("[Router] Đã nạp cấu hình định tuyến từ %s", self.config_path)
            return data
        except Exception as exc:
            logger.exception("[Router] Lỗi đọc %s: %s — dùng fallback mặc định.", self.config_path, exc)
            return {"default_domain": "general", "default_sub_domain": "utility_app", "modes": {}, "domains": {}}

    def _detect_tag_override(self, text_lower: str) -> tuple[str | None, str | None, str | None, list[str]]:
        """Kiểm tra prefix/tag đặc biệt (@tao-app, @mo-rong, @tu-sua) để ưu tiên đúng luồng."""
        hits = [tag for tag in self.TAG_MODE_MAP if re.search(rf"(?<!\w){re.escape(tag)}(?!\w)", text_lower)]
        if not hits:
            return None, None, None, []
        primary = hits[0]
        mode, domain, sub_domain = self.TAG_MODE_MAP[primary]
        logger.info("[Router] Khớp tag đặc biệt %s -> mode=%s, domain=%s, sub=%s", hits, mode, domain, sub_domain)
        return mode, domain, sub_domain, hits

    def _detect_mode(self, text_lower: str) -> tuple[str, list[str]]:
        """Lớp 1: Xác định Mode (code_module / chit_chat / conversational)."""
        modes_cfg = self.config.get("modes", {})
        best_mode = "conversational"
        best_hits: list[str] = []

        for mode_name in ("code_module", "chit_chat", "conversational"):
            keywords = modes_cfg.get(mode_name, {}).get("keywords", [])
            hits = [kw for kw in keywords if kw.lower() in text_lower]
            if len(hits) > len(best_hits):
                best_mode = mode_name
                best_hits = hits

        if not best_hits and any(k in text_lower for k in ("tạo", "viết", "sửa", "làm", "xuất", "lọc", "mở rộng")):
            best_mode = "code_module"

        return best_mode, best_hits

    def _infer_business_sub_domain(self, text_lower: str, fallback_sub: str) -> str:
        """Suy luận sub-domain nghiệp vụ gọn khi chưa khớp keyword cụ thể trong config."""
        if any(k in text_lower for k in ("lương", "payroll", "chấm công", "nhân sự", "hr")):
            return "payroll_hr"
        if any(k in text_lower for k in ("đối soát", "hóa đơn", "reconcile", "invoice", "kế toán")):
            return "doc_reconcile"
        return fallback_sub

    def _detect_domain_and_sub_domain(self, text_lower: str) -> tuple[str, str, list[str], str]:
        """Lớp 2: Xác định Domain, Sub-domain và ngưỡng sai số mặc định từ config."""
        default_domain = self.config.get("default_domain", "general")
        default_sub = self.config.get("default_sub_domain", "utility_app")
        domains_cfg = self.config.get("domains", {})

        best_domain = default_domain
        best_sub = default_sub
        best_hits: list[str] = []
        best_tol = "0"

        for dom_key, dom_info in domains_cfg.items():
            sub_map = dom_info.get("sub_domains", {})
            for sub_key, sub_info in sub_map.items():
                kws = sub_info.get("keywords", [])
                hits = [kw for kw in kws if kw.lower() in text_lower]
                if len(hits) > len(best_hits):
                    best_domain = dom_key
                    best_sub = sub_key
                    best_hits = hits
                    best_tol = str(sub_info.get("default_tolerance", "0"))

        if not best_hits:
            best_sub = self._infer_business_sub_domain(text_lower, best_sub)

        return best_domain, best_sub, best_hits, best_tol

    def route(self, prompt: str) -> RouteDecision:
        """Thực thi định tuyến 2 lớp cho prompt đầu vào."""
        cleaned = (prompt or "").strip()
        text_lower = cleaned.lower()
        logger.info("[Router] Bắt đầu định tuyến prompt (độ dài=%d ký tự): '%s'", len(cleaned), cleaned[:120])

        tag_mode, tag_domain, tag_sub, tag_hits = self._detect_tag_override(text_lower)
        cfg_mode, mode_hits = self._detect_mode(text_lower)
        cfg_domain, cfg_sub, dom_hits, default_tol = self._detect_domain_and_sub_domain(text_lower)

        final_mode = tag_mode or cfg_mode
        final_domain = tag_domain or cfg_domain
        final_sub = cfg_sub if dom_hits else (tag_sub or cfg_sub)
        all_hits = list(dict.fromkeys(tag_hits + mode_hits + dom_hits))

        decision = RouteDecision(
            raw_prompt=cleaned,
            mode=final_mode,
            domain=final_domain,
            sub_domain=final_sub,
            matched_keywords=all_hits,
            default_tolerance=default_tol,
        )
        logger.info(
            "[Router] Kết quả định tuyến: mode=%s | domain=%s | sub_domain=%s | hits=%s",
            decision.mode,
            decision.domain,
            decision.sub_domain,
            decision.matched_keywords,
        )
        return decision