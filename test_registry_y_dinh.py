# ============================================================================
# File Path: test_registry_y_dinh.py
# Module: Kiem Thu Nhanh BoDangKyYDinh & Luong Truy Van DB/File
# Linked Files: khoi_tao_y_dinh.py, bo_dang_ky_y_dinh.py, truy_van_du_lieu.py
# Purpose: Kiem tra nap cau hinh JSON, khop y dinh qua Registry, do thoi gian
#          phan hoi va xac minh thuc_hien_truy_van_db_va_file tra ve dung bang.
# ============================================================================

import logging
from pathlib import Path
import sys
import time

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger(__name__)

GOC_DU_AN = Path(__file__).resolve().parent
if str(GOC_DU_AN) not in sys.path:
    sys.path.insert(0, str(GOC_DU_AN))

from dieu_phoi_y_dinh.dich_vu.chi_muc_ma_nguon import xay_dung_chi_muc_ma_nguon
from dieu_phoi_y_dinh.dich_vu.khoi_tao_y_dinh import registry
from dieu_phoi_y_dinh.dich_vu.truy_van_du_lieu import thuc_hien_truy_van_db_va_file


def _kiem_tra_registry_truc_tiep(chi_muc: dict) -> None:
    """Kiem tra tung cau hoi qua registry.thuc_thi va in thoi gian xu ly."""
    cac_cau = [
        ("chức năng từng app", True),
        ("lập bảng liệt kê app, folder, file, hàm, biến trong hệ thống này", True),
        ("so sánh file chi_muc_ma_nguon.py và bo_dinh_dang_bang_ma_nguon.py", True),
        ("câu hỏi không khớp từ khóa nào cả", False),
    ]
    for cau, ky_vong_khop in cac_cau:
        t0 = time.perf_counter()
        kq = registry.thuc_thi(cau, GOC_DU_AN, chi_muc)
        tg_ms = (time.perf_counter() - t0) * 1000
        da_khop = bool(kq)
        logger.info("Registry | '%s' -> khop=%s (ky_vong=%s) | %.2f ms", cau, da_khop, ky_vong_khop, tg_ms)
        if kq:
            print(f"--- Ket qua truc tiep [{cau}] ---")
            print("\n".join(kq.splitlines()[:8]))


def _kiem_tra_qua_truy_van_du_lieu() -> None:
    """Kiem tra luong thuc_hien_truy_van_db_va_file sau khi da gan Registry."""
    cau = "chức năng từng app"
    t0 = time.perf_counter()
    res = thuc_hien_truy_van_db_va_file(cau, {"nguon": "test_script"})
    tg_ms = (time.perf_counter() - t0) * 1000
    noi_dung = res.get("thong_diep") or res.get("noi_dung") or ""
    logger.info("TruyVanDBFile | ok=%s | co_du_lieu=%s | %.2f ms", res.get("ok"), res.get("co_du_lieu"), tg_ms)
    print(f"--- Ket qua thuc_hien_truy_van_db_va_file [{cau}] ---")
    print("\n".join(noi_dung.splitlines()[:10]))


def chay_kiem_thu() -> None:
    """Chay toan bo bai test cho Registry va truy_van_du_lieu."""
    logger.info("Bat dau kiem thu tai thu muc: %s", GOC_DU_AN)
    t0 = time.perf_counter()
    chi_muc = xay_dung_chi_muc_ma_nguon(GOC_DU_AN)
    logger.info("Xay dung chi muc xong sau %.2f ms (so file=%d)", (time.perf_counter() - t0) * 1000, len(chi_muc.get("files", {})))

    _kiem_tra_registry_truc_tiep(chi_muc)
    _kiem_tra_qua_truy_van_du_lieu()


if __name__ == "__main__":
    chay_kiem_thu()