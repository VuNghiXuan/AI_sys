# ==============================================================================
# File Path: quan_ly_du_an/giao_dien/urls_giao_dien.py
# Description: URL routes for the AI_Sys testing and orchestration workbench.
# Linked Files: [quan_ly_du_an/giao_dien/views_dieu_khien.py]
# Logs: Map workbench root and profile detail URLs.
# ==============================================================================

from django.urls import path
from quan_ly_du_an.giao_dien.views_dieu_khien import trang_dieu_khien
from quan_ly_du_an.giao_dien.views_telemetry import api_telemetry_thuc_te
from .. import api_dieu_phoi

urlpatterns = [
    path("", trang_dieu_khien, name="giao_dien_trang_chu"),
    path("ho-so/<int:ho_so_id>/", trang_dieu_khien, name="giao_dien_ho_so"),

    path("api/telemetry-thuc/", api_telemetry_thuc_te, name="api_telemetry_thuc_te"),
    path("api/lich-su/", api_dieu_phoi.api_lich_su_hoi_thoai, name="api_lich_su_hoi_thoai"),
    path("api/xu-ly-y-dinh/", api_dieu_phoi.api_xu_ly_y_dinh, name="api_xu_ly_y_dinh"),
]