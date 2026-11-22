# ==============================================================================
# File Path: lat_cat_da_tao\ho_so_2\xu_ly_chinh.py
# Description: Auto-generated slice for work item M2 of Tao chuc nang kiem ke va doi soat lich su quet san pham vang cho nhan vien kho.
# Linked Files: [quan_ly_du_an/dich_vu_dieu_phoi.py]
# Logs: Execute chay_xu_ly with configured fields.
# ==============================================================================

TRUONG_DU_LIEU_MAC_DINH = ['ma_phieu_kiem_ke', 'ma_san_pham', 'tuoi_vang', 'trong_luong_he_thong', 'trong_luong_quet', 'thoi_gian_quet', 'trang_thai_lech']


def chay_xu_ly(du_lieu_vao: dict | None = None) -> dict:
    """Process input dictionary and return standardized result."""
    du_lieu = du_lieu_vao or {}
    return {
        "ma_muc": 'M2',
        "trang_thai": "ok",
        "so_truong": len(TRUONG_DU_LIEU_MAC_DINH),
        "du_lieu_nhan": du_lieu,
    }
