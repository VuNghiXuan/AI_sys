# File: enterprise_factory/routing.py
"""
Định tuyến URL WebSocket (ASGI Routing) cho vnxBox Enterprise.
"""

from django.urls import re_path
from enterprise_factory import consumers

websocket_urlpatterns = [
    # Đường dẫn kết nối WebSocket tới Live War Room
    re_path(r'ws/war-room/$', consumers.WarRoomConsumer.as_asgi()),
]