"""
# File Path: vnx_hub/urls.py
# Purpose: Định tuyến URL tổng thể của dự án vnx_hub.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('hub_core.urls')),
]