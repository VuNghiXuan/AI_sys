# ==============================================================================
# File Path: slices/doc_reconcile/contract.py
# Description: Hợp đồng dữ liệu và cấu hình quy tắc đối soát chứng từ/bảng kê.
# Linked Files: [slices/doc_reconcile/core.py, slices/doc_reconcile/ui_view.py, slices/doc_reconcile/test_doc_reconcile.py]
# Slice Tag: [SLICE: DOC_RECONCILE_CONTRACT]
# ==============================================================================

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any


@dataclass
class ReconcileRule:
    """Quy tắc đối soát một cặp cột giữa nguồn (source) và đích (target)."""

    source_field: str
    target_field: str
    tolerance: Decimal = Decimal("0")
    compare_type: str = "numeric"  # "numeric" | "text"
    case_sensitive: bool = False


@dataclass
class ReconcileConfig:
    """Cấu hình chung cho một phiên đối soát chứng từ/bảng kê."""

    key_fields: list[str] = field(default_factory=lambda: ["ref_code"])
    rules: list[ReconcileRule] = field(default_factory=list)
    default_numeric_tolerance: Decimal = Decimal("0")


@dataclass
class ReconcileItemResult:
    """Kết quả đối soát của một bản ghi/dòng dữ liệu."""

    key_value: str
    status: str  # "MATCHED" | "WITHIN_TOLERANCE" | "MISMATCH" | "MISSING_TARGET" | "EXTRA_TARGET"
    diffs: dict[str, dict[str, Any]] = field(default_factory=dict)
    message: str = ""


@dataclass
class ReconcileReport:
    """Báo cáo tổng hợp toàn bộ phiên đối soát."""

    total_source: int
    total_target: int
    matched_count: int
    within_tolerance_count: int
    mismatch_count: int
    missing_target_count: int
    extra_target_count: int
    items: list[ReconcileItemResult] = field(default_factory=list)


def build_config_from_dict(raw_cfg: dict[str, Any] | None = None) -> ReconcileConfig:
    """Chuyển dictionary cấu hình thành ReconcileConfig có kiểm tra kiểu an toàn."""
    cfg = raw_cfg or {}
    key_fields = list(cfg.get("key_fields") or ["ref_code"])
    default_tol = Decimal(str(cfg.get("default_numeric_tolerance", "0")))
    raw_rules = cfg.get("rules") or []

    rules: list[ReconcileRule] = []
    for item in raw_rules:
        compare_type = str(item.get("compare_type", "numeric")).lower()
        tol_raw = item.get("tolerance", default_tol)
        rules.append(
            ReconcileRule(
                source_field=str(item["source_field"]),
                target_field=str(item["target_field"]),
                tolerance=Decimal(str(tol_raw)),
                compare_type=compare_type,
                case_sensitive=bool(item.get("case_sensitive", False)),
            )
        )

    return ReconcileConfig(
        key_fields=key_fields,
        rules=rules,
        default_numeric_tolerance=default_tol,
    )