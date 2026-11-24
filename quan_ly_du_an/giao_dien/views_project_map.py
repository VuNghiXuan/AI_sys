# ============================================================================
# File Path: quan_ly_du_an/views_project_map.py
# Module: API Cap Nhat PROJECT_MAP.md Tu Giao Dien
# Linked Files: quan_ly_du_an/dich_vu/cap_nhat_project_map.py, PROJECT_MAP.md
# Purpose: Endpoint POST de nguoi dung bam nut cap nhat PROJECT_MAP.md ngay.
# ============================================================================

import logging

from django.http import JsonResponse
from django.views.decorators.http import require_POST

from quan_ly_du_an.dich_vu.cap_nhat_project_map import dong_bo_project_map_neu_can

logger = logging.getLogger(__name__)


@require_POST
def api_cap_nhat_project_map(request):
    """Xu ly bam nut cap nhat PROJECT_MAP.md va tra ve trang thai JSON."""
    del request
    try:
        ket_qua = dong_bo_project_map_neu_can()
        logger.info("Bam nut cap nhat PROJECT_MAP.md thanh cong: %s", ket_qua)
        return JsonResponse({"ok": True, **ket_qua})
    except Exception as loi:
        logger.error("Loi khi bam nut cap nhat PROJECT_MAP.md: %s", loi, exc_info=True)
        return JsonResponse({"ok": False, "error": str(loi)}, status=500)