# ============================================================================
# File Path: dieu_phoi_y_dinh/dich_vu/dieu_phoi_nhanh.py
# Module: Dieu Phoi Don Va Da Y Dinh Cho dieu_phoi_y_dinh
# Linked Files: dieu_phoi_y_dinh/dich_vu/tach_va_loc_y_dinh.py,
#               dieu_phoi_y_dinh/dich_vu/dinh_tuyen/khoi_tao_y_dinh.py,
#               dieu_phoi_y_dinh/dich_vu/thuc_thi_nhanh/trinh_xu_ly_chung.py,
#               dieu_phoi_y_dinh/dich_vu/bo_nho_va_cache.py,
#               dieu_phoi_y_dinh/dich_vu/hoc_tang_cuong_qa.py
# Purpose: Dieu phoi prompt don/da y dinh, gan ngu canh luot truoc, ket hop
#          cache va hoc tang cuong Q&A (< 300 dong).
# ============================================================================

import logging
from pathlib import Path
import re
from typing import Any

from .bo_nho_va_cache import (
    TTL_CACHE_DB_TELEMETRY_GIAY,
    TTL_CACHE_MAC_DINH_GIAY,
    chuan_hoa_khoa_prompt,
    ghi_luot_hoi_thoai,
    lay_lich_su_phien,
    lay_ten_nguoi_dung_phien,
    lay_tu_cache,
    luu_vao_cache,
)
from .dinh_tuyen.khoi_tao_y_dinh import registry
from .hoc_tang_cuong_qa import ghi_nhan_tuong_tac_qa, la_tin_hieu_dinh_chinh
from .tach_va_loc_y_dinh import (
    MA_Y_DINH_MAC_DINH,
    chuan_hoa_truoc_dinh_tuyen,
    phan_tich_cac_y_dinh,
)

logger = logging.getLogger(__name__)

NHOM_LON_MAC_DINH = "hoi_thoai"
NHAN_Y_DINH_MAC_DINH = "Trò chuyện tự do"
CHE_DO_KHONG_CACHE = {"db_truy_van", "tra_mang", "tao_app"}
MAX_LUOT_NGU_CANH_NHANH = 6
MAU_HOI_TEN_NGUOI_DUNG = re.compile(
    r"^\s*(?:cho\s+hỏi\s+)?(?:tôi|tao|mình|minh|em|anh)?\s*(?:tên|teen|ten)\s*(?:gì|gi|là\s+gì|la\s+gi)\s*[?.!]*\s*$",
    flags=re.IGNORECASE,
)


def _lay_goc_du_an() -> Path:
    """Tim thu muc goc chua manage.py."""
    hien_tai = Path(__file__).resolve()
    for cha in [hien_tai.parent, *hien_tai.parents]:
        if (cha / "manage.py").exists():
            return cha
    goc_du_phong = hien_tai.parents[3]
    logger.warning("Khong thay manage.py, dung thu muc du phong: %s", goc_du_phong)
    return goc_du_phong


def _xac_dinh_ma_phien(session: Any = None, request: Any = None) -> str:
    """Lay ma phien hoi thoai an toan tu session hoac request."""
    if session is not None:
        key = getattr(session, "session_key", None)
        if key:
            return str(key)
        if isinstance(session, dict) and session.get("ma_phien"):
            return str(session["ma_phien"])
    if request is not None:
        req_session = getattr(request, "session", None)
        key = getattr(req_session, "session_key", None)
        if key:
            return str(key)
    return "mac_dinh"


def _trich_luot_truoc_hop_le(lich_su: list[dict[str, Any]] | None) -> dict[str, Any] | None:
    """Lay luot user truoc co thong tin prompt/y_dinh de phuc vu thuong/phat Q&A."""
    for muc in reversed(lich_su or []):
        if not isinstance(muc, dict):
            continue
        prompt_cu = str(muc.get("prompt") or muc.get("cau_hoi") or muc.get("user") or "").strip()
        yd_cu = str(muc.get("y_dinh") or muc.get("intent") or "").strip()
        if prompt_cu or yd_cu:
            return {**muc, "prompt": prompt_cu, "y_dinh": yd_cu}
    return None


def _xu_ly_nhanh_cau_hoi_ten(prompt: str, ten_nguoi_dung: str) -> str | None:
    """Tra loi tuc thi (00:00s) neu prompt la cau hoi ten nguoi dung."""
    if not MAU_HOI_TEN_NGUOI_DUNG.match(prompt or ""):
        return None
    if ten_nguoi_dung:
        return f"Tên của anh/bạn trong phiên này là **{ten_nguoi_dung}**."
    return "Trong đoạn chat này chưa có tên được lưu. Anh/bạn cho biết tên để mình nhớ nhé."


