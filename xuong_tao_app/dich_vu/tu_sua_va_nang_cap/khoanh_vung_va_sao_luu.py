# ============================================================================
# File Path: xuong_tao_app/dich_vu/tu_sua_va_nang_cap/khoanh_vung_va_sao_luu.py
# Module: Khoanh Vung Tep Lien Quan Va Sao Luu / Hoan Tac
# Linked Files: vong_lap_tu_sua.py
# Purpose: Phan loai y do (sua loi hay nang cap), chon dung cac tep trong thu
#          muc test rieng cua app va quan ly ban sao luu de hoan tac an toan.
# ============================================================================

import logging
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_MAU_NANG_CAP = re.compile(
    r"\b(thêm|them|nâng\s+cấp|nang\s+cap|mở\s+rộng|mo\s+rong|bổ\s+sung|bo\s+sung|"
    r"tính\s+năng\s+mới|tinh\s+nang\s+moi|cột\s+mới|cot\s+moi|tab\s+mới|tab\s+moi)\b",
    flags=re.IGNORECASE,
)


def phan_loai_y_do_phan_hoi(prompt_phan_hoi: str, mo_ta_anh: str = "") -> str:
    """Phan loai phan hoi test giao dien la 'nang_cap' hay 'sua_loi'."""
    tong_hop = f"{prompt_phan_hoi or ''} {mo_ta_anh or ''}".strip().lower()
    if not tong_hop:
        return "sua_loi"
    loai = "nang_cap" if _MAU_NANG_CAP.search(tong_hop) else "sua_loi"
    logger.debug("Phan loai y do phan hoi -> %s", loai)
    return loai


def khoanh_vung_tep_lien_quan(
    thu_muc_goc_du_an: Path,
    ma_app: str,
    prompt_phan_hoi: str,
    mo_ta_anh: str = "",
    ma_chuc_nang_con: str = "",
    gioi_han_tep: int = 3,
) -> list[Path]:
    """Khoanh vung dung cac tep thuoc thu muc test rieng cua app ma_app."""
    thu_muc_app = (thu_muc_goc_du_an / "sandbox_apps" / (ma_app or "").strip()).resolve()
    if not thu_muc_app.exists() or not thu_muc_app.is_dir():
        logger.warning("Khong tim thay thu muc test rieng cua app: '%s'", thu_muc_app)
        return []

    cac_tep = [p for p in sorted(thu_muc_app.rglob("*")) if p.is_file() and ".backups" not in p.parts]
    if not cac_tep:
        return []

    goi_y_tim = f"{prompt_phan_hoi or ''} {mo_ta_anh or ''} {ma_chuc_nang_con or ''}".lower()
    tep_cham_diem: list[tuple[int, Path]] = []

    for tep in cac_tep:
        diem = 0
        ten_thap = tep.name.lower()
        stem = tep.stem.lower()
        if ma_chuc_nang_con and ma_chuc_nang_con.lower() in ten_thap:
            diem += 10
        if stem and stem in goi_y_tim:
            diem += 6
        if tep.suffix.lower() == ".html" and any(k in goi_y_tim for k in ("giao diện", "giao dien", "nút", "nut", "bảng", "bang", "form", "màn hình", "man hinh")):
            diem += 5
        if "kho_du_lieu" in ten_thap and any(k in goi_y_tim for k in ("dữ liệu", "du lieu", "cột", "cot", "lưu", "luu")):
            diem += 4
        tep_cham_diem.append((diem, tep))

    tep_cham_diem.sort(key=lambda pair: (-pair[0], pair[1].name))
    ds_chon = [tep for _, tep in tep_cham_diem[: max(1, gioi_han_tep)]]
    logger.info("Khoanh vung %d tep cho app '%s': %s", len(ds_chon), ma_app, [p.name for p in ds_chon])
    return ds_chon


def sao_luu_cac_tep(thu_muc_goc_du_an: Path, ma_app: str, danh_sach_tep: list[Path]) -> str:
    """Tao ban sao luu cac tep truoc khi sua/nang cap va tra ve ma snapshot."""
    ma_snapshot = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    thu_muc_backup = thu_muc_goc_du_an / "sandbox_apps" / ma_app / ".backups" / ma_snapshot
    thu_muc_app = (thu_muc_goc_du_an / "sandbox_apps" / ma_app).resolve()

    for tep in danh_sach_tep:
        if not tep.exists():
            continue
        try:
            tuong_doi = tep.resolve().relative_to(thu_muc_app)
        except ValueError:
            tuong_doi = Path(tep.name)
        dich_backup = thu_muc_backup / tuong_doi
        dich_backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(tep, dich_backup)

    logger.info("Da sao luu %d tep vao snapshot '%s'", len(danh_sach_tep), ma_snapshot)
    return ma_snapshot


def hoan_tac_tu_ban_sao_luu(thu_muc_goc_du_an: Path, ma_app: str, ma_snapshot: str) -> dict[str, Any]:
    """Khoi phuc cac tep tu snapshot da sao luu truoc do."""
    thu_muc_app = (thu_muc_goc_du_an / "sandbox_apps" / ma_app).resolve()
    thu_muc_backup = (thu_muc_app / ".backups" / ma_snapshot).resolve()
    if not thu_muc_backup.exists() or not thu_muc_backup.is_dir():
        logger.warning("Khong tim thay snapshot '%s' de hoan tac", ma_snapshot)
        return {"thanh_cong": False, "thong_bao": f"Không tìm thấy bản sao lưu '{ma_snapshot}'."}

    so_tep_khoi_phuc = 0
    for tep_cu in thu_muc_backup.rglob("*"):
        if not tep_cu.is_file():
            continue
        tuong_doi = tep_cu.relative_to(thu_muc_backup)
        tep_dich = thu_muc_app / tuong_doi
        tep_dich.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(tep_cu, tep_dich)
        so_tep_khoi_phuc += 1

    logger.info("Da hoan tac %d tep tu snapshot '%s'", so_tep_khoi_phuc, ma_snapshot)
    return {
        "thanh_cong": True,
        "ma_snapshot": ma_snapshot,
        "so_tep_khoi_phuc": so_tep_khoi_phuc,
        "thong_bao": f"Đã hoàn tác {so_tep_khoi_phuc} tệp về bản lưu '{ma_snapshot}'.",
    }