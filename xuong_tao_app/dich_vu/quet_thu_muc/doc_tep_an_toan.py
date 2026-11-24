# ============================================================================
# File Path: xuong_tao_app/dich_vu/quet_thu_muc/doc_tep_an_toan.py
# Module: Doc Tep Nguon An Toan
# Linked Files: quet_thu_muc_nguon.py
# Purpose: Kiem tra tep va doc noi dung van ban/du lieu co gioi han dung
#          luong de tranh qua tai bo nho tren may CPU-only.
# ============================================================================

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DUOI_TEP_HO_TRO = {
    ".txt",
    ".md",
    ".markdown",
    ".csv",
    ".json",
    ".py",
    ".html",
    ".htm",
    ".css",
    ".js",
    ".sql",
    ".yaml",
    ".yml",
    ".xml",
    ".log",
}

THU_MUC_BO_QUA = {
    "__pycache__",
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "migrations",
}

GIOI_HAN_BYTE_MOI_TEP = 200_000  # ~200KB moi tep de giu nhip xu ly nhanh
GIOI_HAN_KY_TU_MOI_TEP = 25_000


def la_thu_muc_bi_bo_qua(ten_thu_muc: str) -> bool:
    """Kiem tra ten thu muc co nam trong danh sach loai tru hay khong."""
    return (ten_thu_muc or "").strip() in THU_MUC_BO_QUA


def la_tep_duoc_ho_tro(duong_dan: Path) -> bool:
    """Kiem tra tep ton tai, la file thuong va thuoc nhom duoi van ban/du lieu."""
    if not duong_dan.exists() or not duong_dan.is_file():
        return False
    return duong_dan.suffix.lower() in DUOI_TEP_HO_TRO


def _chuan_hoa_noi_dung_json(raw_text: str) -> str:
    """Thu dinh dang gon JSON neu hop le, fallback ve van ban goc neu loi."""
    try:
        parsed = json.loads(raw_text)
        return json.dumps(parsed, ensure_ascii=False, indent=2)
    except Exception:
        return raw_text


def doc_noi_dung_tep(
    duong_dan_tep: Path,
    thu_muc_goc: Path,
    gioi_han_byte: int = GIOI_HAN_BYTE_MOI_TEP,
    gioi_han_ky_tu: int = GIOI_HAN_KY_TU_MOI_TEP,
) -> dict[str, Any]:
    """Doc an toan noi dung mot tep va tra ve thong tin kem trang thai."""
    try:
        kich_thuoc_byte = duong_dan_tep.stat().st_size
    except OSError as exc:
        logger.error("Loi lay kich thuoc tep '%s': %s", duong_dan_tep, exc, exc_info=True)
        return {
            "duong_dan": str(duong_dan_tep),
            "duong_dan_tuong_doi": str(duong_dan_tep),
            "ten_tep": duong_dan_tep.name,
            "trang_thai": "loi",
            "ly_do": f"Khong doc duoc thong tin tep: {exc}",
            "noi_dung": "",
        }

    try:
        duong_dan_tuong_doi = str(duong_dan_tep.relative_to(thu_muc_goc))
    except ValueError:
        duong_dan_tuong_doi = str(duong_dan_tep)

    if kich_thuoc_byte > gioi_han_byte:
        logger.warning(
            "Bo qua noi dung day do tep '%s' vuot gioi han (%d > %d bytes)",
            duong_dan_tuong_doi,
            kich_thuoc_byte,
            gioi_han_byte,
        )
        return {
            "duong_dan": str(duong_dan_tep),
            "duong_dan_tuong_doi": duong_dan_tuong_doi,
            "ten_tep": duong_dan_tep.name,
            "kich_thuoc_byte": kich_thuoc_byte,
            "trang_thai": "bo_qua_dung_luong",
            "ly_do": f"Kich thuoc {kich_thuoc_byte} bytes vuot nguong {gioi_han_byte} bytes",
            "noi_dung": "",
        }

    try:
        with duong_dan_tep.open("r", encoding="utf-8", errors="replace") as f:
            noi_dung = f.read(gioi_han_ky_tu + 1)
    except OSError as exc:
        logger.error("Loi khi doc tep '%s': %s", duong_dan_tuong_doi, exc, exc_info=True)
        return {
            "duong_dan": str(duong_dan_tep),
            "duong_dan_tuong_doi": duong_dan_tuong_doi,
            "ten_tep": duong_dan_tep.name,
            "kich_thuoc_byte": kich_thuoc_byte,
            "trang_thai": "loi",
            "ly_do": str(exc),
            "noi_dung": "",
        }

    bi_cat_bot = len(noi_dung) > gioi_han_ky_tu
    if bi_cat_bot:
        noi_dung = noi_dung[:gioi_han_ky_tu]

    if duong_dan_tep.suffix.lower() == ".json":
        noi_dung = _chuan_hoa_noi_dung_json(noi_dung)[:gioi_han_ky_tu]

    logger.debug(
        "Da doc tep '%s' (%d ky tu, cat_bot=%s)",
        duong_dan_tuong_doi,
        len(noi_dung),
        bi_cat_bot,
    )
    return {
        "duong_dan": str(duong_dan_tep),
        "duong_dan_tuong_doi": duong_dan_tuong_doi,
        "ten_tep": duong_dan_tep.name,
        "duoi_tep": duong_dan_tep.suffix.lower(),
        "kich_thuoc_byte": kich_thuoc_byte,
        "so_ky_tu": len(noi_dung),
        "bi_cat_bot": bi_cat_bot,
        "trang_thai": "da_doc",
        "noi_dung": noi_dung,
    }