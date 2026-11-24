# ============================================================================
# File Path: dieu_phoi_y_dinh/tests/test_da_y_dinh_va_cau_lat_leo.py
# Module: Bo Test Da Y Dinh, Cau Hoi Lat Leo Va Hoc Tang Cuong Q&A
# Linked Files: dieu_phoi_y_dinh/dich_vu/dieu_phoi_nhanh.py,
#               dieu_phoi_y_dinh/dich_vu/tach_va_loc_y_dinh.py,
#               dieu_phoi_y_dinh/dich_vu/bo_nho_va_cache.py,
#               dieu_phoi_y_dinh/dich_vu/hoc_tang_cuong_qa.py
# Purpose: Kiem thu cac prompt go thieu dau/thieu chu ngu, cau hoi lat leo,
#          da y dinh, noi tiep luot truoc va thuong/phat hoc tang cuong Q&A.
# ============================================================================

import json
import logging
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase

from dieu_phoi_y_dinh.dich_vu import bo_nho_va_cache, hoc_tang_cuong_qa
from dieu_phoi_y_dinh.dich_vu.dieu_phoi_nhanh import xu_ly_prompt_da_y_dinh
from dieu_phoi_y_dinh.dich_vu.dinh_tuyen.khoi_tao_y_dinh import registry

logger = logging.getLogger(__name__)


def _gia_lap_thuc_thi(cau_hoi: str, goc_du_an: Path, chi_muc: dict, ma_y_dinh_chi_dinh: str = ""):
    """Gia lap ket qua thuc thi tung y dinh de test luong dieu phoi/ngu canh nhanh."""
    del goc_du_an, chi_muc
    yd = ma_y_dinh_chi_dinh or "chat_tu_do"
    return {
        "noi_dung": f"[YD={yd}] {cau_hoi}",
        "chuyen_huong_tao_app": yd == "tao_app",
    }


