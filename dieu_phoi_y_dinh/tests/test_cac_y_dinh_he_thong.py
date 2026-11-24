# ============================================================================
# File Path: dieu_phoi_y_dinh/tests/test_cac_y_dinh_he_thong.py
# Module: Kiem Thu Toan Bo Y Dinh Da Dang Ky Trong Registry
# Linked Files: ../dich_vu/khoi_tao_y_dinh.py, ../dich_vu/bo_dang_ky_y_dinh.py,
#               ../dich_vu/tra_cuu_huong_dan_he_thong.py,
#               ../cau_hinh/cau_hinh_y_dinh.json,
#               test_bien_the_va_chong_bat_nham.py
# Purpose: Kiem tra cau hinh JSON, khop nhanh va thuc thi cho tat ca 10 y dinh
#          trong Registry qua unittest.TestCase (< 300 dong).
# ============================================================================

import json
import logging
from pathlib import Path
from typing import Any
import unittest
from unittest.mock import patch

logger = logging.getLogger(__name__)

_MA_Y_DINH_KY_VONG = [
    "liet_ke_app",
    "tong_hop_thanh_phan_he_thong",
    "so_sanh_file_va_ham",
    "tra_cuu_cau_hinh_va_model",
    "tao_app_chuyen_trang",
    "muc_dich_va_kien_truc_he_thong",
    "danh_sach_y_dinh_he_thong",
    "cau_truc_model_va_truong_du_lieu",
    "quy_trinh_nang_cap_sua_doi",
    "huong_dan_tim_va_them_chuc_nang_ham",
]


def _tao_chi_muc_mau() -> dict[str, Any]:
    """Tao du lieu chi muc mau nhe de test khong can quet toan bo repo."""
    return {
        "files": {
            "dieu_phoi_y_dinh/dich_vu/khoi_tao_y_dinh.py": {
                "mo_ta": "Khoi tao registry y dinh",
                "ham": [{"ten": "_tao_registry_mac_dinh", "tham_so": [], "dong": 55, "mo_ta": "Tao registry"}],
                "bien": [{"ten": "registry", "loai": "bien/hang", "dong": 75, "mo_ta": "Dong 75"}],
                "lien_ket_di_ra": ["dieu_phoi_y_dinh/dich_vu/bo_dang_ky_y_dinh.py"],
                "lien_ket_di_vao": [],
            },
            "dieu_phoi_y_dinh/dich_vu/bo_dang_ky_y_dinh.py": {
                "mo_ta": "Quan ly danh sach y dinh va trinh xu ly",
                "ham": [{"ten": "khop_nhanh", "tham_so": ["self", "cau_hoi"], "dong": 40, "mo_ta": "Khop y dinh"}],
                "bien": [{"ten": "BoDangKyYDinh", "loai": "class", "dong": 20, "mo_ta": "Lop registry"}],
                "lien_ket_di_ra": [],
                "lien_ket_di_vao": ["dieu_phoi_y_dinh/dich_vu/khoi_tao_y_dinh.py"],
            },
        },
        "ham": [
            {"ten": "_tao_registry_mac_dinh", "file": "dieu_phoi_y_dinh/dich_vu/khoi_tao_y_dinh.py", "tham_so": [], "dong": 55, "mo_ta": "Tao registry"},
            {"ten": "khop_nhanh", "file": "dieu_phoi_y_dinh/dich_vu/bo_dang_ky_y_dinh.py", "tham_so": ["self", "cau_hoi"], "dong": 40, "mo_ta": "Khop y dinh"},
        ],
        "bien": [
            {"ten": "registry", "file": "dieu_phoi_y_dinh/dich_vu/khoi_tao_y_dinh.py", "loai": "bien/hang", "dong": 75, "mo_ta": "Dong 75"},
            {"ten": "BoDangKyYDinh", "file": "dieu_phoi_y_dinh/dich_vu/bo_dang_ky_y_dinh.py", "loai": "class", "dong": 20, "mo_ta": "Lop registry"},
        ],
    }


