# File: enterprise_factory/management/commands/scan_project.py
import os
from django.core.management.base import BaseCommand
from enterprise_factory.utils.ast_scanner import scan_and_register_file
from enterprise_factory.models import Company

class Command(BaseCommand):
    help = 'Quét toàn bộ mã nguồn Python trong dự án để cập nhật vào ProjectNode'

    def handle(self, *args, **kwargs):
        self.stdout.write("🔍 Đang quét toàn bộ cấu trúc mã nguồn dự án qua AST...")
        
        global_corp = Company.objects.filter(code='GLOBAL').first()
        scanned_count = 0

        # Quét thư mục gốc hiện tại (nơi có manage.py)
        root_dir = os.getcwd()
        for dirpath, _, filenames in os.walk(root_dir):
            # Bỏ qua các thư mục ảo (env, venv, __pycache__, .git, staticfiles)
            if any(exc in dirpath for exc in ['env', 'venv', '__pycache__', '.git', 'staticfiles']):
                continue
            
            for filename in filenames:
                if filename.endswith('.py'):
                    full_path = os.path.join(dirpath, filename)
                    scan_and_register_file(full_path, company=global_corp, agent_id='ARCHITECT_CHIEF')
                    scanned_count += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Đã quét và cập nhật thành công {scanned_count} file Python vào ProjectMap!"))