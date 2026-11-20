# ==============================================================================
# File Path: slices/tinh_luong_nhan/test_tinh_luong_nhan.py
# Description: Unit test cho lát cắt 'tinh_luong_nhan' sau khi mở rộng.
# Linked Files: [slices/tinh_luong_nhan/contract.py, slices/tinh_luong_nhan/core.py, slices/tinh_luong_nhan/ui_view.py]
# Slice Tag: [SLICE: TINH_LUONG_NHAN_TEST]
# ==============================================================================

from slices.tinh_luong_nhan.contract import SliceRequest
from slices.tinh_luong_nhan.core import execute_slice


def test_tinh_luong_nhan_expanded_records_and_rules():
    """Kiểm tra lát cắt tinh_luong_nhan xử lý danh sách bản ghi và quy tắc cấu hình."""
    req = SliceRequest(
        payload={"records": [{"name": "NV_01", "base_amount": 100}]},
        rules={"multipliers": {"base_amount": 1.2}, "additions": {"base_amount": 10}},
        options={"mode": "expanded_check"},
    )
    res = execute_slice(req)
    assert res.ok is True
    assert res.data["record_count"] == 1
    assert res.data["records"][0]["base_amount_adjusted"] == 120.0
    assert res.data["records"][0]["base_amount_plus_rule"] == 110.0
