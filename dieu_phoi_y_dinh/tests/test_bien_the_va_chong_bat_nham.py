# ============================================================================
# File Path: dieu_phoi_y_dinh/tests/test_bien_the_va_chong_bat_nham.py
# Module: Kiem Thu Nhieu Bien The Prompt & Cac Truong Hop Chong Bat Nham
# Linked Files: ../dich_vu/khoi_tao_y_dinh.py, ../cau_hinh/cau_hinh_y_dinh.json,
#               test_cac_y_dinh_he_thong.py
# Purpose: Thu nghiem nhieu bien the cau hoi va dam bao cac cau hoi thuong
#          khong khop nham tao_app_chuyen_trang qua unittest.TestCase (< 300 dong).
# ============================================================================

import logging
from pathlib import Path
import sys
import unittest

_GOC_DU_AN = str(Path(__file__).resolve().parents[2])
if _GOC_DU_AN not in sys.path:
    sys.path.insert(0, _GOC_DU_AN)

logger = logging.getLogger(__name__)

_BIEN_THE_PROMPT: list[tuple[str, str]] = [
    ("liet_ke_app", "kể tên app trong hệ thống"),
    ("liet_ke_app", "cac app hien co la gi"),
    ("liet_ke_app", "tên và chức năng app"),
    ("tong_hop_thanh_phan_he_thong", "lập bảng liệt kê app và file"),
    ("tong_hop_thanh_phan_he_thong", "app, folder, file, hàm, biến"),
    ("so_sanh_file_va_ham", "phân biệt file khoi_tao_y_dinh.py và bo_dang_ky_y_dinh.py"),
    ("so_sanh_file_va_ham", "liên kết giữa các file trong dieu_phoi_y_dinh"),
    ("tra_cuu_cau_hinh_va_model", "cau hinh may va model dang dung"),
    ("tra_cuu_cau_hinh_va_model", "may dang xai co may model"),
    ("tao_app_chuyen_trang", "lập ứng dụng quản lý chấm công"),
    ("tao_app_chuyen_trang", "xay dung app theo doi don hang"),
    ("muc_dich_va_kien_truc_he_thong", "he thong nay lam gi va cau truc ra sao"),
    ("muc_dich_va_kien_truc_he_thong", "luong hoat dong chinh cua he thong"),
    ("muc_dich_va_kien_truc_he_thong", "dung he thong the nao"),
    ("danh_sach_y_dinh_he_thong", "các ý định hiện có"),
    ("danh_sach_y_dinh_he_thong", "co nhung y dinh nao"),
    ("cau_truc_model_va_truong_du_lieu", "model co cac truong gi"),
    ("cau_truc_model_va_truong_du_lieu", "cau truc bang db hien tai"),
    ("quy_trinh_nang_cap_sua_doi", "muon sua thi lam gi"),
    ("quy_trinh_nang_cap_sua_doi", "quy trinh sua code khi nang cap"),
    ("huong_dan_tim_va_them_chuc_nang_ham", "muon tim ham xu_ly_phan_tich o dau"),
    ("huong_dan_tim_va_them_chuc_nang_ham", "them 1 ham moi thi can lam gi"),
    ("huong_dan_tim_va_them_chuc_nang_ham", "cach dat prompt tra cuu he thong"),
]

_CAU_KHONG_DUOC_KHOP_TAO_APP: list[str] = [
    "alo",
    "nhắc tên tao",
    "thời tiết đệp nhỉ",
    "tuy hoà có mưa không",
    "hướng dẫn tao cách sử dụng hệ thống",
    "liệt kê các thông tin hệ thống đi",
]


class TestBienTheVaChongBatNham(unittest.TestCase):
    """Bo test nhieu bien the cau hoi va kiem tra chong bat nham tao_app_chuyen_trang."""

    def test_01_nhieu_bien_the_prompt(self) -> None:
        """Kiem tra tat ca bien the cau hoi deu khop dung ma_y_dinh ky vong."""
        from dieu_phoi_y_dinh.dich_vu.khoi_tao_y_dinh import registry

        for ma_ky_vong, prompt in _BIEN_THE_PROMPT:
            yd = registry.khop_nhanh(prompt)
            self.assertIsNotNone(yd, f"Bien chua khop: '{prompt}' (ky vong '{ma_ky_vong}')")
            assert yd is not None
            self.assertEqual(
                yd.ma_y_dinh,
                ma_ky_vong,
                f"Bien the '{prompt}' khop sai: ky vong '{ma_ky_vong}', nhan '{yd.ma_y_dinh}'",
            )
            logger.info("PASS bien the [%s] <- '%s'", ma_ky_vong, prompt)

    def test_02_khong_bat_nham_tao_app(self) -> None:
        """Dam bao cac cau hoi thuong/nhac lai/huong dan khong bi bat nham tao_app_chuyen_trang."""
        from dieu_phoi_y_dinh.dich_vu.khoi_tao_y_dinh import registry

        for cau in _CAU_KHONG_DUOC_KHOP_TAO_APP:
            yd = registry.khop_nhanh(cau)
            if yd is not None:
                self.assertNotEqual(
                    yd.ma_y_dinh,
                    "tao_app_chuyen_trang",
                    f"Cau '{cau}' bi bat nham sang tao_app_chuyen_trang",
                )
            logger.info("PASS chong bat nham tao_app <- '%s' (khop=%s)", cau, yd.ma_y_dinh if yd else None)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    unittest.main()