# ============================================================================
# File Path: code_map/scanner.py
# Module: Quet Tep Thuc Te, Phan Mo Rong Va Dem So Dong Tren Dia
# Linked Files: core_policy/loader.py,
#               code_map/sitter_index.py,
#               code_map/context_builder.py
# Purpose: Quet cac tep ma nguon/tai lieu thuc te trong du an, loai bo thu muc
#          bi bo qua, dem so dong thuc te va tim tep theo duoi hoac nguong dong.
# ============================================================================

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from core_policy.loader import FileLimitConfig, tai_cau_hinh_chien_thuat

logger = logging.getLogger(__name__)


@dataclass
class ThongTinTep:
    """Thong tin metadata co ban cua mot tep tren dia."""

    duong_dan_tuong_doi: str
    phan_mo_rong: str
    so_dong: int
    kich_thuoc_byte: int


def _bi_bo_qua(duong_dan: Path, goc: Path, ignore_dirs: set[str]) -> bool:
    """Kiem tra tep/thu muc co nam trong danh sach loai tru hay khong."""
    try:
        rel_parts = duong_dan.relative_to(goc).parts
    except ValueError:
        return True
    return any(part in ignore_dirs for part in rel_parts)


def dem_so_dong_tep(tep: Path) -> int:
    """Dem so dong thuc te cua mot tep van ban/ma nguon."""
    try:
        with tep.open(encoding="utf-8", errors="ignore") as f:
            return sum(1 for _ in f)
    except OSError:
        return 0


def quet_danh_sach_tep(
    goc_du_an: str | Path,
    duoi_file: str | list[str] | tuple[str, ...] | None = None,
    gioi_han_tep: int | None = None,
    file_limits: FileLimitConfig | None = None,
) -> list[ThongTinTep]:
    """Quet danh sach tep thuc te theo duoi file (neu chi dinh) va bo qua thu muc rac."""
    goc = Path(goc_du_an).resolve()
    if not goc.exists() or not goc.is_dir():
        return []

    limits = file_limits or tai_cau_hinh_chien_thuat().file_limits
    ignore_dirs = set(limits.ignore_dirs)
    max_items = gioi_han_tep if gioi_han_tep is not None else 500

    duoi_loc: set[str] | None = None
    if duoi_file:
        raw_list = [duoi_file] if isinstance(duoi_file, str) else list(duoi_file)
        duoi_loc = {
            ("." + item.lstrip(".").lower())
            for item in raw_list
            if item and item.strip()
        }

    ket_qua: list[ThongTinTep] = []
    for tep in sorted(goc.rglob("*")):
        if not tep.is_file() or _bi_bo_qua(tep, goc, ignore_dirs):
            continue
        ext = tep.suffix.lower()
        if duoi_loc is not None and ext not in duoi_loc:
            continue
        try:
            stat = tep.stat()
            size_byte = int(stat.st_size)
        except OSError:
            size_byte = 0
        rel = tep.relative_to(goc).as_posix()
        ket_qua.append(
            ThongTinTep(
                duong_dan_tuong_doi=rel,
                phan_mo_rong=ext,
                so_dong=dem_so_dong_tep(tep),
                kich_thuoc_byte=size_byte,
            )
        )
        if len(ket_qua) >= max_items:
            break

    logger.debug("Quet %d tep tu %s (loc_duoi=%s)", len(ket_qua), goc.name, sorted(duoi_loc or []))
    return ket_qua


def tim_tep_vuot_nguong_dong(
    goc_du_an: str | Path,
    nguong_dong: int = 300,
    duoi_file: str | list[str] | tuple[str, ...] | None = (".py",),
    file_limits: FileLimitConfig | None = None,
) -> list[ThongTinTep]:
    """Tra ve danh sach tep co so dong lon hon nguong chi dinh, sap xep giam dan."""
    ds_tep = quet_danh_sach_tep(
        goc_du_an=goc_du_an,
        duoi_file=duoi_file,
        gioi_han_tep=2000,
        file_limits=file_limits,
    )
    vuot = [t for t in ds_tep if t.so_dong > nguong_dong]
    vuot.sort(key=lambda item: (-item.so_dong, item.duong_dan_tuong_doi))
    return vuot