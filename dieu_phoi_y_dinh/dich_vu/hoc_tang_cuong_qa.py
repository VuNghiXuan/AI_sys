# ============================================================================
# File Path: dieu_phoi_y_dinh/dich_vu/hoc_tang_cuong_qa.py
# Module: Hoc Tang Cuong Tu Cap Cau Hoi Va Cau Tra Loi
# Linked Files: dieu_phoi_y_dinh/dich_vu/dieu_phoi_nhanh.py,
#               dieu_phoi_y_dinh/dich_vu/bo_nho_va_cache.py
# Purpose: Ghi nhan phan hoi dung/sai/dinh chinh tu hoi thoai de tang/giam
#          trong so y dinh va luu mau Q&A da chuan hoa cuc bo.
# ============================================================================

import json
import logging
from pathlib import Path
import re
import threading
from typing import Any
import unicodedata

logger = logging.getLogger(__name__)

LOCK_HOC_QA = threading.Lock()
DUONG_DAN_DU_LIEU_QA = Path(__file__).resolve().parents[1] / "du_lieu" / "bo_nho_hoc_qa.json"
MAX_MAU_QA_LUU = 300

MAU_PHAN_BAC_DINH_CHINH = (
    r"\b(?:sai\s+roi|sai\s+rồi|nham\s+roi|nhầm\s+rồi|khong\s+phai|không\s+phải|"
    r"tao\s+hoi|tôi\s+hỏi|ho\s+i\s+lai|hỏi\s+lại|ten\s+tao|tên\s+tao|ham\s+ma|hàm\s+mà)\b"
)


def _chuan_hoa_khoa(van_ban: str) -> str:
    """Chuan hoa chuoi (bo dau, thuong, gom khoang trang) lam khoa hoc tang cuong."""
    sach = (van_ban or "").strip().lower()
    khong_dau = "".join(
        ch for ch in unicodedata.normalize("NFD", sach)
        if unicodedata.category(ch) != "Mn"
    ).replace("đ", "d")
    return re.sub(r"\s+", " ", khong_dau).strip()


def la_tin_hieu_dinh_chinh(prompt: str) -> bool:
    """Kiem tra prompt co mang sac thai phan bac hoac nhac lai y dinh truoc hay khong."""
    return bool(re.search(MAU_PHAN_BAC_DINH_CHINH, (prompt or "").lower()))


