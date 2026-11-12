# File: enterprise_factory/services/system_bootstrap.py
import os
import sys
import logging
from django.conf import settings
from django.db import connection, transaction

logger = logging.getLogger(__name__)


class SystemBootstrapEngine:

    @classmethod
    def run_full_bootstrap(cls):
        logger.info("⚡ [BOOTSTRAP PIPELINE] >>> BẮT ĐẦU CHUỖI TỰ TRỊ VNXBOX ENTERPRISE <<<")
        try:
            cls._print_diagnostic_map()
            cls._ensure_directories()
            cls._scan_ast_and_router()
            cls._auto_seed_genesis_agents()
            logger.info("🚀 [BOOTSTRAP PIPELINE] >>> HOÀN TẤT TOÀN BỘ CHUỖI KHỞI ĐỘNG <<<")
        except Exception as e:
            logger.error(f"❌ [BOOTSTRAP ERROR] {e}", exc_info=True)

    @staticmethod
    def _print_diagnostic_map():
        logger.info("📊 [Step 1/3] Đang in Bản đồ Trạng thái Hệ thống...")
        db_settings = settings.DATABASES.get('default', {})
        logger.info(f"   - Database Engine: {db_settings.get('ENGINE')}")
        logger.info(f"   - Database Name: {db_settings.get('NAME')}")
        logger.info(f"   - Installed Apps Check: {'enterprise_factory' in settings.INSTALLED_APPS}")

    @staticmethod
    def _ensure_directories():
        os.makedirs("logs", exist_ok=True)
        os.makedirs("dynamic_app", exist_ok=True)
        logger.info("✔️ [Step 2/3] Kiểm tra thư mục hệ thống: OK.")

    @staticmethod
    def _scan_ast_and_router():
        logger.info("🔄 [Step 2.5] Quét AST Blueprint & Warm-up Intent Router...")
        try:
            from enterprise_factory.ast_scanner import ASTCodeScanner
            ASTCodeScanner(project_root=".").scan_project()
            
            from enterprise_factory.intent_router import IntentRouter
            IntentRouter.route("chào hệ thống vnxBox")
            logger.info("✔️ [Step 2.5] AST & Intent Router đã sẵn sàng.")
        except Exception as e:
            logger.error(f"⚠️ Lỗi quét AST/Router: {e}", exc_info=True)

    @staticmethod
    def _auto_seed_genesis_agents():
        logger.info("🔄 [Step 3/3] Tiến hành Khởi sinh Nhân sự Genesis và Cấu hình Tenant vào DB...")
        try:
            from enterprise_factory.models import Company, AgentRole, AgentRegistry, SystemConfig # type: ignore
            
            company, created = Company.objects.get_or_create(
                code="GLOBAL",
                defaults={"name": "vnxBox Global Enterprise"}
            )
            logger.info(f"✔️ [Auto-Genesis] Company GLOBAL (Created: {created})")

            # 🏢 [BỔ SUNG] Seed cấu hình Chủ sở hữu hệ thống (Tenant Owner / Sếp tổng)
            # Giúp sau này bán app cho khách hàng khác chỉ cần đổi config này là xong, không hardcode.
            owner_config, owner_created = SystemConfig.objects.get_or_create(
                key="TENANT_OWNER_NAME",
                defaults={
                    "value": "Sếp Vũ",
                    "description": "Tên định danh Supreme Commander / Chủ sở hữu hệ thống hiện tại"
                }
            )
            logger.info(f"👑 [Auto-Genesis] Tenant Owner được thiết lập: {owner_config.value}")

            initial_roles = [
                ('BOD', 'Ban Giám Đốc / Điều hành Cấp cao', 'Chịu trách nhiệm tổng tài, điều phối chiến lược và phân rã task.'),
                ('HR', 'Giám Đốc Nhân Sự & Tuyển Dụng AI', 'Lắng nghe nhu cầu thiếu hụt kỹ năng để tự động sinh nhân sự mới.'),
                ('BA', 'Chuyên gia Phân tích Nghiệp vụ', 'Phân tích Spec, thiết kế luồng dữ liệu và nghiệp vụ.'),
                ('ARCHITECT', 'Kiến trúc sư Hệ thống', 'Thiết kế cấu trúc file, mô hình dữ liệu và kiểm soát AST.'),
                ('DEV_BE', 'Lập trình viên Backend', 'Thực thi lập trình Vibercode Python/Django theo chuẩn dưới 300 dòng/file.'),
                ('QA_TESTER', 'Chuyên gia Kiểm định QA/QC', 'Kiểm thử, viết test case và rà soát bug hệ thống.')
            ]

            for code, name, desc in initial_roles:
                AgentRole.objects.get_or_create(role_code=code, defaults={'role_name': name, 'description': desc})

            bod_role = AgentRole.objects.filter(role_code='BOD').first()
            hr_role = AgentRole.objects.filter(role_code='HR').first()

            bod_agent, c_bod = AgentRegistry.objects.get_or_create(
                agent_id="BOD_CEO_01",
                defaults={
                    "display_name": "BOD CEO (Tổng Giám Đốc AI)",
                    "company": company,
                    "role": bod_role,
                    "domain_scope": "GLOBAL_MANAGEMENT",
                    "system_prompt": "Quản lý chung, điều phối chiến lược và phân rã task.",
                    "risk_threshold": "HITL_REQUIRED"
                }
            )
            logger.info(f"🚀 [Auto-Genesis] BOD_CEO_01 (Created: {c_bod})")

            hr_agent, c_hr = AgentRegistry.objects.get_or_create(
                agent_id="HR_MANAGER_01",
                defaults={
                    "display_name": "HR Director (Giám Đốc Nhân Sự AI)",
                    "company": company,
                    "role": hr_role,
                    "domain_scope": "RECRUITMENT_SPAWNER",
                    "system_prompt": "Quản lý nhân sự, tuyển dụng và spawn agent chuyên gia.",
                    "risk_threshold": "AUTO_APPLY"
                }
            )
            logger.info(f"🚀 [Auto-Genesis] HR_MANAGER_01 (Created: {c_hr})")
            logger.info(f"🎯 [Genesis Summary] Tổng số agent trong DB: {AgentRegistry.objects.count()}")

        except Exception as e:
            logger.error(f"❌ [Auto-Genesis ERROR] {e}", exc_info=True)