def _co_the_dung_cache(
    ma_yd: str,
    che_do_xu_ly: str,
    bo_qua_cache: bool,
    ten_nguoi_dung: str = "",
) -> bool:
    """Kiem tra y dinh/che do co duoc phep doc/ghi cache hay khong."""
    if bo_qua_cache or ten_nguoi_dung:
        return False
    if (che_do_xu_ly or "").strip() in CHE_DO_KHONG_CACHE:
        return False
    return bool(ma_yd)


def _lay_ttl_theo_che_do(che_do_xu_ly: str) -> float:
    """Xac dinh thoi gian song TTL phu hop cho tung che do xu ly."""
    if (che_do_xu_ly or "").strip() == "db_truy_van":
        return TTL_CACHE_DB_TELEMETRY_GIAY
    return TTL_CACHE_MAC_DINH_GIAY


def _lay_meta_y_dinh(ma_yd: str, yd_goc: Any = None) -> tuple[str, str, str]:
    """Lay (nhom_lon, nhan_y_dinh, che_do_xu_ly) an toan cho ma_yd."""
    yd_chot = registry.lay_y_dinh(ma_yd) if hasattr(registry, "lay_y_dinh") else yd_goc
    nhom_lon = getattr(yd_chot, "nhom_lon", None) or getattr(yd_goc, "nhom_lon", None) or NHOM_LON_MAC_DINH
    nhan_yd = getattr(yd_chot, "mo_ta_ngu_nghia", None) or getattr(yd_goc, "mo_ta_ngu_nghia", None) or NHAN_Y_DINH_MAC_DINH
    che_do = getattr(yd_chot, "che_do_xu_ly", None) or getattr(yd_goc, "che_do_xu_ly", "")
    return str(nhom_lon), str(nhan_yd), str(che_do)


def _xay_dung_ket_qua_dieu_phoi(
    ma_yd: str,
    nhan_yd: str,
    nhom_lon: str,
    kq_thuc_thi: dict[str, Any],
    trung_cache: bool = False,
    danh_sach_y_dinh: list[str] | None = None,
) -> dict[str, Any]:
    """Chuan hoa dictionary ket qua tra ve sau khi thuc thi y dinh."""
    return {
        "ok": True,
        "y_dinh": ma_yd,
        "danh_sach_y_dinh": danh_sach_y_dinh or [ma_yd],
        "nhan_y_dinh": nhan_yd,
        "nhom_lon": nhom_lon,
        "chuyen_huong_tao_app": bool(kq_thuc_thi.get("chuyen_huong_tao_app")),
        "tom_tat": str(kq_thuc_thi.get("noi_dung") or ""),
        "trung_cache": trung_cache,
    }


def _thuc_thi_mot_nhanh(
    doan_cau: str,
    ma_con: str,
    goc_du_an: Path,
    chi_muc: dict[str, Any],
) -> tuple[str, bool]:
    """Thuc thi mot nhanh y dinh an toan, tra ve (noi_dung_str, chuyen_huong)."""
    try:
        kq_con = registry.thuc_thi(doan_cau, goc_du_an, chi_muc, ma_y_dinh_chi_dinh=ma_con) or {}
        noi_dung = str(kq_con.get("noi_dung") or "").strip()
        if not noi_dung:
            noi_dung = f"Chưa có nội dung phản hồi cho ý định `{ma_con}`."
        return noi_dung, bool(kq_con.get("chuyen_huong_tao_app"))
    except Exception as loi:
        logger.error("Loi thuc thi nhanh y_dinh=%s: %s", ma_con, loi, exc_info=True)
        return f"⚠️ Lỗi khi xử lý ý định `{ma_con}`: {loi}", False


