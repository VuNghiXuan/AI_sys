# ============================================================================
# File Path: test_da_y_dinh_registry.py
# Module: Kiem Thu Luong Tach Da Y Dinh -> BoDangKyYDinh -> Gop Ket Qua
# Linked Files: bo_dieu_phoi_da_y_dinh.py, khoi_tao_y_dinh.py, chi_muc_ma_nguon.py
# Purpose: Kiem thu prompt don va prompt da y dinh (co y trong Registry va y
#          ngoai Registry), do toc do va kiem tra ket qua gop.
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

from dieu_phoi_y_dinh.dich_vu.bo_dieu_phoi_da_y_dinh import BoDieuPhoiDaYDinh
from dieu_phoi_y_dinh.dich_vu.chi_muc_ma_nguon import xay_dung_chi_muc_ma_nguon
from dieu_phoi_y_dinh.dich_vu.khoi_tao_y_dinh import registry


def _nhanh_ngoai_gia_lap(y_con: str, ngu_canh: dict) -> str:
    """Mo phong nhanh ngoai Registry (tim kiem mang / vibe / chat) khi khong khop Registry."""
    return f"Chuyen toi nhanh xu ly ngoai Registry cho cau: '{y_con}'"


def chay_test() -> None:
    """Chay thu nghiem dieu phoi da y dinh."""
    chi_muc = xay_dung_chi_muc_ma_nguon(GOC_DU_AN)
    bo_dieu_phoi = BoDieuPhoiDaYDinh(registry=registry, trinh_xu_ly_ngoai=_nhanh_ngoai_gia_lap)

    cac_prompt = [
        "chức năng từng app rồi so sánh file chi_muc_ma_nguon.py và bo_dinh_dang_bang_ma_nguon.py",
        "chức năng từng app và giải thích kiến trúc phân tầng của hệ thống này",
    ]
    for prompt in cac_prompt:
        t0 = time.perf_counter()
        kq = bo_dieu_phoi.dieu_phoi(prompt, GOC_DU_AN, chi_muc)
        dt_ms = (time.perf_counter() - t0) * 1000
        logger.info(
            "Prompt xong sau %.2f ms | so_y=%d | y_chua_khop=%s",
            dt_ms,
            len(kq.ket_qua_tung_y),
            kq.y_chua_khop,
        )
        print(f"\n==================== PROMPT: {prompt} ====================")
        print(kq.noi_dung_gop[:700])


if __name__ == "__main__":
    chay_test()