# ============================================================================
# File Path: code_map/context_builder.py
# Module: Chon Loc Tep Lien Quan Co Gioi Han Va Gom Ngu Canh Nhe Cho AI
# Linked Files: core_policy/loader.py,
#               core_policy/budget.py,
#               code_map/scanner.py,
#               code_map/sitter_index.py
# Purpose: Loc tep dich va tep lien quan theo nguong file_limits va ngan sach
#          token, trich ban do rut gon va doan code lien quan thay vi ca tep.
# ============================================================================

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from core_policy.budget import uoc_luong_token
from core_policy.loader import FileLimitConfig, tai_cau_hinh_chien_thuat

from .sitter_index import BanGhiTepCode, lap_ban_do_repo

logger = logging.getLogger(__name__)


@dataclass
class GoiNguCanhCode:
    """Ngu canh da gom gon de dua cho LLM, kem thong ke token va danh sach tep."""

    ban_do_rut_gon: str
    trich_doan_code: str
    tep_dich: list[str] = field(default_factory=list)
    tep_lien_quan: list[str] = field(default_factory=list)
    uoc_luong_tokens: int = 0


def _tach_tu_khoa(cau_hoi: str) -> list[str]:
    """Tach cum tu khoa co nghia tu cau hoi de so khop tep/symbol."""
    sach = "".join(ch.lower() if (ch.isalnum() or ch in "_./-") else " " for ch in cau_hoi)
    return [tok for tok in sach.split() if len(tok) >= 2]


def _diem_khop_tep(ghi: BanGhiTepCode, tokens: list[str]) -> int:
    """Tinh diem khop giua ban ghi tep va cac token tu cau hoi."""
    if not tokens:
        return 0
    duong_dan_lower = ghi.duong_dan.lower()
    diem = 0
    for tok in tokens:
        if tok in duong_dan_lower:
            diem += 4
        for sym in ghi.ky_hieu:
            if tok in sym.ten.lower():
                diem += 3
    return diem


def _trich_doan_dong(tep_day_du: Path, dong_bat_dau: int, dong_ket_thuc: int, max_dong: int = 45) -> str:
    """Doc mot khoang dong gioi han kem so dong de giu ngu canh gon."""
    try:
        lines = tep_day_du.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return ""
    if not lines:
        return ""
    start_idx = max(0, dong_bat_dau - 1)
    end_idx = min(len(lines), max(start_idx + 1, dong_ket_thuc), start_idx + max_dong)
    return "\n".join(f"{idx + 1}: {lines[idx]}" for idx in range(start_idx, end_idx))


def xay_dung_ngu_canh_code(
    goc_du_an: str | Path,
    cau_hoi: str,
    file_limits: FileLimitConfig | None = None,
    ban_do_san_co: dict[str, BanGhiTepCode] | None = None,
) -> GoiNguCanhCode:
    """Xay dung ban do rut gon va trich doan code lien quan trong gioi han file/token."""
    goc = Path(goc_du_an).resolve()
    limits = file_limits or tai_cau_hinh_chien_thuat().file_limits
    ban_do = ban_do_san_co if ban_do_san_co is not None else lap_ban_do_repo(goc, file_limits=limits)

    tokens = _tach_tu_khoa(cau_hoi)
    xep_hang = sorted(
        ban_do.values(),
        key=lambda g: (-_diem_khop_tep(g, tokens), g.duong_dan),
    )

    tep_dich: list[str] = []
    for ghi in xep_hang:
        if _diem_khop_tep(ghi, tokens) > 0:
            tep_dich.append(ghi.duong_dan)
        if len(tep_dich) >= limits.max_input_files:
            break

    if not tep_dich and xep_hang:
        tep_dich = [g.duong_dan for g in xep_hang[: min(3, limits.max_input_files)]]

    # Mo rong toi da max_related_files tu cac tep co quan he import/imported_by
    tep_lien_quan: list[str] = []
    da_chon = set(tep_dich)
    for rel in tep_dich:
        ghi = ban_do.get(rel)
        if not ghi:
            continue
        ung_vien_lien_quan = list(ghi.imported_by) + [
            imp for imp in ghi.imports if imp in ban_do
        ]
        for ung_vien in ung_vien_lien_quan:
            if ung_vien in ban_do and ung_vien not in da_chon and ung_vien not in tep_lien_quan:
                tep_lien_quan.append(ung_vien)
                if len(tep_lien_quan) >= limits.max_related_files:
                    break
        if len(tep_lien_quan) >= limits.max_related_files:
            break

    # Dung ban do rut gon co kiem soat ngan sach max_map_tokens
    dong_map: list[str] = [f"# Repo Map ({goc.name}) - {len(ban_do)} indexed files"]
    for rel in tep_dich + tep_lien_quan:
        ghi = ban_do.get(rel)
        if not ghi:
            continue
        syms = [f"{s.ten}({s.dong_bat_dau}-{s.dong_ket_thuc})" for s in ghi.ky_hieu[:6]]
        sym_txt = f" | symbols: {', '.join(syms)}" if syms else ""
        dong_map.append(f"- {rel} [{ghi.so_dong} lines]{sym_txt}")

    ban_do_txt = "\n".join(dong_map)
    while uoc_luong_token(ban_do_txt) > limits.max_map_tokens and len(dong_map) > 2:
        dong_map.pop()
        ban_do_txt = "\n".join(dong_map)

    # Trich doan code ngan tu cac tep dich dau tien
    khoi_doan: list[str] = []
    for rel in tep_dich[: min(3, len(tep_dich))]:
        ghi = ban_do.get(rel)
        if not ghi:
            continue
        if ghi.ky_hieu:
            sym = ghi.ky_hieu[0]
            doan = _trich_doan_dong(goc / rel, sym.dong_bat_dau, sym.dong_ket_thuc)
        else:
            doan = _trich_doan_dong(goc / rel, 1, 35)
        if doan:
            khoi_doan.append(f"### {rel}\n```text\n{doan}\n```")

    trich_doan_txt = "\n\n".join(khoi_doan)
    tong_tok = uoc_luong_token(ban_do_txt) + uoc_luong_token(trich_doan_txt)
    logger.debug(
        "Goi ngu canh code: dich=%d, lien_quan=%d, uoc_luong_tokens=%d",
        len(tep_dich),
        len(tep_lien_quan),
        tong_tok,
    )
    return GoiNguCanhCode(
        ban_do_rut_gon=ban_do_txt,
        trich_doan_code=trich_doan_txt,
        tep_dich=tep_dich,
        tep_lien_quan=tep_lien_quan,
        uoc_luong_tokens=tong_tok,
    )