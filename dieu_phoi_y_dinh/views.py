# ============================================================================
# File Path: dieu_phoi_y_dinh/views.py
# Module: API Dieu Phoi Y Dinh
# Linked Files: urls.py, dich_vu/dieu_phoi_nhanh.py
# Purpose: Nhan prompt tu client va tra ve ket qua dieu phoi y dinh da tang.
# ============================================================================

import json
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .dich_vu.dieu_phoi_nhanh import xu_ly_prompt_da_y_dinh

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def api_dieu_phoi_y_dinh(request):
    try:
        du_lieu = json.loads((request.body or b"{}").decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "JSON không hợp lệ"}, status=400)

    prompt = (du_lieu.get("prompt") or "").strip()
    chon_phuong_an = (du_lieu.get("chon_phuong_an") or "").strip()
    bo_qua_cache = bool(du_lieu.get("bo_qua_cache", False))

    ket_qua = xu_ly_prompt_da_y_dinh(
        prompt=prompt,
        chon_phuong_an=chon_phuong_an,
        bo_qua_cache=bo_qua_cache,
    )
    ma_trang_thai = 200 if ket_qua.get("ok") else 400
    return JsonResponse(ket_qua, status=ma_trang_thai)