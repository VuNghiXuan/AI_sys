# File: vnxbox_core/asgi.py
import os
import logging
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vnxbox_core.settings')

# Kích hoạt logging ngay khi ASGI khởi động để ép tạo file log lập tức
logger = logging.getLogger('enterprise_factory')
logger.info("[*] [ASGI] Daphne ASGI Server đang khởi động vnxBox Enterprise...")

django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import enterprise_factory.routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            enterprise_factory.routing.websocket_urlpatterns
        )
    ),
})