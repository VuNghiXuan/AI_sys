# File: enterprise_factory/management/commands/test_directive.py
from django.core.management.base import BaseCommand
from enterprise_factory.models import Company, DirectiveLog, AgentTaskDAG, AgentRegistry

class Command(BaseCommand):
    help = 'Mô phỏng Sếp ra chỉ đạo và kiểm tra hệ thống phân rã Task'

    def handle(self, *args, **kwargs):
        self.stdout.write("🎯 Bắt đầu test thực tế quy trình chỉ đạo của Sếp...")

        # 1. Lấy công ty Vàng bạc và CEO
        gold_corp = Company.objects.filter(code='GOLD_CORP').first()
        ceo = AgentRegistry.objects.filter(agent_id='BOD_CEO_01').first()
        ba_gold = AgentRegistry.objects.filter(agent_id='BA_GOLD_01').first()
        dev_be = AgentRegistry.objects.filter(agent_id='DEV_BE_01').first()

        if not gold_corp or not ceo:
            self.stdout.write(self.style.ERROR("❌ Chưa chạy lệnh seed_enterprise! Hãy chạy seed trước."))
            return

        # 2. Sếp ra chỉ đạo mới
        directive_text = "Xây dựng module quản lý hóa đơn mua bán vàng 9999 và tính toán tuổi vàng tự động qua Secure Sandbox."
        
        directive = DirectiveLog.objects.create(
            company=gold_corp,
            directive_text=directive_text,
            target_folder='gold_erp_app',
            status='PROCESSING'
        )
        self.stdout.write(f"📝 Đã ghi nhận chỉ đạo: {directive.directive_text}")

        # 3. BOD (CEO) phân rã công việc thành DAG Tasks giao cho nhân viên
        task_1 = AgentTaskDAG.objects.create(
            task_id='TASK_GOLD_01',
            company=gold_corp,
            directive=directive,
            title='Phân tích luồng nghiệp vụ hóa đơn vàng & tính toán tuổi vàng',
            assigned_agent=ba_gold,
            status='SUCCESS',
            result_output='Đã hoàn thành phân tích: Hóa đơn gồm trọng lượng chỉ/gram, đơn giá, tiền công và hàm quy đổi tuổi vàng chuẩn xác.'
        )

        task_2 = AgentTaskDAG.objects.create(
            task_id='TASK_GOLD_02',
            company=gold_corp,
            directive=directive,
            title='Viết Model & API Django cho hóa đơn vàng (Tích hợp Secure Sandbox)',
            assigned_agent=dev_be,
            status='PENDING',
            dependencies=['TASK_GOLD_01']
        )

        self.stdout.write(self.style.SUCCESS(f"✅ Đã phân rã thành công 2 DAG Tasks cho nhân sự AI!"))
        self.stdout.write(f"   - Task 1: {task_1.title} -> Giao cho: {task_1.assigned_agent.display_name} [Trạng thái: {task_1.status}]")
        self.stdout.write(f"   - Task 2: {task_2.title} -> Giao cho: {task_2.assigned_agent.display_name} [Trạng thái: {task_2.status}]")