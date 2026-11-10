# File: enterprise_factory/management/commands/seed_db.py
from django.core.management.base import BaseCommand
from enterprise_factory.models import Company, AgentRegistry, AgentDiscussion

class Command(BaseCommand):
    help = 'Khởi tạo dữ liệu mẫu (Seed Data) ban đầu cho vnxBox Enterprise khi cài đặt trên máy mới.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE('Đang khởi tạo dữ liệu mẫu cho hệ thống...'))

        # 1. Tạo Company mặc định
        company, created = Company.objects.get_or_create(
            code='GLOBAL', 
            defaults={'name': 'vnxBox Enterprise Holding'}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Đã tạo mới Company: {company.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'Company {company.code} đã tồn tại.'))

        # 2. Khởi tạo 2 nhân sự cốt lõi: BOD_CEO_01 & DEV_BE_01
        bod, bod_created = AgentRegistry.objects.update_or_create(
            agent_id='BOD_CEO_01',
            defaults={
                'display_name': 'BOD CEO (Tổng Giám Đốc)',
                'company': company,
                'role_type': 'BOD',
                'system_prompt': 'You are the BOD CEO of vnxBox Enterprise, handling communications, greetings, and strategic direction professionally.',
                'version': '1.0.0'
            }
        )
        self.stdout.write(self.style.SUCCESS(f'Đã thiết lập nhân sự: {bod.display_name}'))

        dev, dev_created = AgentRegistry.objects.update_or_create(
            agent_id='DEV_BE_01',
            defaults={
                'display_name': 'Dev Backend (Chuyên gia Vibercode)',
                'company': company,
                'role_type': 'DEV_BE',
                'system_prompt': 'You are an expert Python Backend Developer specializing in Django, AST validation, and clean modular code under 300 lines.',
                'version': '1.0.0'
            }
        )
        self.stdout.write(self.style.SUCCESS(f'Đã thiết lập nhân sự: {dev.display_name}'))

        # 3. Tạo thông điệp chào mừng khởi đầu trong phòng họp nếu chưa có
        if not AgentDiscussion.objects.exists():
            AgentDiscussion.objects.create(
                company=company,
                agent=bod,
                phase='SMALL_TALK',
                message_content='Chào Sếp! Hội đồng AGI đã tề tựu sẵn sàng tại Live War Room (vnxBox Enterprise). Sếp cần em hỗ trợ công việc gì hôm nay ạ?'
            )
            self.stdout.write(self.style.SUCCESS('Đã tạo bản ghi tin nhắn chào mừng trong phòng họp.'))

        self.stdout.write(self.style.SUCCESS('HOÀN TẤT! Dữ liệu mẫu đã được nạp thành công vào hệ thống.'))