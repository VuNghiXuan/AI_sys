# ============================================================================
# File Path: xuong_tao_app/dich_vu/sinh_ma_sandbox/kiem_tra_ma_sinh.py
# Module: Kiem Tra Cu Phap, Chuan File Va Ghi Tep Sandbox
# Linked Files: thuc_thi_sinh_sandbox.py
# Purpose: Boc code sach tu phan hoi model, dam bao header file va logger, kiem
#          tra ast.parse va gioi han <300 dong truoc khi ghi vao thu muc test.
# ============================================================================

import ast
import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

GIOI_HAN_DONG_FILE = 300


def boc_ma_nguon_sach(phan_hoi_raw: str) -> str:
    """Loa bo markdown code fence neu model bao ngoai ma nguon."""
    van_ban = (phan_hoi_raw or "").strip()
    if not van_ban:
        return ""
    match = re.search(r"```(?:python|html|css|js|json)?\s*\n([\s\S]*?)```", van_ban, flags=re.IGNORECASE)
    if match:
        return match.group(1).strip() + "\n"
    return van_ban + "\n"


def dam_bao_header_va_logger_python(ma_nguon: str, duong_dan_tuong_doi: str, mo_ta: str) -> str:
    """Chen header file va logger chuan neu model quen them vao dau file .py."""
    ket_qua = ma_nguon
    if "File Path:" not in ket_qua:
        header = (
            "# ============================================================================\n"
            f"# File Path: {duong_dan_tuong_doi}\n"
            "# Module: Module Moi Truong Test Xuong Tao App\n"
            "# Linked Files: kho_du_lieu.py\n"
            f"# Purpose: {mo_ta or 'Module duoc sinh cho moi truong test rieng.'}\n"
            "# ============================================================================\n\n"
        )
        ket_qua = header + ket_qua

    if "logging.getLogger" not in ket_qua:
        chen_log = "import logging\n\nlogger = logging.getLogger(__name__)\n\n"
        ket_qua = chen_log + ket_qua

    return ket_qua


def kiem_tra_ma_python(ma_nguon: str) -> tuple[bool, str]:
    """Kiem tra cu phap ast.parse va gioi han so dong (<300) cho file Python."""
    so_dong = len(ma_nguon.splitlines())
    if so_dong > GIOI_HAN_DONG_FILE:
        return False, f"File vuot gioi han {GIOI_HAN_DONG_FILE} dong (hien tai: {so_dong} dong)."
    try:
        ast.parse(ma_nguon)
    except SyntaxError as exc:
        return False, f"Loi cu phap Python dong {exc.lineno}: {exc.msg}"
    return True, f"Hop le ({so_dong} dong)."


def kiem_tra_va_ghi_tep_sandbox(
    thu_muc_goc_du_an: Path,
    file_muc_tieu: str,
    phan_hoi_raw: str,
    mo_ta_task: str = "",
) -> dict[str, Any]:
    """Kiem tra ma nguon va ghi an toan vao khu vuc moi truong test rieng."""
    duong_dan_sach = (file_muc_tieu or "").strip().lstrip("/\\")
    if not duong_dan_sach:
        return {"thanh_cong": False, "trang_thai": "loi_duong_dan", "thong_bao": "Thieu file_muc_tieu."}

    tep_dich = (thu_muc_goc_du_an / duong_dan_sach).resolve()
    goc_resolve = thu_muc_goc_du_an.resolve()
    if goc_resolve not in tep_dich.parents and tep_dich != goc_resolve:
        logger.warning("Chan ghi file ngoai pham vi du an: '%s'", tep_dich)
        return {"thanh_cong": False, "trang_thai": "ngoai_pham_vi", "thong_bao": "Duong dan nam ngoai du an."}

    ma_nguon = boc_ma_nguon_sach(phan_hoi_raw)
    if not ma_nguon.strip():
        return {"thanh_cong": False, "trang_thai": "ma_rong", "thong_bao": "Model tra ve ma nguon rong."}

    if tep_dich.suffix.lower() == ".py":
        ma_nguon = dam_bao_header_va_logger_python(ma_nguon, duong_dan_sach, mo_ta_task)
        hop_le, thong_diep = kiem_tra_ma_python(ma_nguon)
        if not hop_le:
            logger.warning("Kiem tra ma that bai cho '%s': %s", duong_dan_sach, thong_diep)
            return {
                "thanh_cong": False,
                "trang_thai": "khong_dat_kiem_tra",
                "thong_bao": thong_diep,
                "so_dong": len(ma_nguon.splitlines()),
            }
    else:
        so_dong = len(ma_nguon.splitlines())
        if so_dong > GIOI_HAN_DONG_FILE:
            return {
                "thanh_cong": False,
                "trang_thai": "vuot_so_dong",
                "thong_bao": f"File vuot gioi han {GIOI_HAN_DONG_FILE} dong ({so_dong} dong).",
                "so_dong": so_dong,
            }
        thong_diep = f"Hop le ({so_dong} dong)."

    try:
        tep_dich.parent.mkdir(parents=True, exist_ok=True)
        tep_dich.write_text(ma_nguon, encoding="utf-8")
    except OSError as exc:
        logger.error("Loi ghi tep sandbox '%s': %s", tep_dich, exc, exc_info=True)
        return {"thanh_cong": False, "trang_thai": "loi_ghi_tep", "thong_bao": str(exc)}

    logger.info("Da ghi tep sandbox '%s' (%s)", duong_dan_sach, thong_diep)
    return {
        "thanh_cong": True,
        "trang_thai": "da_sinh",
        "duong_dan_tep": str(tep_dich),
        "file_muc_tieu": duong_dan_sach,
        "so_dong": len(ma_nguon.splitlines()),
        "thong_bao": thong_diep,
    }