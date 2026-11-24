# ============================================================================
# File Path: dieu_phoi_y_dinh/dich_vu/bo_nho_va_cache.py
# Module: Bo Nho Lich Su Hoi Thoai Va Cache Dieu Phoi
# Linked Files: dieu_phoi_y_dinh/dich_vu/dieu_phoi_nhanh.py,
#               dieu_phoi_y_dinh/dich_vu/thuc_thi_nhanh/trinh_xu_ly_chung.py,
#               dieu_phoi_y_dinh/dich_vu/hoc_tang_cuong_qa.py
# Purpose: Quan ly lich su hoi thoai (kem y_dinh tung luot), ten nguoi dung
#          theo phien va cache TTL.
# ============================================================================

from collections import OrderedDict
from dataclasses import dataclass, field
import logging
import re
import time
from typing import Any

logger = logging.getLogger(__name__)

MAX_PHIEN_LUU = 100
MAX_LUOT_MOI_PHIEN = 16
MAX_MUC_CACHE = 300
TTL_CACHE_MAC_DINH_GIAY = 120.0
TTL_CACHE_DB_TELEMETRY_GIAY = 15.0

TU_LOAI_TRU_TEN = {
    "alo", "ok", "okay", "ừ", "uh", "ừm", "vâng", "dạ", "không", "chào", "hi", "hello",
    "gì", "gi", "nào", "nao", "sao", "đâu", "dau",
}

CUM_HOI_TEN_AI: tuple[str, ...] = (
    "cho mình biết tên",
    "cho tôi biết tên",
    "cho em biết tên",
    "tên bạn là gì",
    "tên của bạn",
    "nhắc tên",
    "chưa thấy tên",
)

MAU_HOI_TEN_USER = re.compile(r"\b(?:tên|teen|ten|nhắc\s+tên|nhac\s+ten)\b", flags=re.IGNORECASE)


@dataclass
class TrangThaiPhien:
    """Trang thai hoi thoai ngan gon cho mot phien."""

    luot_hoi_thoai: list[dict[str, str]] = field(default_factory=list)
    ten_nguoi_dung: str = ""


_LICH_SU_THEO_PHIEN: OrderedDict[str, TrangThaiPhien] = OrderedDict()
_BO_DEM_CACHE: OrderedDict[str, tuple[float, dict[str, Any]]] = OrderedDict()


def chuan_hoa_khoa_prompt(prompt: str) -> str:
    """Chuan hoa chuoi prompt de tao khoa cache on dinh."""
    return re.sub(r"\s+", " ", (prompt or "").strip().lower())


def _lay_hoac_tao_phien(ma_phien: str) -> TrangThaiPhien:
    """Lay hoac khoi tao TrangThaiPhien an toan."""
    khoa = (ma_phien or "mac_dinh").strip() or "mac_dinh"
    phien = _LICH_SU_THEO_PHIEN.get(khoa)
    if phien is None:
        phien = TrangThaiPhien()
        _LICH_SU_THEO_PHIEN[khoa] = phien
    _LICH_SU_THEO_PHIEN.move_to_end(khoa)
    while len(_LICH_SU_THEO_PHIEN) > MAX_PHIEN_LUU:
        phien_cu, _ = _LICH_SU_THEO_PHIEN.popitem(last=False)
        logger.info("Don phien cu vuot gioi han: %s", phien_cu)
    return phien


def trich_xuat_ten_tu_cau(van_ban: str, co_hoi_ten_truoc: bool = False) -> str:
    """Trich xuat ten nguoi dung tu cau gioi thieu hoac cau tra loi ngan sau hoi ten."""
    chuoi = (van_ban or "").strip()
    if not chuoi:
        return ""

    for mau in (
        r"^(?:(?:ờ|ừ|ủa|à|ơi|hi|chào)\s+)?(?:tên\s+)?(?:tôi|tao|mình|minh|em|anh)\s+"
        r"(?:là|la)\s+([A-Za-zÀ-ỹ0-9_.-]+(?:\s+[A-Za-zÀ-ỹ0-9_.-]+){0,2})\s*[.!?]*$",
        r"^tên\s+bạn\s+là\s+([A-Za-zÀ-ỹ0-9_.-]+(?:\s+[A-Za-zÀ-ỹ0-9_.-]+){0,2})\s*[.!?]*$",
    ):
        khop = re.match(mau, chuoi, flags=re.IGNORECASE)
        if khop:
            ten = khop.group(1).strip(" .,!?:;")
            if ten.lower() not in TU_LOAI_TRU_TEN:
                return ten

    if co_hoi_ten_truoc:
        ten_gon = chuoi.strip(" .,!?:;")
        if re.fullmatch(r"[A-Za-zÀ-ỹ]+(?:\s+[A-Za-zÀ-ỹ]+){0,2}", ten_gon):
            if ten_gon.lower() not in TU_LOAI_TRU_TEN:
                return ten_gon

    return ""


