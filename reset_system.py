# File: reset_system.py
import os
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
APP_NAME = 'enterprise_factory'
DB_PATH = BASE_DIR / 'db.sqlite3'

def clean_migrations():
    migrations_dir = BASE_DIR / APP_NAME / 'migrations'
    if not migrations_dir.exists():
        print(f"[!] Không tìm thấy thư mục migrations tại: {migrations_dir}")
        return

    print(f"[*] Đang dọn dẹp các file migration cũ trong '{APP_NAME}'...")
    count = 0
    for file_path in migrations_dir.iterdir():
        # Giữ lại file __init__.py, chỉ xóa các file py/pyc sinh ra từ migration
        if file_path.is_file() and file_path.name != '__init__.py':
            file_path.unlink()
            print(f"    [-] Đã xóa: {file_path.name}")
            count += 1
    print(f"[+] Đã dọn xong {count} file migration cũ.")

def clean_database():
    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"[+] Đã xóa sạch database cũ: {DB_PATH.name}")
    else:
        print(f"[!] Không tìm thấy file database cũ (db.sqlite3).")

if __name__ == '__main__':
    print("=== BẮT ĐẦU QUÁ TRÌNH RESET HỆ THỐNG VNXBOX ===")
    clean_database()
    clean_migrations()
    print("=== HOÀN TẤT LÀM SẠCH! ===")
    print("Bây giờ Sếp có thể chạy lại lệnh: python manage.py makemigrations và python manage.py migrate")