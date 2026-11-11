# File: vnxbox_core/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Bao gồm toàn bộ routing của enterprise_factory
    path('', include('enterprise_factory.urls')),
]

# Thêm cấu hình phục vụ static/media files khi đang chạy DEBUG = True trên ASGI/Daphne
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # Hoặc nếu Sếp để file trong app static:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])