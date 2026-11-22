# ==============================================================================
# File Path: he_thong/urls.py
# Description: Root URL configuration for he_thong project.
# Linked Files: [quan_ly_du_an/giao_dien/urls_giao_dien.py]
# Logs: Register admin route and mount quan_ly_du_an UI routes.
# ==============================================================================

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("giao-dien/", include("quan_ly_du_an.giao_dien.urls_giao_dien")),
    path("", include("quan_ly_du_an.giao_dien.urls_giao_dien")),
    
]