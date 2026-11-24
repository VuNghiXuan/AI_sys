# ============================================================================
# File Path: xuong_tao_app/giao_dien/trang_xuong_tao_app.py
# Module: View & Dieu Huong Giao Dien Xuong Tao App
# Linked Files: ../urls.py, ../dich_vu/chuyen_huong_tao_app/cho_xac_nhan_tao_app.py,
#               ../templates/xuong_tao_app/trang_chu_xuong_tao_app.html
# Purpose: Xu ly hien thi trang Xuong Tao App ke thua khung chinh cua
#          quan_ly_du_an va nap san du lieu chuyen huong tu prompt chinh.
# ============================================================================

import logging
from typing import Any

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from xuong_tao_app.dich_vu.chuyen_huong_tao_app.cho_xac_nhan_tao_app import (
    DUONG_DAN_XUONG_TAO_APP,
)

logger = logging.getLogger(__name__)

SESSION_KEY_NGU_CANH_CHUYEN_TAB = "xuong_tao_app_ngu_canh_chuyen_tab"


def luu_ngu_canh_vao_tab(request: HttpRequest, prompt_goc: str, duong_dan_nguon: str = "") -> None:
    """Luu ngu canh da duoc xac nhan de tab xuong_tao_app tu dien khi mo."""
    if not hasattr(request, "session"):
        return
    request.session[SESSION_KEY_NGU_CANH_CHUYEN_TAB] = {
        "prompt_goc": (prompt_goc or "").strip(),
        "duong_dan_nguon": (duong_dan_nguon or "").strip(),
        "target_url": DUONG_DAN_XUONG_TAO_APP,
    }
    request.session.modified = True
    logger.info("Da luu ngu canh chuyen tab cho xuong_tao_app")


def _lay_va_tieu_thu_ngu_canh(request: HttpRequest) -> dict[str, Any]:
    """Doc ngu canh chuyen tab tu session hoac query param va xoa trang thai tam."""
    prompt_goc = (request.GET.get("prompt_goc") or "").strip()
    duong_dan_nguon = (request.GET.get("duong_dan_nguon") or "").strip()

    session = getattr(request, "session", None)
    if session and SESSION_KEY_NGU_CANH_CHUYEN_TAB in session:
        du_lieu = session.pop(SESSION_KEY_NGU_CANH_CHUYEN_TAB, {}) or {}
        session.modified = True
        if not prompt_goc:
            prompt_goc = str(du_lieu.get("prompt_goc") or "").strip()
        if not duong_dan_nguon:
            duong_dan_nguon = str(du_lieu.get("duong_dan_nguon") or "").strip()

    return {
        "prompt_goc": prompt_goc,
        "duong_dan_nguon": duong_dan_nguon,
    }


def hien_thi_trang_xuong_tao_app(request: HttpRequest) -> HttpResponse:
    """Render trang xuong_tao_app ke thua khung dieu khien chinh."""
    ngu_canh = _lay_va_tieu_thu_ngu_canh(request)
    logger.info(
        "Mo trang xuong_tao_app (co_prompt=%s, co_duong_dan=%s)",
        bool(ngu_canh["prompt_goc"]),
        bool(ngu_canh["duong_dan_nguon"]),
    )
    context = {
        "app_name": "xuong_tao_app",
        "tab_hien_tai": "xuong_tao_app",
        "tieu_de_tab": "Xưởng Tạo App",
        "prompt_goc": ngu_canh["prompt_goc"],
        "duong_dan_nguon": ngu_canh["duong_dan_nguon"],
        "cac_buoc_quy_trinh": [
            {"ma": "quet_thu_muc", "ten": "1. Quét folder & tóm tắt nghiệp vụ", "trang_thai": "cho"},
            {"ma": "thiet_ke_va_task", "ten": "2. Bản thiết kế & chia nhỏ task", "trang_thai": "cho"},
            {"ma": "sinh_ma_sandbox", "ten": "3. Sinh code & test môi trường riêng", "trang_thai": "cho"},
            {"ma": "tu_sua_va_nang_cap", "ten": "4. Test giao diện, sửa/nâng cấp theo ảnh & prompt", "trang_thai": "cho"},
            {"ma": "dang_ky_tab_app", "ten": "5. Đưa vào 1 tab hệ thống + các chức năng con", "trang_thai": "cho"},
        ],
    }
    return render(request, "xuong_tao_app/trang_chu_xuong_tao_app.html", context)