# ============================================================================
# File Path: xuong_tao_app/urls.py
# Module: Dinh Tuyen URL Va API Cua Xuong Tao App
# Linked Files: giao_dien/trang_xuong_tao_app.py, giao_dien/api_xuong_tao_app.py
# Purpose: Khai bao route giao dien chinh va cac endpoint thao tac tung buoc
#          cua Xuong Tao App.
# ============================================================================

from django.urls import path

from xuong_tao_app.giao_dien.api_xuong_tao_app import (
    api_hoan_tac_ban_luu,
    api_nap_vao_tab_he_thong,
    api_quet_va_thiet_ke,
    api_sinh_code_sandbox,
    api_sua_hoac_nang_cap,
)
from xuong_tao_app.giao_dien.trang_xuong_tao_app import hien_thi_trang_xuong_tao_app

app_name = "xuong_tao_app"

urlpatterns = [
    path("", hien_thi_trang_xuong_tao_app, name="xuong_tao_app"),
    path("api/quet-va-thiet-ke/", api_quet_va_thiet_ke, name="api_quet_va_thiet_ke"),
    path("api/sinh-code-sandbox/", api_sinh_code_sandbox, name="api_sinh_code_sandbox"),
    path("api/sua-hoac-nang-cap/", api_sua_hoac_nang_cap, name="api_sua_hoac_nang_cap"),
    path("api/hoan-tac-ban-luu/", api_hoan_tac_ban_luu, name="api_hoan_tac_ban_luu"),
    path("api/nap-vao-tab-he-thong/", api_nap_vao_tab_he_thong, name="api_nap_vao_tab_he_thong"),
]