def _doc_du_lieu_qa() -> dict[str, Any]:
    """Doc file du lieu hoc tang cuong Q&A, tra ve cau truc mac dinh neu chua co."""
    if not DUONG_DAN_DU_LIEU_QA.exists():
        logger.info("Khoi tao du lieu hoc Q&A moi tai %s", DUONG_DAN_DU_LIEU_QA)
        return {"trong_so_y_dinh": {}, "mau_qa": []}
    try:
        raw = json.loads(DUONG_DAN_DU_LIEU_QA.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            raw.setdefault("trong_so_y_dinh", {})
            raw.setdefault("mau_qa", [])
            return raw
    except Exception as loi:
        logger.warning("Khong doc duoc bo_nho_hoc_qa.json: %s", loi)
    return {"trong_so_y_dinh": {}, "mau_qa": []}


def _ghi_du_lieu_qa(du_lieu: dict[str, Any]) -> None:
    """Ghi du lieu hoc tang cuong Q&A an toan ra dia."""
    try:
        DUONG_DAN_DU_LIEU_QA.parent.mkdir(parents=True, exist_ok=True)
        DUONG_DAN_DU_LIEU_QA.write_text(
            json.dumps(du_lieu, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.info("Da ghi du lieu hoc Q&A vao %s", DUONG_DAN_DU_LIEU_QA)
    except Exception as loi:
        logger.error("Loi ghi bo_nho_hoc_qa.json: %s", loi, exc_info=True)


def cap_nhat_trong_so_y_dinh(khoa_cau: str, ma_y_dinh: str, delta: float, du_lieu: dict[str, Any]) -> None:
    """Cap nhat diem hoc tang cuong cho cap (khoa_cau, ma_y_dinh) co gioi han kep [-3.0, +3.0]."""
    if not khoa_cau or not ma_y_dinh:
        return
    trong_so = du_lieu.setdefault("trong_so_y_dinh", {})
    muc = trong_so.setdefault(khoa_cau, {})
    diem_cu = float(muc.get(ma_y_dinh, 0.0))
    diem_moi = max(-3.0, min(3.0, round(diem_cu + delta, 3)))
    muc[ma_y_dinh] = diem_moi
    logger.info("Hoc tang cuong y_dinh khoa='%s' ma='%s': %.2f -> %.2f", khoa_cau, ma_y_dinh, diem_cu, diem_moi)


def _trich_khoa_va_y_dinh_luot_truoc(
    luot_truoc: dict[str, Any] | None,
    du_lieu: dict[str, Any],
) -> tuple[str, str]:
    """Trich (khoa_truoc, yd_truoc) tu luot user truoc, tranh lay nham cau tra loi assistant."""
    if isinstance(luot_truoc, dict):
        vai_tro = str(luot_truoc.get("role") or "").strip().lower()
        raw_prompt = luot_truoc.get("prompt") or luot_truoc.get("cau_hoi") or ""
        if not raw_prompt and vai_tro != "assistant":
            raw_prompt = luot_truoc.get("content") or ""
        khoa_truoc = _chuan_hoa_khoa(str(raw_prompt))
        yd_truoc = str(luot_truoc.get("y_dinh") or luot_truoc.get("intent") or "").strip()
        if khoa_truoc and yd_truoc:
            return khoa_truoc, yd_truoc

    for muc in reversed(du_lieu.get("mau_qa") or []):
        if isinstance(muc, dict):
            khoa_mau = _chuan_hoa_khoa(str(muc.get("khoa") or muc.get("prompt") or ""))
            yd_mau = str(muc.get("y_dinh") or "").strip()
            if khoa_mau and yd_mau:
                return khoa_mau, yd_mau
    return "", ""


def ghi_nhan_tuong_tac_qa(
    prompt_hien_tai: str,
    y_dinh_hien_tai: str,
    cau_tra_loi_hien_tai: str,
    luot_truoc: dict[str, Any] | None = None,
) -> None:
    """Hoc tu cap Q&A hien tai va danh gia dung/sai cho luot truoc dua tren phan hoi."""
    khoa_ht = _chuan_hoa_khoa(prompt_hien_tai)
    if not khoa_ht:
        return

    la_dinh_chinh = la_tin_hieu_dinh_chinh(prompt_hien_tai)
    with LOCK_HOC_QA:
        du_lieu = _doc_du_lieu_qa()
        if luot_truoc or la_dinh_chinh:
            khoa_truoc, yd_truoc = _trich_khoa_va_y_dinh_luot_truoc(luot_truoc, du_lieu)
            if la_dinh_chinh:
                cap_nhat_trong_so_y_dinh(khoa_truoc, yd_truoc, delta=-1.0, du_lieu=du_lieu)
            elif khoa_truoc and yd_truoc:
                cap_nhat_trong_so_y_dinh(khoa_truoc, yd_truoc, delta=+0.25, du_lieu=du_lieu)

        if y_dinh_hien_tai and not la_dinh_chinh:
            cap_nhat_trong_so_y_dinh(khoa_ht, y_dinh_hien_tai, delta=+0.15, du_lieu=du_lieu)

        mau_qa: list[dict[str, Any]] = du_lieu.get("mau_qa") or []
        mau_qa.append({
            "khoa": khoa_ht,
            "prompt": (prompt_hien_tai or "").strip(),
            "y_dinh": y_dinh_hien_tai,
            "tra_loi": (cau_tra_loi_hien_tai or "").strip()[:1200],
            "la_dinh_chinh": la_dinh_chinh,
        })
        du_lieu["mau_qa"] = mau_qa[-MAX_MAU_QA_LUU:]
        _ghi_du_lieu_qa(du_lieu)


def lay_diem_hoc_y_dinh(prompt: str, ma_y_dinh: str) -> float:
    """Lay diem hoc tang cuong da tich luy cho (prompt, ma_y_dinh)."""
    khoa = _chuan_hoa_khoa(prompt)
    if not khoa or not ma_y_dinh:
        return 0.0
    with LOCK_HOC_QA:
        du_lieu = _doc_du_lieu_qa()
        return float((du_lieu.get("trong_so_y_dinh") or {}).get(khoa, {}).get(ma_y_dinh, 0.0))


def tim_mau_qa_da_dinh_chinh(prompt: str) -> dict[str, Any] | None:
    """Tim mau Q&A da duoc dinh chinh/xac nhan gan nhat cho cung cau hoi chuan hoa."""
    khoa = _chuan_hoa_khoa(prompt)
    if not khoa:
        return None
    with LOCK_HOC_QA:
        du_lieu = _doc_du_lieu_qa()
        for muc in reversed(du_lieu.get("mau_qa") or []):
            if muc.get("khoa") == khoa and muc.get("y_dinh"):
                return muc
    return None