# ============================================================================
# File Path: xuong_tao_app/dich_vu/quet_thu_muc/quet_thu_muc_nguon.py
# Module: Quet Thu Muc Nguon Phuc Vu Tao App
# Linked Files: doc_tep_an_toan.py, ../thiet_ke_va_task/
# Purpose: Kiem tra duong dan thu muc nguon, duyet danh sach tep hop le co
#          gioi han va tong hop du lieu da doc cho buoc thiet ke nghiep vu.
# ============================================================================

import logging
from pathlib import Path
from typing import Any

from xuong_tao_app.dich_vu.quet_thu_muc.doc_tep_an_toan import (
    doc_noi_dung_tep,
    la_tep_duoc_ho_tro,
    la_thu_muc_bi_bo_qua,
)

logger = logging.getLogger(__name__)

GIOI_HAN_SO_TEP_TOI_DA = 40
GIOI_HAN_TONG_KY_TU = 120_000


def _thu_thap_tep_hop_le(thu_muc_goc: Path, quet_de_quy: bool = True) -> list[Path]:
    """Thu thap danh sach tep ho tro trong thu muc goc theo thu tu on dinh."""
    danh_sach_tep: list[Path] = []
    if not quet_de_quy:
        for item in sorted(thu_muc_goc.iterdir(), key=lambda p: p.name.lower()):
            if la_tep_duoc_ho_tro(item):
                danh_sach_tep.append(item)
        return danh_sach_tep

    def _duyet(hien_tai: Path) -> None:
        for item in sorted(hien_tai.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
            if item.is_dir():
                if la_thu_muc_bi_bo_qua(item.name):
                    logger.debug("Bo qua thu muc: %s", item)
                    continue
                _duyet(item)
            elif la_tep_duoc_ho_tro(item):
                danh_sach_tep.append(item)

    _duyet(thu_muc_goc)
    return danh_sach_tep


def quet_va_doc_thu_muc(
    duong_dan_nguon: str,
    quet_de_quy: bool = True,
    gioi_han_tep: int = GIOI_HAN_SO_TEP_TOI_DA,
    gioi_han_tong_ky_tu: int = GIOI_HAN_TONG_KY_TU,
) -> dict[str, Any]:
    """Quet thu muc nguon va doc noi dung cac tep hop le.

    Tra ve dict gom trang thai, danh sach tep da doc, tep bo qua va loi neu co.
    """
    duong_dan_sach = (duong_dan_nguon or "").strip().strip('"').strip("'")
    if not duong_dan_sach:
        logger.warning("Duong dan thu muc nguon bi trong")
        return {
            "hop_le": False,
            "loi": "Chưa nhập đường dẫn thư mục nguồn.",
            "duong_dan_nguon": "",
            "tep_da_doc": [],
            "tep_bo_qua": [],
        }

    thu_muc_goc = Path(duong_dan_sach)
    if not thu_muc_goc.exists() or not thu_muc_goc.is_dir():
        logger.warning("Duong dan thu muc khong ton tai hoac khong phai thu muc: '%s'", duong_dan_sach)
        return {
            "hop_le": False,
            "loi": f"Thư mục không tồn tại hoặc không phải thư mục hợp lệ: {duong_dan_sach}",
            "duong_dan_nguon": str(thu_muc_goc),
            "tep_da_doc": [],
            "tep_bo_qua": [],
        }

    logger.info("Bat dau quet thu muc nguon: '%s' (de_quy=%s)", thu_muc_goc, quet_de_quy)
    cac_tep = _thu_thap_tep_hop_le(thu_muc_goc, quet_de_quy=quet_de_quy)

    tep_da_doc: list[dict[str, Any]] = []
    tep_bo_qua: list[dict[str, Any]] = []
    tong_ky_tu = 0

    for idx, duong_dan_tep in enumerate(cac_tep):
        if idx >= gioi_han_tep:
            tep_bo_qua.append({
                "ten_tep": duong_dan_tep.name,
                "ly_do": f"Vuot gioi han {gioi_han_tep} tep moi lan quet",
            })
            continue

        ket_qua_tep = doc_noi_dung_tep(duong_dan_tep, thu_muc_goc)
        if ket_qua_tep.get("trang_thai") != "da_doc":
            tep_bo_qua.append(ket_qua_tep)
            continue

        noi_dung_tep = ket_qua_tep.get("noi_dung", "")
        if tong_ky_tu + len(noi_dung_tep) > gioi_han_tong_ky_tu:
            con_lai = max(0, gioi_han_tong_ky_tu - tong_ky_tu)
            if con_lai == 0:
                tep_bo_qua.append({
                    "ten_tep": ket_qua_tep["ten_tep"],
                    "ly_do": f"Dat gioi han tong {gioi_han_tong_ky_tu} ky tu moi lan quet",
                })
                continue
            ket_qua_tep["noi_dung"] = noi_dung_tep[:con_lai]
            ket_qua_tep["so_ky_tu"] = con_lai
            ket_qua_tep["bi_cat_bot"] = True

        tong_ky_tu += len(ket_qua_tep.get("noi_dung", ""))
        tep_da_doc.append(ket_qua_tep)

    logger.info(
        "Hoan tat quet '%s': da_doc=%d tep, bo_qua=%d tep, tong_ky_tu=%d",
        thu_muc_goc,
        len(tep_da_doc),
        len(tep_bo_qua),
        tong_ky_tu,
    )
    return {
        "hop_le": True,
        "loi": "",
        "duong_dan_nguon": str(thu_muc_goc.resolve()),
        "tong_so_tep_da_doc": len(tep_da_doc),
        "tong_ky_tu": tong_ky_tu,
        "tep_da_doc": tep_da_doc,
        "tep_bo_qua": tep_bo_qua,
    }