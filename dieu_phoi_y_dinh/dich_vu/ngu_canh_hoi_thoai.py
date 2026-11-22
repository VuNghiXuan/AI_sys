# ============================================================================
# File Path: dieu_phoi_y_dinh/dich_vu/ngu_canh_hoi_thoai.py
# Module: Truy Xuat Ngu Canh, Ten Nguoi Dung & Thong Tin May
# Linked Files: bo_nao_cache_cosine.py, xu_ly_chat.py, mau_y_dinh.py
# Purpose: Doc cac luot prompt & ket_qua_hien_thi gan nhat (RAM + DB),
#          trich xuat chinh xac ten nguoi dung tu prompt truoc va doc thong tin may.
# ============================================================================

import logging
import os
import platform
import re

logger = logging.getLogger(__name__)

_TU_KHONG_PHAI_TEN = {
    "gì", "gi", "nào", "nao", "ai", "bot", "đây", "day", "đó", "do",
    "máy", "may", "qwen", "ollama", "nhắc", "nhac", "tên", "ten", "là", "la",
}


def lay_cac_luot_gan_day(gioi_han: int = 10) -> list[dict]:
    """Lay danh sach luot trao doi gan nhat (uu tien RAM, bo sung tu DB LichSuDieuPhoi)."""
    ket_qua: list[dict] = []
    try:
        from . import bo_nao_cache_cosine as bo_nao

        ds_ram = getattr(bo_nao, "_LICH_SU_HOI_THOAI", []) or []
        for muc in ds_ram[-gioi_han:]:
            if isinstance(muc, dict) and muc.get("prompt"):
                ket_qua.append({
                    "prompt": str(muc.get("prompt", "")).strip(),
                    "ket_qua_hien_thi": str(muc.get("ket_qua_hien_thi", "")).strip(),
                    "y_dinh": str(muc.get("loai_nhanh") or muc.get("y_dinh") or "").strip(),
                })
    except Exception as loi:
        logger.warning("Khong doc duoc lich su RAM: %s", loi)

    if len(ket_qua) < gioi_han:
        try:
            from ..models import LichSuDieuPhoi

            da_co = {x["prompt"] for x in ket_qua}
            for obj in LichSuDieuPhoi.objects.order_by("-id")[:gioi_han]:
                if obj.prompt and obj.prompt not in da_co:
                    ket_qua.append({
                        "prompt": obj.prompt.strip(),
                        "ket_qua_hien_thi": (obj.ket_qua_hien_thi or "").strip(),
                        "y_dinh": (obj.y_dinh or "").strip(),
                    })
                    if len(ket_qua) >= gioi_han:
                        break
        except Exception as loi:
            logger.warning("Khong doc duoc LichSuDieuPhoi tu DB: %s", loi)

    return ket_qua[-gioi_han:]


def tim_ten_trong_lich_su() -> str | None:
    """Chi tim ten nguoi dung tu cac cau tu gioi thieu trong 'prompt' (khong quet cau tra loi AI)."""
    cac_luot = lay_cac_luot_gan_day(gioi_han=25)
    mau_ten = re.compile(
        r"\b(?:tên\s+(?:tao|mình|minh|tôi|toi|anh|em)\s*(?:là|la)?|(?:tao|mình|minh|tôi|toi|anh|em)\s+(?:tên|ten|là|la)\s*(?:là|la)?)\s+([a-zA-Z0-9_à-ỹ]{1,20})\b",
        flags=re.IGNORECASE,
    )
    for luot in reversed(cac_luot):
        cau_hoi = (luot.get("prompt") or "").strip()
        if not cau_hoi:
            continue
        khop = mau_ten.search(cau_hoi)
        if khop:
            ten = khop.group(1).strip().title()
            if ten.lower() not in _TU_KHONG_PHAI_TEN:
                return ten
    return None


def lay_thong_tin_may_hien_tai() -> str:
    """Doc thong tin cau hinh may tu DB (neu co) ket hop thong so he dieu hanh/CPU hien tai."""
    thong_tin_db = ""
    try:
        from django.apps import apps

        for model in apps.get_models():
            if "cauhinhmay" in model._meta.model_name:
                ban_ghi = model.objects.first()
                if ban_ghi:
                    thong_tin_db = f"Cấu hình DB ({model._meta.db_table}): {ban_ghi}"
                break
    except Exception as loi:
        logger.warning("Khong doc duoc bang cau hinh may tu DB: %s", loi)

    os_info = f"{platform.system()} {platform.release()}"
    cpu_luong = os.cpu_count() or "?"
    may_info = f"OS: {os_info} | CPU threads: {cpu_luong}"
    return f"{thong_tin_db} | {may_info}" if thong_tin_db else may_info


def xu_ly_cau_hoi_nhac_lai(noi_dung: str) -> str | None:
    """Xu ly cac cau hoi nhac lai ten, thong tin may hoac noi dung trao doi truoc."""
    thuong = (noi_dung or "").strip().lower()

    if re.search(
        r"\b(nhắc\s+lại\s+tên|nhac\s+lai\s+ten|tên\s+(tao|mình|minh|tôi|toi)|tôi\s+tên\s+gì|toi\s+ten\s+gi|tao\s+tên\s+gì|tao\s+ten\s+gi)\b",
        thuong,
    ):
        ten = tim_ten_trong_lich_su()
        if ten:
            return f"Tên của bạn là {ten} (theo lượt tự giới thiệu trước đó)."
        return "Mình chưa thấy lượt tự giới thiệu tên nào trong lịch sử gần đây."

    if re.search(
        r"\b(thông\s+tin\s+máy|thong\s+tin\s+may|cấu\s+hình\s+máy|cau\s+hinh\s+may|máy\s+(tao|mình|minh|tôi|toi))\b",
        thuong,
    ):
        return lay_thong_tin_may_hien_tai()

    if re.search(
        r"\b(nội\s+dung\s+trao\s+đổi|noi\s+dung\s+trao\s+doi|vừa\s+hỏi\s+gì|vua\s+hoi\s+gi|lúc\s+nãy|luc\s+nay)\b",
        thuong,
    ):
        cac_luot = lay_cac_luot_gan_day(gioi_han=6)
        if not cac_luot:
            return "Chưa có lịch sử trao đổi nào được lưu."
        tom_tat = [f"- Hỏi: {x['prompt']} -> Đáp: {x['ket_qua_hien_thi'][:90]}" for x in cac_luot]
        return "Các lượt trao đổi gần đây:\n" + "\n".join(tom_tat)

    return None