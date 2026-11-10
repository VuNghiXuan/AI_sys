# File: enterprise_factory/apps.py
from django.apps import AppConfig
from django.db.utils import OperationalError, ProgrammingError

class EnterpriseFactoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'enterprise_factory'

    def ready(self):
        """
        Hệ thống tự động kiểm tra điều kiện vận hành và seed dữ liệu ngầm 
        mỗi khi ứng dụng khởi động (App Readiness Check).
        """
        # Tránh thực thi khi chạy các lệnh quản trị như makemigrations, collectstatic,...
        import sys
        if any(cmd in sys.argv for cmd in ['makemigrations', 'migrate', 'collectstatic', 'shell']):
            return

        try:
            from enterprise_factory.models import Company, AgentRegistry, AgentDiscussion

            # 1. Kiểm tra và tự động tạo Company mặc định nếu chưa có
            company, created = Company.objects.get_or_create(
                code='GLOBAL', 
                defaults={'name': 'vnxBox Enterprise Holding'}
            )

            # 2. Kiểm tra và tự động khởi tạo 2 nhân sự cốt lõi: BOD_CEO_01 & DEV_BE_01
            bod, _ = AgentRegistry.objects.update_or_create(
                agent_id='BOD_CEO_01',
                defaults={
                    'display_name': 'BOD CEO (Tổng Giám Đốc)',
                    'company': company,
                    'role_type': 'BOD',
                    'system_prompt': 'You are the BOD CEO of vnxBox Enterprise, handling communications, greetings, and strategic direction professionally.',
                    'version': '1.0.0'
                }
            )

            dev, _ = AgentRegistry.objects.update_or_create(
                agent_id='DEV_BE_01',
                defaults={
                    'display_name': 'Dev Backend (Chuyên gia Vibercode)',
                    'company': company,
                    'role_type': 'DEV_BE',
                    'system_prompt': 'You are an expert Python Backend Developer specializing in Django, AST validation, and clean modular code under 300 lines.',
                    'version': '1.0.0'
                }
            )

            # 3. Kiểm tra phòng họp Viber Room, tạo tin nhắn chào mừng nếu trống
            if not AgentDiscussion.objects.exists():
                AgentDiscussion.objects.create(
                    company=company,
                    agent=bod,
                    phase='SMALL_TALK',
                    message_content='Chào Sếp! Hội đồng AGI đã tự động điểm danh và sẵn sàng tại Live War Room. Sếp cần em hỗ trợ công việc gì hôm nay ạ?'
                )
                
        except (OperationalError, ProgrammingError):
            # Bỏ qua an toàn nếu bảng cơ sở dữ liệu chưa được tạo (chưa chạy migrate lần đầu)
            pass