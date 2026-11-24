# ============================================================================
# File Path: xuong_tao_app/dich_vu/dang_ky_tab_app/__init__.py
# Module: Khoi Tao Package Dang Ky Tab Va Chuc Nang Con Cua App
# Linked Files: quan_ly_registry_tab.py, nap_app_vao_he_thong.py
# Purpose: Xuat ham quan ly registry tab app va quy trinh nap app da test on
#          vao 1 tab he thong kem cac chuc nang con.
# ============================================================================

from xuong_tao_app.dich_vu.dang_ky_tab_app.nap_app_vao_he_thong import (
    nap_app_vao_khung_he_thong,
)
from xuong_tao_app.dich_vu.dang_ky_tab_app.quan_ly_registry_tab import (
    doc_danh_sach_tab_app,
    go_dang_ky_tab_app,
    luu_hoac_cap_nhat_tab_app,
)

__all__ = [
    "doc_danh_sach_tab_app",
    "luu_hoac_cap_nhat_tab_app",
    "go_dang_ky_tab_app",
    "nap_app_vao_khung_he_thong",
]