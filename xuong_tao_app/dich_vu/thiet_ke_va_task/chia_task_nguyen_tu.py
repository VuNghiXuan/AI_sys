# ============================================================================
# File Path: xuong_tao_app/dich_vu/thiet_ke_va_task/chia_task_nguyen_tu.py
# Module: Chia Danh Sach Task Nguyen Tu Tu Ban Thiet Ke
# Linked Files: tom_tat_va_thiet_ke.py, ../sinh_ma_sandbox/
# Purpose: Chuyen ban thiet ke app va cac chuc nang con thanh cac task nho
#          theo thu tu phu thuoc, bam quy chuan < 300 dong/file va logging.
# ============================================================================

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

GIOI_HAN_DONG_MOI_FILE = 300


def _chuan_hoa_ma_dinh_danh(ten: str) -> str:
    """Chuan hoa ten thanh ma snake_case an toan cho ten folder/file/tab."""
    khong_dau = (ten or "").strip().lower()
    ma = re.sub(r"[^a-z0-9_]+", "_", khong_dau).strip("_")
    return ma or "app_nghiep_vu"


def chia_task_tu_thiet_ke(ban_thiet_ke: dict[str, Any]) -> list[dict[str, Any]]:
    """Chia ban thiet ke thanh cac task nguyen tu theo thu tu thuc thi.

    Moi task gan voi mot muc tieu file/module cu thể de tranh phinh code.
    """
    ma_app = _chuan_hoa_ma_dinh_danh(str(ban_thiet_ke.get("ten_app_goi_y") or "app_nghiep_vu"))
    tieu_de_tab = str(ban_thiet_ke.get("tieu_de_tab") or ma_app).strip()
    chuc_nang_con = ban_thiet_ke.get("chuc_nang_con") or []

    danh_sach_task: list[dict[str, Any]] = []
    thu_tu = 1

    # Task 1: Tang du lieu & cau hinh cho moi truong test rieng
    danh_sach_task.append({
        "ma_task": f"TASK_{thu_tu:02d}",
        "thu_tu": thu_tu,
        "nhom": "du_lieu_va_kho",
        "tieu_de": f"Khởi tạo kho dữ liệu & cấu hình test riêng cho '{tieu_de_tab}'",
        "file_muc_tieu": f"sandbox_apps/{ma_app}/kho_du_lieu.py",
        "gioi_han_dong": GIOI_HAN_DONG_MOI_FILE,
        "phu_thuoc": [],
        "trang_thai": "cho_thuc_thi",
    })
    ma_task_kho = f"TASK_{thu_tu:02d}"
    thu_tu += 1

    # Task cho tung chuc nang con: tach nghiep vu rieng theo tung file
    ma_cac_task_nghiep_vu: list[str] = []
    for cn in chuc_nang_con:
        if not isinstance(cn, dict):
            continue
        ma_cn = _chuan_hoa_ma_dinh_danh(str(cn.get("ma") or cn.get("ten") or f"chuc_nang_{thu_tu}"))
        ten_cn = str(cn.get("ten") or ma_cn).strip()
        mo_ta_cn = str(cn.get("mo_ta") or "").strip()

        ma_hien_tai = f"TASK_{thu_tu:02d}"
        danh_sach_task.append({
            "ma_task": ma_hien_tai,
            "thu_tu": thu_tu,
            "nhom": "nghiep_vu_chuc_nang_con",
            "ma_chuc_nang_con": ma_cn,
            "ten_chuc_nang_con": ten_cn,
            "mo_ta": mo_ta_cn,
            "tieu_de": f"Xử lý nghiệp vụ chức năng con: {ten_cn}",
            "file_muc_tieu": f"sandbox_apps/{ma_app}/dich_vu/{ma_cn}.py",
            "gioi_han_dong": GIOI_HAN_DONG_MOI_FILE,
            "phu_thuoc": [ma_task_kho],
            "trang_thai": "cho_thuc_thi",
        })
        ma_cac_task_nghiep_vu.append(ma_hien_tai)
        thu_tu += 1

    # Task giao dien test tren moi truong rieng (gom cac chuc nang con tren tab)
    danh_sach_task.append({
        "ma_task": f"TASK_{thu_tu:02d}",
        "thu_tu": thu_tu,
        "nhom": "giao_dien_test_rieng",
        "tieu_de": f"Dựng giao diện test thực tế cho tab '{tieu_de_tab}' và các chức năng con",
        "file_muc_tieu": f"sandbox_apps/{ma_app}/giao_dien/trang_test_{ma_app}.html",
        "gioi_han_dong": GIOI_HAN_DONG_MOI_FILE,
        "phu_thuoc": ma_cac_task_nghiep_vu or [ma_task_kho],
        "trang_thai": "cho_thuc_thi",
    })
    ma_task_gd = f"TASK_{thu_tu:02d}"
    thu_tu += 1

    # Task kiem tra cu phap & chuan hoa truoc khi test tuong tac
    danh_sach_task.append({
        "ma_task": f"TASK_{thu_tu:02d}",
        "thu_tu": thu_tu,
        "nhom": "kiem_tra_ban_dau",
        "tieu_de": f"Kiểm tra cú pháp, giới hạn <300 dòng và tính sẵn sàng của '{ma_app}'",
        "file_muc_tieu": f"sandbox_apps/{ma_app}/kiem_tra_nhanh.py",
        "gioi_han_dong": GIOI_HAN_DONG_MOI_FILE,
        "phu_thuoc": [ma_task_gd],
        "trang_thai": "cho_thuc_thi",
    })

    logger.info("Da chia %d task nguyen tu cho app '%s'", len(danh_sach_task), ma_app)
    return danh_sach_task