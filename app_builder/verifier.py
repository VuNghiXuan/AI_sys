# ============================================================================
# File Path: app_builder/verifier.py
# Module: Bo Kiem Chung Cu Phap Va Doi Chieu Ket Qua Thuc Te
# Linked Files: code_map/scanner.py,
#               app_builder/executor.py
# Purpose: Kiem tra cu phap cac tep ma nguon (dac biet tep .py qua ast.parse),
#          kiem tra tep da ghi ton tai tren dia va phat hien dau hieu thieu/loi.
# ============================================================================

from __future__ import annotations

import ast
import logging
from dataclasses import dataclass, field
from pathlib import Path

from code_map.scanner import dem_so_dong_tep

logger = logging.getLogger(__name__)


@dataclass
class LoiTepKiemChung:
    """Chi tiet loi phat hien tren mot tep sau khi tao/sua."""

    duong_dan: str
    loai_loi: str
    chi_tiet: str


@dataclass
class BaoCaoKiemChung:
    """Tong ket trang thai kiem chung sau thuc thi."""

    dat_kiem_chung: bool
    so_tep_da_kiem_tra: int
    thong_ke_tep: dict[str, int] = field(default_factory=dict)
    cac_loi: list[LoiTepKiemChung] = field(default_factory=list)


def kiem_chung_tep_da_ghi(
    goc_du_an: str | Path,
    danh_sach_tep: list[str],
    tep_bi_bo_qua: list[str] | None = None,
) -> BaoCaoKiemChung:
    """Kiem tra su ton tai, so dong va cu phap cua cac tep da ghi tren dia."""
    goc = Path(goc_du_an).resolve()
    loi_ds: list[LoiTepKiemChung] = []
    thong_ke_dong: dict[str, int] = {}

    for bi_qua in tep_bi_bo_qua or []:
        loi_ds.append(
            LoiTepKiemChung(
                duong_dan=bi_qua,
                loai_loi="vuot_gioi_han_tep_xuat",
                chi_tiet="Tep bi bo qua do vuot max_output_files_per_turn.",
            )
        )

    for rel in danh_sach_tep:
        tep = (goc / rel).resolve()
        if not tep.exists() or not tep.is_file():
            loi_ds.append(
                LoiTepKiemChung(
                    duong_dan=rel,
                    loai_loi="thieu_tep",
                    chi_tiet="Tep khong ton tai sau khi ghi.",
                )
            )
            continue

        so_dong = dem_so_dong_tep(tep)
        thong_ke_dong[rel] = so_dong
        if so_dong == 0:
            loi_ds.append(
                LoiTepKiemChung(
                    duong_dan=rel,
                    loai_loi="tep_rong",
                    chi_tiet="Tep sau khi ghi khong co noi dung.",
                )
            )
            continue

        if tep.suffix.lower() == ".py":
            try:
                ma_py = tep.read_text(encoding="utf-8", errors="ignore")
                ast.parse(ma_py, filename=rel)
            except SyntaxError as exc:
                loi_ds.append(
                    LoiTepKiemChung(
                        duong_dan=rel,
                        loai_loi="loi_cu_phap_python",
                        chi_t=f"Dong {exc.lineno}: {exc.msg}",
                    )
                )

    dat = len(loi_ds) == 0
    logger.debug(
        "Kiem chung %d tep: dat=%s, so_loi=%d",
        len(danh_sach_tep),
        dat,
        len(loi_ds),
    )
    return BaoCaoKiemChung(
        dat_kiem_chung=dat,
        so_tep_da_kiem_tra=len(danh_sach_tep),
        thong_ke_tep=thong_ke_dong,
        cac_loi=loi_ds,
    )