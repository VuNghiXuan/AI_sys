# File: enterprise_factory/management/commands/seed_enterprise.py
from django.core.management.base import BaseCommand
from enterprise_factory.models import Company, AgentRegistry

class Command(BaseCommand):
    help = 'Khởi tạo dữ liệu mẫu (Seed Data) cho Tập đoàn vnxBox'

    def handle(self, *args, **kwargs):
        self.stdout.write("🏛️ Đang khởi tạo cơ cấu tập đoàn vnxBox...")

        # 1. Tạo Khối Tập đoàn & Các công ty con
        global_corp, _ = Company.objects.get_or_create(
            code='GLOBAL',
            defaults={
                'name': 'vnxBox Holding Corporation', 
                'domain': 'Tập đoàn đa ngành & Nền tảng AI', 
                'description': 'Ban điều hành trung tâm'
            }
        )
        
        gold_corp, _ = Company.objects.get_or_create(
            code='GOLD_CORP',
            defaults={
                'name': 'vnxBox Gold & Jewelry ERP', 
                'domain': 'Vàng bạc đá quý', 
                'description': 'Hệ thống quản lý kho vàng, tuổi vàng, hóa đơn.'
            }
        )

        build_corp, _ = Company.objects.get_or_create(
            code='BUILD_CORP',
            defaults={
                'name': 'vnxBox Construction & Project', 
                'domain': 'Xây dựng & Định mức', 
                'description': 'Phần mềm quản lý định mức vật tư, bóc tách khối lượng.'
            }
        )

        # 2. Khởi tạo Ban điều hành & Nhân sự cốt lõi trực thuộc Tập đoàn
        agents_data = [
            {
                'agent_id': 'BOD_CEO_01',
                'display_name': 'Trần Gia Hân (BOD CEO)',
                'company': global_corp,
                'role_type': 'BOD',
                'role_desc': 'Chủ tọa phòng họp chiến lược, phân tích ý định (Intent Router) và điều phối DAG task.',
                'system_prompt': 'Bạn là CEO điều hành tập đoàn vnxBox. Sắc sảo, thực tế, quyết đoán, luôn hướng tới hiệu quả tối ưu Local-First.'
            },
            {
                'agent_id': 'ARCHITECT_CHIEF',
                'display_name': 'Nguyễn Minh Quân (Chief Architect)',
                'company': global_corp,
                'role_type': 'ARCHITECT',
                'role_desc': 'Kiến trúc sư trưởng, quản lý sơ đồ CSDL, chuẩn hóa Vibercode và phân bổ tài nguyên.',
                'system_prompt': 'Bạn là Kiến trúc sư trưởng. Chuyên gia về Django Monolith, SQLite, tối ưu CPU-only, kiểm soát file dưới 300 dòng.'
            },
            {
                'agent_id': 'HR_SPAWNER_01',
                'display_name': 'Lê Hoàng Nam (HR Spawner)',
                'company': global_corp,
                'role_type': 'BA',
                'role_desc': 'Trưởng phòng Nhân sự AI, chịu trách nhiệm tự sinh chuyên gia mới khi phát sinh bài toán ngành.',
                'system_prompt': 'Bạn là Trưởng phòng Nhân sự AI. Phân tích yêu cầu bài toán để khởi tạo đúng chuyên gia chuyên ngành.'
            },
            {
                'agent_id': 'BA_GOLD_01',
                'display_name': 'Phạm Thu Thảo (Gold BA Specialist)',
                'company': gold_corp,
                'role_type': 'BA',
                'role_desc': 'Chuyên gia phân tích nghiệp vụ Vàng bạc (Tuổi vàng 9999, 18K, chỉ/gram/li).',
                'system_prompt': 'Bạn là BA chuyên ngành Vàng bạc đá quý. Bóc tách chi tiết luồng nghiệp vụ kho vàng, hóa đơn, hao hụt.'
            },
            {
                'agent_id': 'DEV_BE_01',
                'display_name': 'Vũ Đức Mạnh (Senior Backend Dev)',
                'company': global_corp,
                'role_type': 'DEV_BE',
                'role_desc': 'Chuyên gia lập trình Backend Django, DRF, Secure Sandbox, WebSocket.',
                'system_prompt': 'Bạn là Backend Dev cao cấp. Viết code chuẩn chỉnh, sạch sẽ, mỗi file dưới 300 dòng, tích hợp Secure Sandbox cho tính toán tài chính.'
            },
            {
                'agent_id': 'QA_TESTER_01',
                'display_name': 'Hoàng Mai Chi (QA & Tester Lead)',
                'company': global_corp,
                'role_type': 'QA',
                'role_desc': 'Chuyên gia kiểm thử, viết Testcase boundary value và kiểm tra lỗi logic.',
                'system_prompt': 'Bạn là QA Lead. Bắt buộc lập bộ testcase đầy đủ các trường hợp biên, kiểm tra mã nguồn trước khi release.'
            }
        ]

        for data in agents_data:
            AgentRegistry.objects.update_or_create(
                agent_id=data['agent_id'],
                defaults=data
            )

        self.stdout.write(self.style.SUCCESS("✅ Đã seed thành công cấu trúc Tập đoàn và Nhân sự AI cốt lõi!"))