def xu_ly_prompt_da_y_dinh(
    prompt: str,
    chon_phuong_an: str = "",
    bo_qua_cache: bool = False,
    session: Any = None,
    request: Any = None,
) -> dict[str, Any]:
    """Dieu phoi prompt don hoac da y dinh, lien ket luot truoc, cache va hoc Q&A."""
    del chon_phuong_an
    prompt_sach = (prompt or "").strip()
    if not prompt_sach:
        logger.warning("Nhan prompt rong trong xu_ly_prompt_da_y_dinh.")
        return {"ok": False, "error": "Prompt trống"}

    ma_phien = _xac_dinh_ma_phien(session=session, request=request)
    lich_su = lay_lich_su_phien(ma_phien)
    luot_truoc = _trich_luot_truoc_hop_le(lich_su)
    ten_nguoi_dung = lay_ten_nguoi_dung_phien(ma_phien)

    try:
        cac_y_dinh = phan_tich_cac_y_dinh(prompt_sach, lich_su=lich_su)
        ds_ma_yd = [ma for _, ma in cac_y_dinh]
        ma_yd = ds_ma_yd[0]
        yd_dau = registry.khop_nhanh(chuan_hoa_truoc_dinh_tuyen(cac_y_dinh[0][0]), dung_ngu_nghia=True)
        nhom_lon, nhan_yd, che_do = _lay_meta_y_dinh(ma_yd, yd_dau)
        lich_su_gon = lich_su[-MAX_LUOT_NGU_CANH_NHANH:]
        chi_muc = {"lich_su_hoi_thoai": lich_su_gon, "ten_nguoi_dung": ten_nguoi_dung}
        goc_du_an = _lay_goc_du_an()

        if len(cac_y_dinh) == 1:
            cau_tra_loi_ten = _xu_ly_nhanh_cau_hoi_ten(prompt_sach, ten_nguoi_dung)
            if cau_tra_loi_ten is not None:
                logger.info("Tra loi nhanh cau hoi ten (phien=%s)", ma_phien)
                ghi_luot_hoi_thoai(ma_phien, prompt_sach, cau_tra_loi_ten, y_dinh=ma_yd)
                ghi_nhan_tuong_tac_qa(prompt_sach, ma_yd, cau_tra_loi_ten, luot_truoc=luot_truoc)
                return _xay_dung_ket_qua_dieu_phoi(
                    ma_yd,
                    nhan_yd,
                    nhom_lon,
                    {"noi_dung": cau_tra_loi_ten, "chuyen_huong_tao_app": False},
                    trung_cache=False,
                    danh_sach_y_dinh=ds_ma_yd,
                )

            khoa_cache = f"{ma_yd}:{chuan_hoa_khoa_prompt(prompt_sach)}"
            cho_phep_cache = (
                _co_the_dung_cache(ma_yd, che_do, bo_qua_cache, ten_nguoi_dung)
                and not lich_su
                and not la_tin_hieu_dinh_chinh(prompt_sach)
            )
            if cho_phep_cache:
                kq_cache = lay_tu_cache(khoa_cache)
                if kq_cache is not None:
                    noi_dung_cache = str(kq_cache.get("noi_dung") or "")
                    ghi_luot_hoi_thoai(ma_phien, prompt_sach, noi_dung_cache, y_dinh=ma_yd)
                    ghi_nhan_tuong_tac_qa(prompt_sach, ma_yd, noi_dung_cache, luot_truoc=luot_truoc)
                    return _xay_dung_ket_qua_dieu_phoi(
                        ma_yd, nhan_yd, nhom_lon, kq_cache, trung_cache=True, danh_sach_y_dinh=ds_ma_yd
                    )

            logger.info("Dieu phoi don y dinh (phien=%s) -> %s", ma_phien, ma_yd)
            noi_dung_kq, chuyen_huong = _thuc_thi_mot_nhanh(prompt_sach, ma_yd, goc_du_an, chi_muc)
            kq = {"noi_dung": noi_dung_kq, "chuyen_huong_tao_app": chuyen_huong}
            ghi_luot_hoi_thoai(ma_phien, prompt_sach, noi_dung_kq, y_dinh=ma_yd)
            ghi_nhan_tuong_tac_qa(prompt_sach, ma_yd, noi_dung_kq, luot_truoc=luot_truoc)
            if cho_phep_cache:
                luu_vao_cache(khoa_cache, kq, ttl_giay=_lay_ttl_theo_che_do(che_do))
            return _xay_dung_ket_qua_dieu_phoi(
                ma_yd, nhan_yd, nhom_lon, kq, trung_cache=False, danh_sach_y_dinh=ds_ma_yd
            )

        logger.info("Dieu phoi da y dinh (phien=%s) -> %s", ma_phien, ds_ma_yd)
        phan_noi_dung: list[str] = []
        co_chuyen_huong = False
        for idx, (doan_cau, ma_con) in enumerate(cac_y_dinh, start=1):
            logger.info("Thuc thi y dinh con #%d: ma='%s', cau='%s'", idx, ma_con, doan_cau)
            noi_con, huong_con = _thuc_thi_mot_nhanh(doan_cau, ma_con, goc_du_an, chi_muc)
            co_chuyen_huong = co_chuyen_huong or huong_con
            phan_noi_dung.append(f"### Ý định {idx}: `{ma_con}`\n{noi_con}")

        noi_dung_tong = "\n\n---\n\n".join(phan_noi_dung)
        kq_tong = {"noi_dung": noi_dung_tong, "chuyen_huong_tao_app": co_chuyen_huong}
        ghi_luot_hoi_thoai(ma_phien, prompt_sach, noi_dung_tong, y_dinh=ma_yd)
        ghi_nhan_tuong_tac_qa(prompt_sach, ma_yd, noi_dung_tong, luot_truoc=luot_truoc)
        return _xay_dung_ket_qua_dieu_phoi(
            ma_yd, nhan_yd, nhom_lon, kq_tong, trung_cache=False, danh_sach_y_dinh=ds_ma_yd
        )
    except Exception as loi:
        logger.error("Loi xu_ly_prompt_da_y_dinh: %s", loi, exc_info=True)
        return {"ok": False, "error": f"Lỗi điều phối ý định: {loi}"}