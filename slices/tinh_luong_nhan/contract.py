# ==============================================================================
# File Path: slices/tinh_luong_nhan/contract.py
# Description: Hợp đồng dữ liệu mở rộng (hỗ trợ cấu hình tham số & quy tắc) cho 'tinh_luong_nhan'.
# Linked Files: [slices/tinh_luong_nhan/core.py, slices/tinh_luong_nhan/ui_view.py, slices/tinh_luong_nhan/test_tinh_luong_nhan.py]
# Slice Tag: [SLICE: TINH_LUONG_NHAN_CONTRACT]
# ==============================================================================

from dataclasses import dataclass, field
from typing import Any

SOURCE_PROMPT = "@tao-app tính lương nhân viên"
LAST_EXPANSION_PROMPT = "@mo-rong mở rộng tính năng tính lương"


@dataclass
class SliceRequest:
    """Dữ liệu đầu vào chuẩn cho lát cắt tinh_luong_nhan."""

    payload: dict[str, Any] = field(default_factory=dict)
    rules: dict[str, Any] = field(default_factory=dict)
    options: dict[str, Any] = field(default_factory=dict)


@dataclass
class SliceResult:
    """Kết quả đầu ra chuẩn của lát cắt tinh_luong_nhan."""

    ok: bool
    slice_name: str
    summary: str
    data: dict[str, Any] = field(default_factory=dict)
