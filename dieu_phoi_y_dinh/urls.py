# ============================================================================
# File Path: dieu_phoi_y_dinh/urls.py
# Module: Dinh Tuyen URL App Dieu Phoi Y Dinh
# Linked Files: views.py
# Purpose: Khai bao endpoint API cho app dieu_phoi_y_dinh.
# ============================================================================

from django.urls import path

from .views import api_dieu_phoi_y_dinh

urlpatterns = [
    path("api/dieu-phoi/", api_dieu_phoi_y_dinh, name="api_dieu_phoi_y_dinh"),
]