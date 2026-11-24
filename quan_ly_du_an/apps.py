# ============================================================================
# File Path: quan_ly_du_an/apps.py
# Module: Cau Hinh App quan_ly_du_an Va Khoi Dong Dong Bo Map
# Linked Files: quan_ly_du_an/dich_vu/cap_nhat_project_map.py, PROJECT_MAP.md
# Purpose: Tu dong kich hoat quet va dong bo PROJECT_MAP.md khi khoi dong
#          he thong o luong nen an toan.
# ============================================================================

import logging
import os
import sys
import threading

from django.apps import AppConfig

logger = logging.getLogger(__name__)


def _chay_dong_bo_map_nen() -> None:
    """Chay cap nhat PROJECT_MAP.md o thread nen de khong chan khoi dong."""
    try:
        from quan_ly_du_an.dich_vu.cap_nhat_project_map import dong_bo_project_map_neu_can

        ket_qua = dong_bo_project_map_neu_can()
        logger.info("Khoi dong dong bo PROJECT_MAP.md: %s", ket_qua)
    except Exception as loi:
        logger.warning("Bo qua loi dong bo PROJECT_MAP.md khi khoi dong: %s", loi)


class QuanLyDuAnConfig(AppConfig):
    """Cau hinh ung dung quan_ly_du_an."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "quan_ly_du_an"

    def ready(self) -> None:
        """Kich hoat dong bo PROJECT_MAP.md mot lan khi tien trinh chinh khoi dong."""
        if "runserver" in sys.argv and os.environ.get("RUN_MAIN") != "true":
            return
        threading.Thread(target=_chay_dong_bo_map_nen, name="sync-project-map", daemon=True).start()