# ==============================================================================
# File Path: slices/tinh_luong_nhan/core.py
# Description: Logic xử lý cốt lõi đã mở rộng cho lát cắt 'tinh_luong_nhan' (<300 dòng).
# Linked Files: [slices/tinh_luong_nhan/contract.py, slices/tinh_luong_nhan/ui_view.py, slices/tinh_luong_nhan/test_tinh_luong_nhan.py]
# Slice Tag: [SLICE: TINH_LUONG_NHAN_CORE]
# ==============================================================================

import logging
from typing import Any

from slices.tinh_luong_nhan.contract import LAST_EXPANSION_PROMPT, SOURCE_PROMPT, SliceRequest, SliceResult

logger = logging.getLogger(__name__)


def _extract_records(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Chuẩn hóa danh sách bản ghi từ payload (hỗ trợ cả 'records'/'items' hoặc dict đơn)."""
    for key in ("records", "items", "entries"):
        raw_list = payload.get(key)
        if isinstance(raw_list, list):
            return [item if isinstance(item, dict) else {"value": item} for item in raw_list]
    return [dict(payload)] if payload else []


def _apply_numeric_rules(record: dict[str, Any], rules: dict[str, Any]) -> dict[str, Any]:
    """Áp dụng các hệ số/quy tắc cấu hình truyền vào lên từng bản ghi (không hardcode công thức)."""
    enriched = dict(record)
    multipliers = rules.get("multipliers") or {}
    additions = rules.get("additions") or {}

    for field_name, factor in multipliers.items():
        if field_name in enriched and isinstance(enriched[field_name], (int, float)):
            try:
                enriched[f"{field_name}_adjusted"] = round(float(enriched[field_name]) * float(factor), 4)
            except (TypeError, ValueError):
                logger.warning("[%s] Bỏ qua multiplier không hợp lệ cho '%s'", "tinh_luong_nhan", field_name)

    for field_name, bonus in additions.items():
        if field_name in enriched and isinstance(enriched[field_name], (int, float)):
            try:
                enriched[f"{field_name}_plus_rule"] = round(float(enriched[field_name]) + float(bonus), 4)
            except (TypeError, ValueError):
                logger.warning("[%s] Bỏ qua addition không hợp lệ cho '%s'", "tinh_luong_nhan", field_name)

    return enriched


def execute_slice(req: SliceRequest) -> SliceResult:
    """Thực thi luồng xử lý mở rộng của lát cắt tinh_luong_nhan và ghi log chi tiết."""
    logger.info("[%s] Bắt đầu execute_slice (expanded) | keys=%s", "tinh_luong_nhan", list(req.payload.keys()))
    try:
        raw_records = _extract_records(req.payload)
        processed_records = [_apply_numeric_rules(rec, req.rules) for rec in raw_records]
        result_data: dict[str, Any] = {
            "source_prompt": SOURCE_PROMPT,
            "last_expansion_prompt": LAST_EXPANSION_PROMPT,
            "record_count": len(processed_records),
            "records": processed_records,
            "rules_applied": list((req.rules or {}).keys()),
            "options_used": req.options,
        }
        logger.info("[%s] Hoàn tất execute_slice | records=%d", "tinh_luong_nhan", len(processed_records))
        return SliceResult(
            ok=True,
            slice_name="tinh_luong_nhan",
            summary=f"Lát cắt 'tinh_luong_nhan' đã xử lý mở rộng {len(processed_records)} bản ghi thành công.",
            data=result_data,
        )
    except Exception as exc:
        logger.exception("[%s] Lỗi trong execute_slice: %s", "tinh_luong_nhan", exc)
        return SliceResult(
            ok=False,
            slice_name="tinh_luong_nhan",
            summary=f"Lỗi xử lý mở rộng ở lát cắt 'tinh_luong_nhan': {exc}",
            data={},
        )
