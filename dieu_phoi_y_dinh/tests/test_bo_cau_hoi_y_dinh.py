# ============================================================================
# File Path: dieu_phoi_y_dinh/tests/test_bo_cau_hoi_y_dinh.py
# Module: Bo Test Dinh Tuyen, Noi Dung Tra Loi Va Toc Do Dieu Phoi
# Linked Files: dieu_phoi_y_dinh/dich_vu/dieu_phoi_nhanh.py,
#               dieu_phoi_y_dinh/dich_vu/bo_nho_va_cache.py,
#               dieu_phoi_y_dinh/cau_hinh_y_dinh.json
# Purpose: Kiem tra y dinh, noi dung phan hoi, mach hoi thoai va toc do
#          xu ly cua bo dieu phoi y dinh.
# ============================================================================

from dataclasses import dataclass
import logging
import os
from pathlib import Path
import sys
import time
from typing import Any

GOC_DU_AN = Path(__file__).resolve().parents[2]
if str(GOC_DU_AN) not in sys.path:
    sys.path.insert(0, str(GOC_DU_AN))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "he_thong.settings")

import django

django.setup()

from dieu_phoi_y_dinh.dich_vu.dieu_phoi_nhanh import xu_ly_prompt_da_y_dinh

logging.basicConfig(level=logging.WARNING, format="%(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CaKiemThu:
    """Dinh nghia mot ca test gom cau hoi, y dinh ky vong va kiem tra noi dung."""

    cau_hoi: str
    y_dinh_ky_vong: str
    bat_buoc_chua: tuple[str, ...] = ()
    cam_chua: tuple[str, ...] = ()


BO_TEST_CHUAN: tuple[CaKiemThu, ...] = (
    # 1. Truy van cau truc app & model DB
    CaKiemThu("kể tên các app và model trong database hiện tại", "liet_ke_app_va_model", ("| App |",)),
    CaKiemThu("danh sách bảng dữ liệu và trường trong db", "liet_ke_app_va_model", ("| App |",)),
    CaKiemThu("cấu trúc model của hệ thống ra sao", "liet_ke_app_va_model", ("| App |",)),
    CaKiemThu("liet ke cac app va truong du lieu", "liet_ke_app_va_model", ("| App |",)),
    # 2. Thong ke du lieu DB
    CaKiemThu("thống kê số lượng bản ghi trong database", "thong_ke_du_lieu_db", ("| App |",)),
    CaKiemThu("bảng nào trong db đang có dữ liệu", "thong_ke_du_lieu_db", ("| App |",)),
    CaKiemThu("đếm số dòng dữ liệu các model", "thong_ke_du_lieu_db", ("| App |",)),
    CaKiemThu("thong ke so ban ghi tung bang", "thong_ke_du_lieu_db", ("| App |",)),
    # 3. Huong dan su dung nhanh
    CaKiemThu("hướng dẫn tao cách sử dụng hệ thống", "huong_dan_su_dung_nhanh", ("Cách dùng nhanh",)),
    CaKiemThu("hệ thống này làm gì và dùng thế nào", "huong_dan_su_dung_nhanh", ("Cách dùng nhanh",)),
    CaKiemThu("luồng hoạt động chính ra sao", "huong_dan_su_dung_nhanh", ("Cách dùng nhanh",)),
    CaKiemThu("huong dan su dung he thong", "huong_dan_su_dung_nhanh", ("Cách dùng nhanh",)),
    # 4. Viet code & phan tich
    CaKiemThu("viết cho tôi một hàm python kiểm tra file json hợp lệ", "viet_code_va_phan_tich"),
    CaKiemThu("sửa lỗi đoạn mã này giúp: def chia(a, b): return a / b khi b=0", "viet_code_va_phan_tich"),
    CaKiemThu("phân tích phương án và chia đầu mục triển khai xuất excel", "viet_code_va_phan_tich"),
    # 5. Tao app chuyen trang
    CaKiemThu("tạo app quản lý chấm công", "tao_app_chuyen_trang"),
    CaKiemThu("lập ứng dụng theo dõi đơn hàng và công nợ", "tao_app_chuyen_trang"),
    CaKiemThu("xây dựng app quản lý kho vật tư", "tao_app_chuyen_trang"),
    CaKiemThu("tao app cham cong nhan vien", "tao_app_chuyen_trang"),
    # 6. Tra cuu mang / thoi su / gia ca
    CaKiemThu("tuy hoà có mưa không", "tra_cuu_mang_va_thoi_su", ("Link tham khảo",)),
    CaKiemThu("thời tiết sài gòn hôm nay thế nào", "tra_cuu_mang_va_thoi_su", ("Link tham khảo",)),
    CaKiemThu("giá vàng hôm nay bao nhiêu", "tra_cuu_mang_va_thoi_su", ("Link tham khảo",)),
    CaKiemThu("tin tức mới nhất hôm nay", "tra_cuu_mang_va_thoi_su", ("Link tham khảo",)),
    # 7. Chat tu do & telemetry
    CaKiemThu("alo", "chat_tu_do"),
    CaKiemThu("chào buổi sáng nhé", "chat_tu_do"),
    CaKiemThu("ok cảm ơn nhiều", "chat_tu_do"),
    CaKiemThu("nhắc tên tao", "chat_tu_do", cam_chua=("trợ lý AI của",)),
    CaKiemThu("máy đang chạy model nào và cấu hình phần cứng ra sao", "tra_cuu_telemetry_va_model", ("CPU", "RAM")),
    CaKiemThu("cau hinh may va model ollama dang chay", "tra_cuu_telemetry_va_model", ("CPU", "RAM")),
)

BO_TEST_BAY_RANH_GIOI: tuple[CaKiemThu, ...] = (
    CaKiemThu("hôm nay hơi mệt xíu", "chat_tu_do"),
    CaKiemThu("tao muốn tạo một cái note để nhớ việc", "chat_tu_do"),
    CaKiemThu("viết code tạo app chấm công bằng django", "viet_code_va_phan_tich"),
    CaKiemThu("viet ham loc so chan trong list", "viet_code_va_phan_tich"),
    CaKiemThu("chức năng từng app", "liet_ke_app_va_model", cam_chua=("Xưởng Tạo App",)),
    CaKiemThu("hệ thống có file gì", "hoi_dap_he_thong_chi_tiet", cam_chua=("Cách dùng nhanh",)),
)

CHUOI_HOI_THOAI_LIEN_TUC: tuple[CaKiemThu, ...] = (
    CaKiemThu("tên tao là Vũ", "chat_tu_do", ("Vũ",)),
    CaKiemThu("máy đang chạy model nào và cấu hình phần cứng ra sao", "tra_cuu_telemetry_va_model", ("RAM",)),
    CaKiemThu("nhức lại tên tao", "chat_tu_do", ("Vũ",), ("trợ lý AI của", "tao tên vũ")),
    CaKiemThu("ừ", "chat_tu_do", cam_chua=("Cách dùng nhanh",)),
)


def _kiem_tra_noi_dung(ca: CaKiemThu, kq: dict[str, Any]) -> tuple[bool, str]:
    """Kiem tra noi dung phan hoi hop le, khong rong va khong dinh chuoi cam."""
    noi_dung = str(kq.get("tom_tat") or "").strip()
    if not noi_dung:
        return False, "tom_tat rong"

    noi_dung_thuong = noi_dung.lower()
    for cum in ca.bat_buoc_chua:
        if cum.lower() not in noi_dung_thuong:
            return False, f"thieu '{cum}'"

    for cum_cam in ca.cam_chua:
        if cum_cam.lower() in noi_dung_thuong:
            return False, f"dinh chuoi cam '{cum_cam}'"

    return True, "ok"


def _chay_mot_ca(ca: CaKiemThu, phien: dict[str, str] | None = None) -> tuple[bool, float, str]:
    """Thuc thi mot ca test, do thoi gian va in tóm tắt kq + tra loi."""
    t0 = time.perf_counter()
    kq = xu_ly_prompt_da_y_dinh(ca.cau_hoi, session=phien)
    thoi_gian = time.perf_counter() - t0

    thuc_te = str(kq.get("y_dinh") or "")
    ok_dinh = bool(kq.get("ok")) and (thuc_te == ca.y_dinh_ky_vong)
    ok_nd, ly_do_nd = _kiem_tra_noi_dung(ca, kq)
    dat = ok_dinh and ok_nd

    tom_tat_gon = " ".join(str(kq.get("tom_tat") or "").split())[:90]
    trang_thai = "PASS" if dat else "FAIL"
    print(
        f"[{trang_thai}] ({thoi_gian:5.2f}s) '{ca.cau_hoi}' -> "
        f"yd={thuc_te} (ky_vong={ca.y_dinh_ky_vong}) | nd={ly_do_nd} | {tom_tat_gon}"
    )
    return dat, thoi_gian, str(kq.get("tom_tat") or "")


def _chay_nhom(
    ten_nhom: str,
    danh_sach: tuple[CaKiemThu, ...],
    dung_chung_phien: bool = False,
) -> tuple[int, int, float]:
    """Chay mot nhom ca test va tra ve (so_dat, tong_so, tong_thoi_gian)."""
    print(f"\n--- {ten_nhom} ({len(danh_sach)} cau) ---")
    phien = {"ma_phien": "test_hoi_thoai_lien_tuc"} if dung_chung_phien else None
    dat = 0
    tong_tg = 0.0

    for ca in danh_sach:
        ok_ca, tg, _ = _chay_mot_ca(ca, phien=phien)
        tong_tg += tg
        if ok_ca:
            dat += 1

    return dat, len(danh_sach), tong_tg


def chay_kiem_tra() -> None:
    """Chay full bo test dinh tuyen, noi dung, mach hoi thoai va thong ke toc do."""
    logger.info("Bat dau chay bo test dieu phoi y dinh.")
    tong_start = time.perf_counter()

    dat_c, tong_c, tg_c = _chay_nhom("BO TEST CHUAN", BO_TEST_CHUAN, dung_chung_phien=False)
    dat_b, tong_b, tg_b = _chay_nhom("BAY RANH GIOI", BO_TEST_BAY_RANH_GIOI, dung_chung_phien=False)
    dat_h, tong_h, tg_h = _chay_nhom("MACH HOI THOAI LIEN TUC", CHUOI_HOI_THOAI_LIEN_TUC, dung_chung_phien=True)

    tong_dat = dat_c + dat_b + dat_h
    tong_cau = tong_c + tong_b + tong_h
    tong_tg_thuc_te = time.perf_counter() - tong_start
    tong_tg_luot = tg_c + tg_b + tg_h
    tb_luot = tong_tg_luot / max(1, tong_cau)

    print("\n=== TONG KET KIEM TRA ===")
    print(f"Bo chuan         : {dat_c}/{tong_c} dat ({tg_c:.2f}s)")
    print(f"Bay ranh gioi    : {dat_b}/{tong_b} dat ({tg_b:.2f}s)")
    print(f"Hoi thoai lien   : {dat_h}/{tong_h} dat ({tg_h:.2f}s)")
    print(
        f"Tong cong        : {tong_dat}/{tong_cau} dat | "
        f"Tong thoi gian: {tong_tg_thuc_te:.2f}s | Trung binh/luot: {tb_luot:.2f}s"
    )


if __name__ == "__main__":
    chay_kiem_tra()