def lay_lich_su_phien(ma_phien: str = "mac_dinh", gioi_han: int = MAX_LUOT_MOI_PHIEN) -> list[dict[str, str]]:
    """Lay danh sach luot hoi thoai gan nhat cua mot phien."""
    phien = _lay_hoac_tao_phien(ma_phien)
    return [dict(m) for m in phien.luot_hoi_thoai[-max(1, gioi_han) :]]


def lay_ten_nguoi_dung_phien(ma_phien: str = "mac_dinh") -> str:
    """Lay ten nguoi dung da luu trong phien hien tai."""
    return _lay_hoac_tao_phien(ma_phien).ten_nguoi_dung


def ghi_luot_hoi_thoai(
    ma_phien: str,
    cau_hoi_user: str,
    cau_tra_loi_ai: str,
    y_dinh: str = "",
) -> None:
    """Ghi them mot cap hoi thoai (kem y_dinh) va cap nhat ten nguoi dung neu co."""
    phien = _lay_hoac_tao_phien(ma_phien)
    luot_ai_cu = (
        phien.luot_hoi_thoai[-1]["content"].lower()
        if phien.luot_hoi_thoai and phien.luot_hoi_thoai[-1].get("role") == "assistant"
        else ""
    )
    luot_user_cu = (
        phien.luot_hoi_thoai[-2]["content"]
        if len(phien.luot_hoi_thoai) >= 2 and phien.luot_hoi_thoai[-2].get("role") == "user"
        else ""
    )
    co_hoi_ten = any(cum in luot_ai_cu for cum in CUM_HOI_TEN_AI) or bool(MAU_HOI_TEN_USER.search(luot_user_cu))

    if cau_hoi_user:
        user_sach = cau_hoi_user.strip()
        phien.luot_hoi_thoai.append({
            "role": "user",
            "content": user_sach,
            "prompt": user_sach,
            "y_dinh": (y_dinh or "").strip(),
        })
        ten_moi = trich_xuat_ten_tu_cau(user_sach, co_hoi_ten_truoc=co_hoi_ten)
        if ten_moi:
            phien.ten_nguoi_dung = ten_moi
            logger.info("Cap nhat ten_nguoi_dung='%s' cho phien=%s", ten_moi, ma_phien)

    if cau_tra_loi_ai:
        phien.luot_hoi_thoai.append({
            "role": "assistant",
            "content": cau_tra_loi_ai.strip(),
            "y_dinh": (y_dinh or "").strip(),
        })

    phien.luot_hoi_thoai = phien.luot_hoi_thoai[-MAX_LUOT_MOI_PHIEN:]


def _don_cache_het_han(thoi_diem_hien_tai: float) -> None:
    """Xoa cac muc cache da het TTL."""
    for k in [k for k, (moc, _) in _BO_DEM_CACHE.items() if moc <= thoi_diem_hien_tai]:
        _BO_DEM_CACHE.pop(k, None)


def lay_tu_cache(khoa_cache: str) -> dict[str, Any] | None:
    """Lay du lieu tu cache neu con hieu luc TTL."""
    hien_tai = time.monotonic()
    _don_cache_het_han(hien_tai)
    muc = _BO_DEM_CACHE.get(khoa_cache)
    if not muc or muc[0] <= hien_tai:
        _BO_DEM_CACHE.pop(khoa_cache, None)
        return None
    _BO_DEM_CACHE.move_to_end(khoa_cache)
    logger.info("Trung cache (HIT) cho khoa=%s", khoa_cache)
    return dict(muc[1])


def luu_vao_cache(khoa_cache: str, gia_tri: dict[str, Any], ttl_giay: float = TTL_CACHE_MAC_DINH_GIAY) -> None:
    """Luu ket qua vao bo nho dem cache voi thoi gian song TTL."""
    hien_tai = time.monotonic()
    _don_cache_het_han(hien_tai)
    _BO_DEM_CACHE[khoa_cache] = (hien_tai + max(1.0, ttl_giay), dict(gia_tri))
    _BO_DEM_CACHE.move_to_end(khoa_cache)
    while len(_BO_DEM_CACHE) > MAX_MUC_CACHE:
        _BO_DEM_CACHE.popitem(last=False)