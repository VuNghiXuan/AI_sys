# ============================================================================
# File Path: dieu_phoi_y_dinh/dich_vu/dinh_tuyen/khoi_tao_y_dinh.py
# Module: Khoi Tao Registry Mac Dinh Cho Dieu Phoi Y Dinh
# ============================================================================

from pathlib import Path
from .bo_dang_ky_y_dinh import BoDangKyYDinh


def _tao_registry() -> BoDangKyYDinh:
    """Khoi tao registry tu cau_hinh/cau_hinh_y_dinh.json."""
    duong_dan_json = Path(__file__).resolve().parents[2] / "cau_hinh" / "cau_hinh_y_dinh.json"
    reg = BoDangKyYDinh()
    if duong_dan_json.exists():
        reg.nap_tu_json(duong_dan_json)
    return reg


registry: BoDangKyYDinh = _tao_registry()