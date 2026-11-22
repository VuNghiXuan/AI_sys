# ============================================================================
# File Path: quan_ly_du_an/api_dieu_phoi.py
# Module: API JSON Cho Lich Su Hoi Thoai & Luong Xu Ly Y Dinh
# Linked Files: quan_ly_du_an/dich_vu/cau_noi_dieu_phoi.py, quan_ly_du_an/urls.py
# Purpose: Cung cap endpoint GET lich su tu DB va POST chay luong y dinh.
# ============================================================================

import json
import logging

from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from .dich_vu.cau_noi_dieu_phoi import (
    chay_luong_y_dinh_va_luu_lich_su,
    lay_danh_sach_lich_su_cu,
)

logger = logging.getLogger(__name__)


@require_GET
def api_lich_su_hoi_thoai(request):
    """Tra ve danh sach lich su cu hon theo tham so before_id va limit."""
    before_raw = request.GET.get("before_id")
    limit_raw = request.GET.get("limit", "10")

    before_id = None
    if before_raw:
        try:
            before_id = int(before_raw)
        except ValueError:
            return JsonResponse({"ok": False, "loi": "before_id khong hop le"}, status=400)

    try:
        limit = int(limit_raw)
    except ValueError:
        limit = 10

    try:
        items = lay_danh_sach_lich_su_cu(before_id=before_id, limit=limit)
        return JsonResponse({"ok": True, "items": items})
    except Exception as loi:
        logger.error("Loi api_lich_su_hoi_thoai: %s", loi, exc_info=True)
        return JsonResponse({"ok": False, "loi": "Khong tai duoc lich su"}, status=500)


@require_POST
def api_xu_ly_y_dinh(request):
    """Nhan prompt, chay luong xu ly y dinh, luu LichSuDieuPhoi va tra ket qua."""
    try:
        du_lieu = json.loads((request.body or b"{}").decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"ok": False, "loi": "Du lieu JSON khong hop le"}, status=400)

    prompt = (du_lieu.get("prompt") or "").strip()
    che_do = (du_lieu.get("che_do") or "luong_chinh").strip()
    if not prompt:
        return JsonResponse({"ok": False, "loi": "Prompt khong duoc de trong"}, status=400)

    try:
        ket_qua = chay_luong_y_dinh_va_luu_lich_su(prompt=prompt, che_do=che_do)
        return JsonResponse({"ok": True, "ket_qua": ket_qua})
    except Exception as loi:
        logger.error("Loi api_xu_ly_y_dinh: %s", loi, exc_info=True)
        return JsonResponse({"ok": False, "loi": "Loi khi xu ly luong y dinh"}, status=500)