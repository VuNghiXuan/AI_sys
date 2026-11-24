# ============================================================================
# File Path: xuong_tao_app/dich_vu/chuyen_huong_tao_app/dieu_phoi_xac_nhan.py
# Module: Dieu Phoi Hoi Xac Nhan & Chuyen Tab Xuong Tao App
# Linked Files: cho_xac_nhan_tao_app.py, ../../giao_dien/trang_xuong_tao_app.py
# Purpose: Xu ly luong hoi xac nhan khi go tao app o prompt chinh, luu san
#          ngu canh vao tab xuong_tao_app khi dong y va tra payload chuyen tab.
# ============================================================================

import logging
from typing import Any

from xuong_tao_app.dich_vu.chuyen_huong_tao_app.cho_xac_nhan_tao_app import (
    DUONG_DAN_XUONG_TAO_APP,
    la_yeu_cau_tao_app,
    lay_trang_thai_cho,
    luu_trang_thai_cho,
    phan_loai_phan_hoi_xac_nhan,
    trich_duong_dan_nguon,
    xoa_trang_thai_cho,
)
from xuong_tao_app.giao_dien.trang_xuong_tao_app import luu_ngu_canh_vao_tab

logger = logging.getLogger(__name__)


def _tao_loi_hoi_xac_nhan(prompt_goc: str, duong_dan: str) -> str:
    """Tao loi hoi xac nhan ro rang truoc khi chuyen sang tab xuong_tao_app."""
    dong_nguon = (
        f"\n- Đường dẫn nguồn nhận diện: `{duong_dan}`"
        if duong_dan
        else "\n- Đường dẫn nguồn: *(chưa nêu, sẽ cấu hình trên tab Xưởng Tạo App)*"
    )
    return (
        "Anh đang yêu cầu tạo app mới ngay ở khung prompt chính:\n"
        f"- Yêu cầu: \"{prompt_goc}\""
        f"{dong_nguon}\n"
        "Để tránh làm nhiễu luồng prompt chính, xác nhận đồng ý để chuyển sang tab **Xưởng Tạo App (`xuong_tao_app`)** và giữ nguyên thông tin này nhé?"
    )


def xu_ly_xac_nhan_tao_app(
    van_ban: str,
    session: Any = None,
    request: Any = None,
) -> dict[str, Any] | None:
    """Kiem tra va xu ly trang thai cho xac nhan hoac yeu cau tao app moi.

    Tra ve dict ket qua neu luong nay xu ly; tra ve None neu prompt thuoc luong khac.
    """
    phien = session if session is not None else getattr(request, "session", None)
    noi_dung = (van_ban or "").strip()
    trang_thai_cho = lay_trang_thai_cho(phien)

    if trang_thai_cho:
        phan_hoi = phan_loai_phan_hoi_xac_nhan(noi_dung)
        prompt_goc = trang_thai_cho.get("prompt_goc", "")
        duong_dan = trang_thai_cho.get("duong_dan_nguon", "")

        if phan_hoi == "dong_y":
            xoa_trang_thai_cho(phien)
            if request is not None:
                luu_ngu_canh_vao_tab(request, prompt_goc, duong_dan)
            logger.info("Nguoi dung xac nhan chuyen sang xuong_tao_app cho yeu cau: '%s'", prompt_goc)
            return {
                "da_xu_ly": True,
                "trang_thai": "chuyen_tab_tao_app",
                "chuyen_tab": True,
                "target_tab": "xuong_tao_app",
                "target_url": DUONG_DAN_XUONG_TAO_APP,
                "prompt_goc": prompt_goc,
                "duong_dan_nguon": duong_dan,
                "noi_dung_tra_loi": (
                    "Đã xác nhận. Đang chuyển sang tab **Xưởng Tạo App (`xuong_tao_app`)** "
                    f"với yêu cầu: \"{prompt_goc}\""
                    + (f" và đường dẫn `{duong_dan}`." if duong_dan else ".")
                ),
            }

        if phan_hoi == "tu_choi":
            xoa_trang_thai_cho(phien)
            logger.info("Nguoi dung huy yeu cau chuyen sang xuong_tao_app")
            return {
                "da_xu_ly": True,
                "trang_thai": "da_huy_tao_app",
                "chuyen_tab": False,
                "target_tab": None,
                "noi_dung_tra_loi": "Đã hủy yêu cầu chuyển sang **Xưởng Tạo App**, hệ thống giữ nguyên luồng prompt chính.",
            }

        if la_yeu_cau_tao_app(noi_dung):
            duong_dan_moi = trich_duong_dan_nguon(noi_dung)
            luu_trang_thai_cho(phien, noi_dung, duong_dan_moi)
            return {
                "da_xu_ly": True,
                "trang_thai": "cho_xac_nhan_tao_app",
                "chuyen_tab": False,
                "target_tab": "xuong_tao_app",
                "prompt_goc": noi_dung,
                "duong_dan_nguon": duong_dan_moi,
                "noi_dung_tra_loi": _tao_loi_hoi_xac_nhan(noi_dung, duong_dan_moi),
            }

        logger.debug("Prompt hien tai khong phai xac nhan tao app, xoa trang thai cho cu de tiep tuc luong chinh")
        xoa_trang_thai_cho(phien)
        return None

    if la_yeu_cau_tao_app(noi_dung):
        duong_dan = trich_duong_dan_nguon(noi_dung)
        luu_trang_thai_cho(phien, noi_dung, duong_dan)
        return {
            "da_xu_ly": True,
            "trang_thai": "cho_xac_nhan_tao_app",
            "chuyen_tab": False,
            "target_tab": "xuong_tao_app",
            "prompt_goc": noi_dung,
            "duong_dan_nguon": duong_dan,
            "noi_dung_tra_loi": _tao_loi_hoi_xac_nhan(noi_dung, duong_dan),
        }

    return None