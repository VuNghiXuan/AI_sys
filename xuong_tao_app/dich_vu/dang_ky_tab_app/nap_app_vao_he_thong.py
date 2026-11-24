# ============================================================================
# File Path: xuong_tao_app/dich_vu/dang_ky_tab_app/nap_app_vao_he_thong.py
# Module: Nap App Da Test Tren Moi Truong Rieng Vao Khung He Thong
# Linked Files: quan_ly_registry_tab.py
# Purpose: Kiem tra thu muc test rieng, sao chep ma nguon sang khu vuc tich
#          hop cua he thong va dang ky 1 tab chinh + cac chuc nang con.
# ============================================================================

import logging
import shutil
from pathlib import Path
from typing import Any

from xuong_tao_app.dich_vu.dang_ky_tab_app.quan_ly_registry_tab import (
    _chuan_hoa_ma,
    luu_hoac_cap_nhat_tab_app,
)

logger = logging.getLogger(__name__)


def _sao_chep_ma_sang_khung_tich_hop(
    thu_muc_sandbox_app: Path,
    thu_muc_dich_tich_hop: Path,
) -> tuple[bool, int, str]:
    """Sao chep cac tep ma/giao dien (bo qua .backups) tu sandbox sang thu muc tich hop."""
    if not thu_muc_sandbox_app.exists() or not thu_muc_sandbox_app.is_dir():
        return False, 0, f"Không tìm thấy thư mục test riêng: '{thu_muc_sandbox_app}'."

    so_tep_chep = 0
    try:
        for tep_nguon in thu_muc_sandbox_app.rglob("*"):
            if not tep_nguon.is_file() or ".backups" in tep_nguon.parts:
                continue
            tuong_doi = tep_nguon.relative_to(thu_muc_sandbox_app)
            tep_dich = thu_muc_dich_tich_hop / tuong_doi
            tep_dich.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(tep_nguon, tep_dich)
            so_tep_chep += 1
    except OSError as exc:
        logger.error("Loi sao chep ma nguon vao khung tich hop: %s", exc, exc_info=True)
        return False, so_tep_chep, str(exc)

    if so_tep_chep == 0:
        return False, 0, "Thư mục test riêng chưa có tệp nào để nạp vào hệ thống."

    return True, so_tep_chep, f"Đã nạp {so_tep_chep} tệp vào khung tích hợp."


def nap_app_vao_khung_he_thong(
    thu_muc_goc_du_an: Path,
    ma_app: str,
    tieu_de_tab: str,
    chuc_nang_con: list[Any],
    yeu_cau_da_test_on: bool = True,
) -> dict[str, Any]:
    """Chuyen app tu moi truong test rieng va dang ky 1 tab chinh + chuc nang con."""
    if not yeu_cau_da_test_on:
        logger.warning("Chan nap app '%s' vi chua xac nhan da test on tren moi truong rieng", ma_app)
        return {
            "thanh_cong": False,
            "trang_thai": "chua_xac_nhan_test",
            "thong_bao": "Cần xác nhận đã test thực tế trên môi trường riêng trước khi đưa vào tab hệ thống.",
        }

    ma_sach = _chuan_hoa_ma(ma_app)
    thu_muc_sandbox = (thu_muc_goc_du_an / "sandbox_apps" / ma_sach).resolve()
    thu_muc_tich_hop = (thu_muc_goc_du_an / "ung_dung_tich_hop" / ma_sach).resolve()

    ok_chep, so_tep, thong_bao_chep = _sao_chep_ma_sang_khung_tich_hop(thu_muc_sandbox, thu_muc_tich_hop)
    if not ok_chep:
        logger.warning("Nap app '%s' that bai o buoc sao chep: %s", ma_sach, thong_bao_chep)
        return {
            "thanh_cong": False,
            "trang_thai": "loi_sao_chep",
            "thong_bao": thong_bao_chep,
        }

    ket_qua_dang_ky = luu_hoac_cap_nhat_tab_app(
        thu_muc_goc_du_an=thu_muc_goc_du_an,
        ma_app=ma_sach,
        tieu_de_tab=tieu_de_tab,
        chuc_nang_con=chuc_nang_con,
        duong_dan_ung_dung=f"/ung-dung/{ma_sach}/",
        nguon_tu_sandbox=str(thu_muc_sandbox),
    )
    if not ket_qua_dang_ky.get("thanh_cong"):
        return ket_qua_dang_ky

    logger.info("Hoan tat nap app '%s' vao khung he thong (%d tep, tab='%s')", ma_sach, so_tep, tieu_de_tab)
    return {
        "thanh_cong": True,
        "trang_thai": "da_nap_vao_he_thong",
        "ma_app": ma_sach,
        "so_tep_da_nap": so_tep,
        "thu_muc_tich_hop": str(thu_muc_tich_hop),
        "tab": ket_qua_dang_ky.get("tab"),
        "thong_bao": f"{thong_bao_chep} {ket_qua_dang_ky.get('thong_bao', '')}".strip(),
    }