# ============================================================================
# File Path: dieu_phoi_y_dinh/apps.py
# Module: Cau Hinh App Django
# Linked Files: __init__.py, urls.py, views.py
# Purpose: Khai bao cau hinh Django cho app dieu_phoi_y_dinh.
# ============================================================================

from django.apps import AppConfig


class DieuPhoiYDinhConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "dieu_phoi_y_dinh"
    verbose_name = "Điều phối Ý định Đa tầng & Bộ não"