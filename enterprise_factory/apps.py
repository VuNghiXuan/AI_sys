# File: enterprise_factory/apps.py
from django.apps import AppConfig

class EnterpriseFactoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'enterprise_factory'

    def ready(self):
        # Không cần làm gì ở đây nữa vì asgi.py hoặc management command đã lo trọn gói,
        # giúp tránh hoàn toàn lỗi re-entrant populate().
        pass