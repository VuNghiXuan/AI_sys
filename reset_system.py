"""
# File Path: reset_system.py
# Purpose: Script tự động hóa hoàn toàn việc dọn dẹp DB, xóa migrations cũ, 
#          tạo migrations mới và migrate lại database cho Django.
"""

import os
import shutil
import subprocess
import sys

def run_command(command):
    """Thực thi lệnh shell và in log."""
    print(f"[EXEC] Đang chạy: {' '.join(command)}")
    result = subprocess.run(command, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    if result.returncode != 0:
        print(f"[ERROR] Lệnh thất bại với mã lỗi {result.returncode}")
        sys.exit(result.returncode)

def reset_database_and_migrations():
    print("==================================================")
    print("🚀 BẮT ĐẦU QUÁ TRÌNH RESET HỆ THỐNG VNXBOX")
    print("==================================================")

    # 1. Xóa file cơ sở dữ liệu db.sqlite3 nếu có
    db_file = "db.sqlite3"
    if os.path.exists(db_file):
        os.remove(db_file)
        print(f"🗑️ Đã xóa cơ sở dữ liệu cũ: {db_file}")
    else:
        print("ℹ️ Không tìm thấy file db.sqlite3 cũ.")

    # 2. Xóa các file migration cũ trong hub_core/migrations/ (giữ lại __init__.py)
    migrations_dir = os.path.join("hub_core", "migrations")
    if os.path.exists(migrations_dir):
        print(f"🧹 Đang dọn dẹp thư mục migration: {migrations_dir}")
        for filename in os.listdir(migrations_dir):
            file_path = os.path.join(migrations_dir, filename)
            if filename != "__init__.py" and os.path.isfile(file_path):
                os.remove(file_path)
                print(f"   - Đã xóa migration cũ: {filename}")
            elif filename != "__init__.py" and os.path.isdir(file_path):
                shutil.rmtree(file_path)
                print(f"   - Đã xóa thư mục con: {filename}")
    else:
        print("ℹ️ Thư mục hub_core/migrations không tồn tại.")

    print("--------------------------------------------------")

    # 3. Chạy makemigrations cho hub_core
    print("📦 Đang tạo các file migration mới...")
    run_command([sys.executable, "manage.py", "makemigrations", "hub_core"])

    # 4. Chạy migrate để tạo database mới
    print("🏗️ Đang áp dụng migration vào Database (Migrate)...")
    run_command([sys.executable, "manage.py", "migrate"])

    print("==================================================")
    print("✨ RESET VÀ MIGRATE HỆ THỐNG THÀNH CÔNG RỰC RỠ! ✨")
    print("==================================================")
    print("👉 Bây giờ anh có thể chạy lệnh: python manage.py runserver để khởi động lại server.")

if __name__ == "__main__":
    reset_database_and_migrations()