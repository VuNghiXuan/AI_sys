# File: vnxbox_core/asgi.py
import os
import django
from django.core.asgi import get_asgi_application

# 1. Khởi tạo môi trường Django một lần duy nhất
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vnxbox_core.settings')
django.setup()

# 2. Sau khi Django đã setup xong, gọi SystemBootstrapEngine hoàn toàn an toàn
try:
    print("⚡ [ASGI BOOTSTRAP] Đang kích hoạt SystemBootstrapEngine...")
    from enterprise_factory.services.system_bootstrap import SystemBootstrapEngine
    SystemBootstrapEngine.run_full_bootstrap()
    print("✔️ [ASGI BOOTSTRAP] Hoàn tất khởi động tự trị và seed Genesis!")
except Exception as e:
    print(f"❌ [ASGI BOOTSTRAP ERROR]: {e}")

# 3. Cấu hình Channels Routing
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import enterprise_factory.routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            enterprise_factory.routing.websocket_urlpatterns
        )
    ),
})