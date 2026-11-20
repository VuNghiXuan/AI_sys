# ==============================================================================
# File Path: slices/doc_reconcile/core.py
# Description: Logic đối soát dữ liệu bảng kê/chứng từ theo khóa và ngưỡng sai số.
# Linked Files: [slices/doc_reconcile/contract.py, slices/doc_reconcile/ui_view.py, slices/doc_reconcile/test_doc_reconcile.py]
# Slice Tag: [SLICE: DOC_RECONCILE_CORE]
# ==============================================================================

import logging
from decimal import Decimal, InvalidOperation
from typing import Any

from slices.doc_reconcile.contract import (
    ReconcileConfig,
    ReconcileItemResult,
    ReconcileReport,
    ReconcileRule,
)

logger = logging.getLogger(__name__)


def _make_row_key(row: dict[str, Any], key_fields: list[str], fallback_idx: int) -> str:
    """Ghép khóa định danh dòng từ danh sách cột cấu hình."""
    parts = [str(row.get(f, "")).strip() for f in key_fields]
    joined = "|".join(p for p in parts if p != "")
    return joined if joined else f"__row_{fallback_idx}"


def _to_decimal(val: Any) -> Decimal | None:
    """Chuyển giá trị sang Decimal an toàn, trả về None nếu không phải số hợp lệ."""
    if val is None or isinstance(val, bool):
        return None
    if isinstance(val, Decimal):
        return val
    if isinstance(val, (int, float)):
        return Decimal(str(val))
    text = str(val).strip().replace(",", "")
    if not text:
        return None
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def _compare_field(
    src_val: Any,
    tgt_val: Any,
    rule: ReconcileRule,
) -> tuple[str, dict[str, Any]]:
    """So sánh 1 cặp trường theo rule; trả về ('ok' | 'tol' | 'diff', chi_tiết)."""
    if rule.compare_type == "text":
        s_str = "" if src_val is None else str(src_val).strip()
        t_str = "" if tgt_val is None else str(tgt_val).strip()
        if not rule.case_sensitive:
            s_str = s_str.lower()
            t_str = t_str.lower()
        if s_str == t_str:
            return "ok", {"source": src_val, "target": tgt_val, "delta": None}
        return "diff", {"source": src_val, "target": tgt_val, "delta": None}

    src_num = _to_decimal(src_val)
    tgt_num = _to_decimal(tgt_val)
    if src_num is None or tgt_num is None:
        equal_raw = str(src_val).strip() == str(tgt_val).strip()
        return ("ok" if equal_raw else "diff"), {
            "source": src_val,
            "target": tgt_val,
            "delta": None,
        }

    delta = abs(src_num - tgt_num)
    if delta == Decimal("0"):
        return "ok", {"source": str(src_num), "target": str(tgt_num), "delta": "0"}
    if delta <= rule.tolerance:
        return "tol", {
            "source": str(src_num),
            "target": str(tgt_num),
            "delta": str(delta),
            "tolerance": str(rule.tolerance),
        }
    return "diff", {
        "source": str(src_num),
        "target": str(tgt_num),
        "delta": str(delta),
        "tolerance": str(rule.tolerance),
    }


def reconcile_records(
    source_rows: list[dict[str, Any]],
    target_rows: list[dict[str, Any]],
    config: ReconcileConfig,
) -> ReconcileReport:
    """Thực hiện đối soát danh sách dòng nguồn và dòng đích theo cấu hình."""
    logger.info(
        "Bắt đầu đối soát: source=%d dòng, target=%d dòng, keys=%s, rules=%d",
        len(source_rows),
        len(target_rows),
        config.key_fields,
        len(config.rules),
    )

    target_map: dict[str, dict[str, Any]] = {}
    for idx, row in enumerate(target_rows):
        key = _make_row_key(row, config.key_fields, idx)
        target_map[key] = row

    seen_target_keys: set[str] = set()
    items: list[ReconcileItemResult] = []
    matched_cnt = 0
    tol_cnt = 0
    mismatch_cnt = 0
    missing_cnt = 0
    extra_cnt = 0

    for idx, src_row in enumerate(source_rows):
        key = _make_row_key(src_row, config.key_fields, idx)
        tgt_row = target_map.get(key)

        if tgt_row is None:
            missing_cnt += 1
            items.append(
                ReconcileItemResult(
                    key_value=key,
                    status="MISSING_TARGET",
                    message="Không tìm thấy dòng tương ứng ở dữ liệu đích.",
                )
            )
            continue

        seen_target_keys.add(key)
        diffs: dict[str, dict[str, Any]] = {}
        has_diff = False
        has_tol = False

        for rule in config.rules:
            s_val = src_row.get(rule.source_field)
            t_val = tgt_row.get(rule.target_field)
            outcome, detail = _compare_field(s_val, t_val, rule)
            if outcome == "diff":
                has_diff = True
                diffs[rule.source_field] = detail
            elif outcome == "tol":
                has_tol = True
                diffs[rule.source_field] = detail

        if has_diff:
            mismatch_cnt += 1
            status = "MISMATCH"
            msg = f"Lệch vượt ngưỡng ở các cột: {', '.join(diffs.keys())}"
        elif has_tol:
            tol_cnt += 1
            status = "WITHIN_TOLERANCE"
            msg = f"Chênh lệch trong ngưỡng cho phép ở: {', '.join(diffs.keys())}"
        else:
            matched_cnt += 1
            status = "MATCHED"
            msg = "Khớp hoàn toàn."

        items.append(
            ReconcileItemResult(
                key_value=key,
                status=status,
                diffs=diffs,
                message=msg,
            )
        )

    for idx, tgt_row in enumerate(target_rows):
        key = _make_row_key(tgt_row, config.key_fields, idx)
        if key not in seen_target_keys:
            extra_cnt += 1
            items.append(
                ReconcileItemResult(
                    key_value=key,
                    status="EXTRA_TARGET",
                    message="Dòng chỉ có ở dữ liệu đích, không có ở dữ liệu nguồn.",
                )
            )

    report = ReconcileReport(
        total_source=len(source_rows),
        total_target=len(target_rows),
        matched_count=matched_cnt,
        within_tolerance_count=tol_cnt,
        mismatch_count=mismatch_cnt,
        missing_target_count=missing_cnt,
        extra_target_count=extra_cnt,
        items=items,
    )
    logger.info(
        "Hoàn tất đối soát: matched=%d, within_tol=%d, mismatch=%d, missing=%d, extra=%d",
        matched_cnt,
        tol_cnt,
        mismatch_cnt,
        missing_cnt,
        extra_cnt,
    )
    return report