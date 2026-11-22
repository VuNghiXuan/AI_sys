# ==============================================================================
# File Path: xu_ly_chinh.py
# Description: Auto-generated slice for work item M2 of Tao chuc nang doi soat du lieu cho ke toan de giam sai sot.
# Linked Files: [quan_ly_du_an/dich_vu_dieu_phoi.py]
# Logs: Execute chay_xu_ly with configured fields.
# ==============================================================================

TRUONG_DU_LIEU_MAC_DINH = ['ma_phieu', 'so_tien_ke_toan', 'so_tien_thuc_te', 'chenh_lech']


def chay_xu_ly(du_lieu_vao: dict | None = None) -> dict:
    """Process input dictionary and return standardized result."""
    du_lieu = du_lieu_vao or {}
    return {
        "ma_muc": 'M2',
        "trang_thai": "ok",
        "so_truong": len(TRUONG_DU_LIEU_MAC_DINH),
        "du_lieu_nhan": du_lieu,
    }
