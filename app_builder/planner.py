# ============================================================================
# File Path: app_builder/planner.py
# Module: Bo Lap Ke Hoach Tac Vu Theo Ngan Sach Va Gioi Han File Xuat
# Linked Files: core_policy/loader.py,
#               core_policy/budget.py,
#               code_map/context_builder.py
# Purpose: Chia yeu cau tao app/sua ma nguon thanh cac buoc nho gon,
#          ap dung gioi han so file dau ra moi luot va ngan sach token/luot.
# ============================================================================

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from core_policy.loader import FileLimitConfig, RoutingPolicy, tai_cau_hinh_chien_thuat

logger = logging.getLogger(__name__)


@dataclass
class BuocKeHoach:
    """Mot buoc thuc thi cu the trong ke hoach tao app/sua code."""

    ma_buoc: str
    tieu_de: str
    loai_buoc: str
    so_file_du_kien: int
    mo_ta: str


@dataclass
class KeHoachThucThi:
    """Tong hop ke hoach cho mot yeu cau."""

    yeu_cau: str
    profile: str
    max_output_files_per_turn: int
    max_llm_calls_per_turn: int
    cac_buoc: list[BuocKeHoach] = field(default_factory=list)


def lap_ke_hoach_tac_vu(
    yeu_cau: str,
    policy: RoutingPolicy | None = None,
    file_limits: FileLimitConfig | None = None,
) -> KeHoachThucThi:
    """Lap danh sach buoc thuc thi gon, khong vuot gioi han file xuat moi luot."""
    cfg = policy or tai_cau_hinh_chien_thuat()
    limits = file_limits or cfg.file_limits
    budget = cfg.lay_ngan_sach_hieu_luc()
    max_out_files = max(1, limits.max_output_files_per_turn)

    buoc_ds: list[BuocKeHoach] = [
        BuocKeHoach(
            ma_buoc="step_1_map_context",
            tieu_de="Thu thap ban do va doan code lien quan",
            loai_buoc="scan_context",
            so_file_du_kien=0,
            mo_ta="Quet metadata tep thuc te va trich doan code trong gioi han token.",
        ),
        BuocKeHoach(
            ma_buoc="step_2_generate",
            tieu_de="Sinh/cap nhat ma nguon theo gioi han tep",
            loai_buoc="llm_generate",
            so_file_du_kien=max_out_files,
            mo_ta=f"Chi tao/sua toi da {max_out_files} tep/luot, bam sat ngu canh thuc te.",
        ),
        BuocKeHoach(
            ma_buoc="step_3_verify",
            tieu_de="Kiem chung cu phap va doi chieu ket qua",
            loai_buoc="verify_output",
            so_file_du_kien=0,
            mo_ta="Kiem tra cu phap tep sinh ra va doi chieu trang thai thuc te.",
        ),
    ]

    # Nhan dien ro rang khi nguoi dung yeu cau tao app/giao dien/tinh nang moi
    yeu_cau_lower = (yeu_cau or "").lower()
    if any(tu in yeu_cau_lower for tu in ("tao app", "tạo app", "ung dung", "ứng dụng", "giao dien", "giao diện")):
        buoc_ds.insert(
            1,
            BuocKeHoach(
                ma_buoc="step_1b_outline",
                tieu_de="Chot khung module va luong du lieu toi thieu",
                loai_buoc="llm_outline",
                so_file_du_kien=0,
                mo_ta="Xac dinh ten tep, ham/model cot loi va rang buoc truoc khi ghi ma.",
            ),
        )

    # Cat bot buoc neu ngan sach so lan goi LLM trong mot luot qua hep
    if budget.max_llm_calls_per_turn <= 1:
        buoc_ds = [b for b in buoc_ds if b.loai_buoc != "llm_outline"]

    logger.debug(
        "Lap ke hoach profile=%s, so_buoc=%d, max_out_files=%d",
        cfg.active_profile,
        len(buoc_ds),
        max_out_files,
    )
    return KeHoachThucThi(
        yeu_cau=yeu_cau.strip(),
        profile=cfg.active_profile,
        max_output_files_per_turn=max_out_files,
        max_llm_calls_per_turn=budget.max_llm_calls_per_turn,
        cac_buoc=buoc_ds,
    )