class TestCacYDinhHeThong(unittest.TestCase):
    """Bo test kiem thu cau hinh va thuc thi 10 y dinh trong Registry."""

    def test_01_cau_hinh_json_va_ten_trinh_xu_ly(self) -> None:
        """Kiem tra file JSON hop le, du 10 ma y dinh va khop ten trinh xu ly."""
        goc_app = Path(__file__).resolve().parent.parent
        duong_dan_json = goc_app / "cau_hinh" / "cau_hinh_y_dinh.json"
        du_lieu = json.loads(duong_dan_json.read_text(encoding="utf-8"))
        ds_yd = du_lieu.get("y_dinh") or []

        ma_da_dang_ky = [item.get("ma_y_dinh") for item in ds_yd]
        logger.info("Kiem tra %d y dinh trong cau_hinh_y_dinh.json", len(ma_da_dang_ky))

        for ma_yd in _MA_Y_DINH_KY_VONG:
            self.assertIn(ma_yd, ma_da_dang_ky, f"Thieu y dinh: {ma_yd}")

        for item in ds_yd:
            self.assertTrue(item.get("ma_y_dinh"), "Thieu ma_y_dinh")
            self.assertTrue(item.get("ten_trinh_xu_ly"), f"Thieu ten_trinh_xu_ly cho {item.get('ma_y_dinh')}")
            self.assertTrue(
                isinstance(item.get("tu_khoa_nhanh"), list) and len(item["tu_khoa_nhanh"]) > 0,
                f"Thieu tu_khoa_nhanh cho {item.get('ma_y_dinh')}",
            )

    def test_02_khop_va_thuc_thi_tat_ca_y_dinh(self) -> None:
        """Kiem tra tung y dinh khop trong Registry va thuc thi tra ve ket qua hop le."""
        from dieu_phoi_y_dinh.dich_vu.dinh_tuyen.khoi_tao_y_dinh import registry

        goc_du_an = Path(__file__).resolve().parents[2]
        chi_muc = _tao_chi_muc_mau()

        bo_cau_test = {
            "liet_ke_app": "chức năng từng app",
            "tong_hop_thanh_phan_he_thong": "tổng hợp thành phần",
            "so_sanh_file_va_ham": "so sánh file khoi_tao_y_dinh.py và bo_dang_ky_y_dinh.py",
            "tra_cuu_cau_hinh_va_model": "cấu hình máy hiện tại",
            "tao_app_chuyen_trang": "tạo app quản lý kho",
            "muc_dich_va_kien_truc_he_thong": "hướng dẫn tao cách sử dụng hệ thống",
            "danh_sach_y_dinh_he_thong": "danh sách các ý định",
            "cau_truc_model_va_truong_du_lieu": "các trường của model",
            "quy_trinh_nang_cap_sua_doi": "muốn nâng cấp thì làm gì",
            "huong_dan_tim_va_them_chuc_nang_ham": "muốn thêm chức năng thì làm sao",
        }

        with (
            patch(
                "dieu_phoi_y_dinh.dich_vu.khoi_tao_y_dinh.xu_ly_xac_nhan_tao_app",
                return_value={"noi_dung_tra_loi": "Chuyển sang Xưởng Tạo App"},
            ),
            patch(
                "dieu_phoi_y_dinh.dich_vu.khoi_tao_y_dinh.bao_cao_cau_hinh_va_model",
                return_value="Cấu hình OK",
            ),
        ):
            for ma_yd_ky_vong, cau_hoi in bo_cau_test.items():
                yd_khop = registry.khop_nhanh(cau_hoi)
                self.assertIsNotNone(yd_khop, f"Khong khop y dinh cho cau: '{cau_hoi}'")
                assert yd_khop is not None
                self.assertEqual(
                    yd_khop.ma_y_dinh,
                    ma_yd_ky_vong,
                    f"Cau '{cau_hoi}' khop sai: ky vong '{ma_yd_ky_vong}', nhan '{yd_khop.ma_y_dinh}'",
                )
                ket_qua = registry.thuc_thi(cau_hoi, goc_du_an, chi_muc)
                self.assertTrue(ket_qua, f"Ket qua thuc thi rong cho y dinh '{ma_yd_ky_vong}'")
                logger.info("PASS [%s] <- '%s'", ma_yd_ky_vong, cau_hoi)
    
    def test_03_do_vi_tri_file_ham_va_lien_ket(self) -> None:
        """Kiem tra cac cau hoi do vi tri file, ham va lien ket phuc vu vibe code."""
        from dieu_phoi_y_dinh.dich_vu.dinh_tuyen.khoi_tao_y_dinh import registry

        goc_du_an = Path(__file__).resolve().parents[2]
        chi_muc = _tao_chi_muc_mau()

        cau_hoi_do_code = [
            "file khoi_tao_y_dinh.py nằm ở đâu",
            "hàm khop_nhanh nằm ở file nào",
            "file bo_dang_ky_y_dinh.py liên kết với file nào",
        ]
        for cau in cau_hoi_do_code:
            yd_khop = registry.khop_nhanh(cau)
            self.assertIsNotNone(yd_khop, f"Chua khop y dinh cho cau do code: '{cau}'")
            ket_qua = registry.thuc_thi(cau, goc_du_an, chi_muc)
            self.assertTrue(ket_qua, f"Khong co ket qua thuc thi cho cau: '{cau}'")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    unittest.main()