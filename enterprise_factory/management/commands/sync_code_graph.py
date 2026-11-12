# File: enterprise_factory/management/commands/sync_code_graph.py
import logging
from django.core.management.base import BaseCommand
from enterprise_factory.ast_scanner import ASTCodeScanner

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Quét toàn bộ cấu trúc mã nguồn qua AST và đồng bộ vào Bản đồ Tri thức hệ thống."

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Bắt đầu quét codebase qua AST Scanner..."))
        logger.info("Khởi chạy lệnh sync_code_graph.")
        
        scanner = ASTCodeScanner(project_root=".")
        codebase_map = scanner.scan_project()
        
        # Thống kê kết quả quét
        total_files = len(codebase_map)
        total_classes = sum(len(item["classes"]) for item in codebase_map)
        
        self.stdout.write(self.style.SUCCESS(
            f"Đồng bộ hoàn tất! Đã quét {total_files} file, nhận diện {total_classes} Class/Model."
        ))
        logger.info(f"sync_code_graph hoàn tất: {total_files} files, {total_classes} classes.")