# ============================================================================
# File Path: chat_ui/urls.py
# Module: Dinh Tuyen URL Cua Ung Dung chat_ui
# Linked Files: chat_ui/views.py,
#               config/urls.py
# Purpose: Khai bao route trang chu va API chat.
# ============================================================================

from django.urls import path

from . import views

app_name = "chat_ui"

urlpatterns = [
    path("", views.trang_chu, name="trang_chu"),
    path("api/chat/", views.api_chat, name="api_chat"),
]