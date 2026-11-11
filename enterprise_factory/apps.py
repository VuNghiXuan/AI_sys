# File: enterprise_factory/apps.py
"""
AppConfig tự động khởi tạo hạt giống Genesis (Self-Bootstrapping) cho vnxBox Enterprise.
Tự động khai sinh 2 cán bộ chủ chốt (BOD CEO & HR Director) và danh mục vai trò động.
"""

import sys
from django.apps import AppConfig


class EnterpriseFactoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'enterprise_factory'

    def ready(self):
        """Tự động kiểm tra và khởi tạo hệ thống khi Django khởi động (Lazy Bootstrapping)"""
        # Tránh xung đột khi đang chạy lệnh migration hoặc unit test
        if any(cmd in sys.argv for cmd in ['makemigrations', 'migrate', 'test', 'collectstatic']):
            return

        try:
            from enterprise_factory.models import Company, AgentRole, AgentRegistry
            
            # 1. Khởi tạo danh mục vai trò động (Dynamic Role Catalog)
            initial_roles = [
                ('BOD', 'Ban Giám Đốc / Điều hành Cấp cao', 'Chịu trách nhiệm tổng tài, điều phối chiến lược và phân rã task.'),
                ('HR', 'Giám Đốc Nhân Sự & Tuyển Dụng AI', 'Lắng nghe nhu cầu thiếu hụt kỹ năng để tự động sinh nhân sự mới.'),
                ('BA', 'Chuyên gia Phân tích Nghiệp vụ', 'Phân tích Spec, thiết kế luồng dữ liệu và nghiệp vụ.'),
                ('ARCHITECT', 'Kiến trúc sư Hệ thống', 'Thiết kế cấu trúc file, mô hình dữ liệu và kiểm soát AST.'),
                ('DEV_BE', 'Lập trình viên Backend', 'Thực thi lập trình Vibercode Python/Django theo chuẩn dưới 300 dòng/file.'),
                ('QA_TESTER', 'Chuyên gia Kiểm định QA/QC', 'Kiểm thử, viết test case và rà soát bug hệ thống.')
            ]

            for code, name, desc in initial_roles:
                AgentRole.objects.get_or_create(
                    role_code=code,
                    defaults={'role_name': name, 'description': desc}
                )

            # 2. Kiểm tra xem đã có hạt giống BOD khởi thủy hay chưa
            if not AgentRegistry.objects.filter(agent_id='BOD_CEO_01').exists():
                print("🌱 [Auto-Genesis] Phát hiện hệ thống trắng, đang tự động khai sinh Ban Giám Đốc và HR...")
                
                company, _ = Company.objects.get_or_create(
                    code="GLOBAL",
                    defaults={"name": "vnxBox Global Enterprise"}
                )

                bod_role = AgentRole.objects.filter(role_code='BOD').first()
                hr_role = AgentRole.objects.filter(role_code='HR').first()

                # Lấy hoặc tạo Tổng Giám Đốc AI (BOD)
                AgentRegistry.objects.get_or_create(
                    agent_id="BOD_CEO_01",
                    defaults={
                        "display_name": "BOD CEO (Tổng Giám Đốc AI)",
                        "company": company,
                        "role": bod_role,
                        "domain_scope": "GLOBAL_MANAGEMENT",
                        "system_prompt": (
                            "Bạn là Giám đốc Điều hành Tổng tài (BOD CEO) của vnxBox Enterprise.\n"
                            "Nhiệm vụ: Tiếp nhận chỉ đạo chiến lược từ Sếp Vũ, phân tích cấu trúc công việc, "
                            "kiểm tra năng lực hệ thống hiện tại. Nếu thiếu hụt nhân sự chuyên môn, hãy ra lệnh "
                            "cho HR Director tuyển dụng nhân sự mới. Điều phối các phòng ban thực thi không có độ trễ."
                        ),
                        "risk_threshold": "HITL_REQUIRED"
                    }
                )

                # Lấy hoặc tạo Giám Đốc Nhân Sự AI (HR Director)
                AgentRegistry.objects.get_or_create(
                    agent_id="HR_MANAGER_01",
                    defaults={
                        "display_name": "HR Director (Giám Đốc Nhân Sự AI)",
                        "company": company,
                        "role": hr_role,
                        "domain_scope": "RECRUITMENT_SPAWNER",
                        "system_prompt": (
                            "Bạn là Giám đốc Nhân sự (HR Director) của vnxBox Enterprise.\n"
                            "Nhiệm vụ: Lắng nghe yêu cầu từ BOD khi hệ thống thiếu chuyên gia trong lĩnh vực mới, "
                            "tự động thiết kế hồ sơ, system prompt và sinh ra chuyên gia AI mới (AgentRegistry) "
                            "với mã định danh và domain scope chuẩn xác."
                        ),
                        "risk_threshold": "AUTO_APPLY"
                    }
                )
                print("🚀 [Auto-Genesis] Khởi tạo thành công BOD_CEO_01 và HR_MANAGER_01!")

        except Exception as e:
            # Bỏ qua lỗi nhẹ trong lúc khởi tạo bảng chưa đồng bộ migration đầu tiên
            print("⚠️ [Auto-Genesis Warning]:", e)
            pass