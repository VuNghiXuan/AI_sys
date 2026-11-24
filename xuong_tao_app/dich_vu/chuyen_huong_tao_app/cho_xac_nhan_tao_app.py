# ============================================================================
# File Path: xuong_tao_app/dich_vu/chuyen_huong_tao_app/cho_xac_nhan_tao_app.py
# Module: Quan Ly Trang Thai Cho Xac Nhan Tao App
# Linked Files: dieu_phoi_xac_nhan.py, dieu_phoi_nhanh.py
# Purpose: Nhan dien yeu cau tao app/duong dan nguon o prompt chinh, luu tam
#          ngu canh cho xac nhan va xu ly phan hoi dong y/huy cua nguoi dung.
# ============================================================================

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

SESSION_KEY_CHO_XAC_NHAN = "xuong_tao_app_cho_xac_nhan"
DUONG_DAN_XUONG_TAO_APP = "/xuong-tao-app/"

_MAU_YEU_CAU_TAO_APP = re.compile(
    r"\b(tạo|tao|lập|lap|xây\s+dựng|xay\s+dung|dựng|dung|sinh)\b[\s\S]{0,45}"
    r"\b(app|ap|ứng\s+dụng|ung\s+dung|hệ\s+thống\s+quản\s+lý|he\s+thong\s+quan\s+ly)\b",
    flags=re.IGNORECASE,
)

_MAU_DUONG_DAN_THU_MUC = re.compile(
    r"(?:[A-Za-z]:\\|/|\.\.?/)[A-Za-z0-9_\-./\\ ]+",
)

_MAU_DONG_Y = re.compile(
    r"^(?:đồng\s+ý|dong\s+y|ok|oke|okay|ừ|uh|ờ|chuyển\s+đi|chuyen\s+di|"
    r"làm\s+đi|lam\s+di|tạo\s+đi|tao\s+di|xác\s+nhận|xac\s+nhan|đúng\s+rồi|dung\s+roi)\b",
    flags=re.IGNORECASE,
)

_MAU_TU_CHOI = re.compile(
    r"^(?:không|khong|thôi|thoi|hủy|huy|bỏ|bo|chưa|chua|để\s+sau|de\s+sau)\b",
    flags=re.IGNORECASE,
)


def trich_duong_dan_nguon(van_ban: str) -> str:
    """Trich xuat duong dan thu muc/tep neu co trong prompt."""
    noi_dung = (van_ban or "").strip()
    if not noi_dung:
        return ""
    match = _MAU_DUONG_DAN_THU_MUC.search(noi_dung)
    duong_dan = match.group(0).strip(" \"'`,.;:") if match else ""
    if duong_dan:
        logger.debug("Da trich duong dan nguon: %s", duong_dan)
    return duong_dan


def la_yeu_cau_tao_app(van_ban: str) -> bool:
    """Kiem tra van ban co mang yeu cau tao app moi hay khong."""
    thuong = (van_ban or "").strip().lower()
    if not thuong:
        return False
    ket_qua = bool(_MAU_YEU_CAU_TAO_APP.search(thuong))
    logger.debug("Kiem tra yeu cau tao app cho '%s' -> %s", thuong, ket_qua)
    return ket_qua


def lay_trang_thai_cho(session: Any) -> dict[str, Any] | None:
    """Lay trang thai cho xac nhan tao app hien tai tu session."""
    if session is None:
        return None
    du_lieu = session.get(SESSION_KEY_CHO_XAC_NHAN)
    if not isinstance(du_lieu, dict) or not du_lieu.get("dang_cho"):
        return None
    return du_lieu


def luu_trang_thai_cho(session: Any, prompt_goc: str, duong_dan: str = "") -> dict[str, Any]:
    """Luu tam yeu cau tao app va duong dan nguon de cho nguoi dung xac nhan."""
    trang_thai = {
        "dang_cho": True,
        "prompt_goc": (prompt_goc or "").strip(),
        "duong_dan_nguon": (duong_dan or "").strip(),
        "target_app": "xuong_tao_app",
        "target_url": DUONG_DAN_XUONG_TAO_APP,
    }
    if session is not None:
        session[SESSION_KEY_CHO_XAC_NHAN] = trang_thai
        session.modified = True
    logger.info("Da luu trang thai cho xac nhan tao app (duong_dan='%s')", trang_thai["duong_dan_nguon"])
    return trang_thai


def xoa_trang_thai_cho(session: Any) -> None:
    """Xoa trang thai cho xac nhan khoi session."""
    if session is not None and SESSION_KEY_CHO_XAC_NHAN in session:
        del session[SESSION_KEY_CHO_XAC_NHAN]
        session.modified = True
        logger.info("Da xoa trang thai cho xac nhan tao app")


def phan_loai_phan_hoi_xac_nhan(van_ban: str) -> str:
    """Phan loai phan hoi cua nguoi dung khi dang cho xac nhan: dong_y | tu_choi | khac."""
    thuong = (van_ban or "").strip().lower()
    if not thuong:
        return "khac"
    if _MAU_TU_CHOI.search(thuong):
        return "tu_choi"
    if _MAU_DONG_Y.search(thuong):
        return "dong_y"
    return "khac"