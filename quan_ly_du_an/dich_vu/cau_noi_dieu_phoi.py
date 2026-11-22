# ============================================================================
# File Path: quan_ly_du_an/dich_vu/cau_noi_dieu_phoi.py
# Module: Cau Noi Goi xu_ly_prompt_da_y_dinh & Doc Lich Su DB
# Linked Files: dieu_phoi_y_dinh/dich_vu/dieu_phoi_nhanh.py,
#               dieu_phoi_y_dinh/models.py
# Purpose: Goi thang xu_ly_prompt_da_y_dinh cua dieu_phoi_nhanh.py (khong luu
#          trung DB) va cung cap ham doc lich su cu theo before_id cho giao dien.
# ============================================================================

import logging
import time

from dieu_phoi_y_dinh.dich_vu.dieu_phoi_nhanh import xu_ly_prompt_da_y_dinh
from dieu_phoi_y_dinh.models import LichSuDieuPhoi

logger = logging.getLogger(__name__)


def dinh_dang_thoi_luong(so_giay: float) -> str:
    """Dinh dang so giay thuc thi thanh chuoi mm:ss."""
    tong = max(0, int(round(so_giay)))
    return f"{str(tong // 60).zfill(2)}:{str(tong % 60).zfill(2)}s"


def _dinh_dang_phan_hoi_tu_ket_qua(ket_qua: dict, prompt: str) -> str:
    """Lay noi dung ket_qua tu cac_nhanh hoac tom_tat de hien thi tren khung chat."""
    cac_nhanh = ket_qua.get("cac_nhanh") or []
    ds_dong = []
    for nhanh in cac_nhanh:
        noi_dung_kq = str(nhanh.get("ket_qua") or "").strip()
        if noi_dung_kq:
            ds_dong.append(noi_dung_kq)

    if len(ds_dong) == 1:
        return ds_dong[0]
    if len(ds_dong) > 1:
        return "\n".join(f"- {dong}" for dong in ds_dong)

    tom_tat = str(ket_qua.get("tom_tat") or "").strip()
    return tom_tat or f"Đã xử lý yêu cầu: {prompt}"


def chay_luong_y_dinh_va_luu_lich_su(prompt: str, che_do: str = "luong_chinh") -> dict:
    """Goi xu_ly_prompt_da_y_dinh tu dieu_phoi_nhanh.py va tra du lieu chuan cho UI."""
    thoi_diem_bat_dau = time.monotonic()
    logger.info("Goi xu_ly_prompt_da_y_dinh (che_do=%s, do_dai=%d)", che_do, len(prompt))

    ket_qua = xu_ly_prompt_da_y_dinh(prompt)
    if not ket_qua.get("ok"):
        raise RuntimeError(ket_qua.get("error") or "Lỗi xử lý từ dieu_phoi_nhanh")

    thoi_luong_chu = dinh_dang_thoi_luong(time.monotonic() - thoi_diem_bat_dau)
    cac_nhanh = ket_qua.get("cac_nhanh") or []
    phan_hoi = _dinh_dang_phan_hoi_tu_ket_qua(ket_qua, prompt)
    ten_model = "qwen2.5-coder:7b" if (len(prompt) > 220 or len(cac_nhanh) >= 2) else "qwen2.5:3b"

    ban_ghi_moi = LichSuDieuPhoi.objects.order_by("-id").first()
    id_db = ban_ghi_moi.id if ban_ghi_moi else None

    return {
        "id_db": id_db,
        "prompt": prompt,
        "phan_hoi": phan_hoi,
        "ten_model": ten_model,
        "thoi_gian_phan_hoi": thoi_luong_chu,
        "so_nhanh": len(cac_nhanh) if cac_nhanh else 1,
        "ma_linh_vuc": ket_qua.get("ma_linh_vuc") or "tong_quat",
        "ten_linh_vuc": ket_qua.get("ten_linh_vuc") or "Đa ngành / Tổng quát",
        "trung_cache": bool(ket_qua.get("trung_cache", False)),
    }


def lay_danh_sach_lich_su_cu(before_id: int | None = None, limit: int = 10) -> list[dict]:
    """Doc cac ban ghi LichSuDieuPhoi cu hon (id < before_id) sap xep giam dan theo id."""
    kich_thuoc = max(1, min(int(limit or 10), 50))
    truy_van = LichSuDieuPhoi.objects.all().order_by("-id")
    if before_id is not None:
        truy_van = truy_van.filter(id__lt=before_id)

    return [
        {
            "id": bg.id,
            "prompt": bg.prompt,
            "ket_qua_hien_thi": bg.ket_qua_hien_thi,
            "y_dinh": bg.y_dinh,
            "ma_linh_vuc": bg.ma_linh_vuc,
            "ten_linh_vuc": bg.ten_linh_vuc,
            "trung_cache": bg.trung_cache,
            "thoi_gian_tao": bg.thoi_gian_tao.isoformat() if bg.thoi_gian_tao else "",
        }
        for bg in truy_van[:kich_thuoc]
    ]