class TestDaYDinHVaCauLatLeo(TestCase):
    """Kiem thu prompt go ngan, thieu dau, da y dinh, noi tiep va hoc Q&A."""

    def setUp(self) -> None:
        """Reset trang thai phien, cache va file bo_nho_hoc_qa truoc moi test."""
        self.ma_phien = "phien_test_lat_leo"
        bo_nho_va_cache._LICH_SU_THEO_PHIEN.clear()
        bo_nho_va_cache._BO_DEM_CACHE.clear()
        self.tep_qa_tam = Path(__file__).resolve().parents[1] / "du_lieu" / "bo_nho_hoc_qa_test.json"
        if self.tep_qa_tam.exists():
            self.tep_qa_tam.unlink()
        self.patcher_qa = patch.object(hoc_tang_cuong_qa, "DUONG_DAN_DU_LIEU_QA", self.tep_qa_tam)
        self.patcher_qa.start()
        self.patcher_thuc_thi = patch.object(registry, "thuc_thi", side_effect=_gia_lap_thuc_thi)
        self.patcher_thuc_thi.start()

    def tearDown(self) -> None:
        """Don dep patch va file tam sau moi test."""
        self.patcher_thuc_thi.stop()
        self.patcher_qa.stop()
        if self.tep_qa_tam.exists():
            self.tep_qa_tam.unlink()

    def _goi_dieu_phoi(self, prompt: str) -> dict:
        """Goi xu_ly_prompt_da_y_dinh voi phien test co dinh."""
        phien = SimpleNamespace(session_key=self.ma_phien)
        return xu_ly_prompt_da_y_dinh(prompt=prompt, session=phien)

    def test_cau_go_thieu_dau_va_thieu_chu_ngu(self) -> None:
        """Kiem tra cac cau nguoi dung go thieu dau, go tat hoac cut loi."""
        logger.info("Bat dau test_cau_go_thieu_dau_va_thieu_chu_ngu")
        kq_dong = self._goi_dieu_phoi("may dong du lieu bao nhieu")
        self.assertTrue(kq_dong["ok"])
        self.assertEqual(kq_dong["y_dinh"], "thong_ke_du_lieu_db")

        kq_ham = self._goi_dieu_phoi("mo ta chuc nang tung ham")
        self.assertTrue(kq_ham["ok"])
        self.assertEqual(kq_ham["y_dinh"], "viet_code_va_phan_tich")

        kq_ram = self._goi_dieu_phoi("ram con bao nhieu")
        self.assertTrue(kq_ram["ok"])
        self.assertEqual(kq_ram["y_dinh"], "tra_cuu_telemetry_va_model")

        kq_mua = self._goi_dieu_phoi("ngoai troi mua hay nang")
        self.assertTrue(kq_mua["ok"])
        self.assertEqual(kq_mua["y_dinh"], "tra_cuu_mang_va_thoi_su")

    def test_prompt_da_y_dinh_nhieu_ve_va_khong_tach_nham_cum_ghep(self) -> None:
        """Kiem tra tach dung nhieu y dinh va giu nguyen cum danh tu ghep."""
        logger.info("Bat dau test_prompt_da_y_dinh_nhieu_ve_va_khong_tach_nham_cum_ghep")
        kq_nhieu_ve = self._goi_dieu_phoi(
            "ram con bao nhieu; bao nhieu dong du lieu roi mo ta tung ham"
        )
        self.assertTrue(kq_nhieu_ve["ok"])
        self.assertGreaterEqual(len(kq_nhieu_ve["danh_sach_y_dinh"]), 2)
        self.assertIn("thong_ke_du_lieu_db", kq_nhieu_ve["danh_sach_y_dinh"])
        self.assertIn("viet_code_va_phan_tich", kq_nhieu_ve["danh_sach_y_dinh"])
        self.assertIn("---", kq_nhieu_ve["tom_tat"])

        kq_cum_ghep = self._goi_dieu_phoi("app và model hiện có gì")
        self.assertTrue(kq_cum_ghep["ok"])
        self.assertEqual(len(kq_cum_ghep["danh_sach_y_dinh"]), 1)

    def test_noi_tiep_luot_truoc_va_dinh_chinh_khi_hoi_lai(self) -> None:
        """Kiem tra luot sau noi tiep lap bang/dinh chinh bam dung y dinh luot truoc."""
        logger.info("Bat dau test_noi_tiep_luot_truoc_va_dinh_chinh_khi_hoi_lai")
        luot_1 = self._goi_dieu_phoi("mo ta chuc nang tung ham")
        self.assertEqual(luot_1["y_dinh"], "viet_code_va_phan_tich")

        luot_2 = self._goi_dieu_phoi("tao hoi ham ma, lap thanh bang")
        self.assertEqual(luot_2["y_dinh"], "viet_code_va_phan_tich")
        self.assertNotEqual(luot_2["y_dinh"], "tra_cuu_mang_va_thoi_su")

    def test_nho_ten_ngan_va_hoc_tang_cuong_thuong_phat(self) -> None:
        """Kiem tra nho ten sau cau tra loi ngan va ghi nhan diem thuong/phat Q&A."""
        logger.info("Bat dau test_nho_ten_ngan_va_hoc_tang_cuong_thuong_phat")
        self._goi_dieu_phoi("tao teen gi")
        self._goi_dieu_phoi("Vũ")
        self.assertEqual(bo_nho_va_cache.lay_ten_nguoi_dung_phien(self.ma_phien), "Vũ")

        kq_sai = self._goi_dieu_phoi("ngoai troi mua hay nang")
        self.assertEqual(kq_sai["y_dinh"], "tra_cuu_mang_va_thoi_su")
        self._goi_dieu_phoi("sai roi, tao hoi ham ma")

        du_lieu_qa = json.loads(self.tep_qa_tam.read_text(encoding="utf-8"))
        trong_so_cu = du_lieu_qa.get("trong_so_y_dinh", {}).get("ngoai troi mua hay nang", {})
        self.assertLess(trong_so_cu.get("tra_cuu_mang_va_thoi_su", 0.0), 0.0)
        self.assertTrue(any(m.get("la_dinh_chinh") for m in du_lieu_qa.get("mau_qa", [])))