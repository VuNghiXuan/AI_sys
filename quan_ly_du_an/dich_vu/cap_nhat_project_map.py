# ============================================================================
# File Path: quan_ly_du_an/dich_vu/cap_nhat_project_map.py
# Module: Tu Dong Quet Va Xuat PROJECT_MAP Ra Thu Muc Goc
# Linked Files: PROJECT_MAP.md, PROJECT_MAP_COMPACT.md, manage.py
# Purpose: Quet header file, lien ket file va so dong ma nguon de xuat
#          PROJECT_MAP.md va PROJECT_MAP_COMPACT.md ra thu muc goc du an.
# ============================================================================

from datetime import datetime
import hashlib
import logging
from pathlib import Path
import re
from typing import Any

logger = logging.getLogger(__name__)

NGUONG_CANH_BAO_DONG = 300
TEN_FILE_MAP_GOC = "PROJECT_MAP.md"
TEN_FILE_MAP_GON = "PROJECT_MAP_COMPACT.md"
THU_MUC_LOAI_TRU = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".pytest_cache",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "migrations",
    "staticfiles",
    "media",
}
PHAN_MO_RONG_QUET = {".py", ".js", ".json", ".html"}
TIEU_TO_NHOM_DIEU_PHOI = ("dieu_phoi_y_dinh/",)


def tim_goc_du_an(bat_dau: Path | None = None) -> Path:
    """Tim thu muc goc du an chua manage.py."""
    hien_tai = (bat_dau or Path(__file__)).resolve()
    for cha in [hien_tai.parent, *hien_tai.parents]:
        if (cha / "manage.py").exists():
            return cha
    return hien_tai.parents[2]


def _trich_xuat_header(noi_dung: str, duong_dan_tuong_doi: str) -> dict[str, str]:
    """Doc thong tin File Path, Module, Linked Files, Purpose tu header dau file."""
    ket_qua = {
        "file_path": duong_dan_tuong_doi,
        "module": "-",
        "linked_files": "-",
        "purpose": "-",
    }
    for dong in noi_dung.splitlines()[:15]:
        sach = re.sub(r"^(?:#|--|//|<!--)\s*", "", dong).strip()
        sach = re.sub(r"\s*-->$", "", sach).strip()
        khop = re.match(
            r"^(File Path|Module|Linked Files|Purpose)\s*:\s*(.+)$",
            sach,
            flags=re.IGNORECASE,
        )
        if khop:
            khoa = khop.group(1).lower().replace(" ", "_")
            ket_qua[khoa] = khop.group(2).strip()
    return ket_qua


def quet_danh_sach_module(goc_du_an: Path) -> list[dict[str, Any]]:
    """Quet cac file ma nguon trong du an va thong ke so dong + header."""
    danh_sach: list[dict[str, Any]] = []
    for tep in sorted(goc_du_an.rglob("*")):
        if not tep.is_file():
            continue
        if any(bo_qua in tep.parts for bo_qua in THU_MUC_LOAI_TRU):
            continue
        if tep.suffix.lower() not in PHAN_MO_RONG_QUET:
            continue

        tuong_doi = tep.relative_to(goc_du_an).as_posix()
        try:
            noi_dung = tep.read_text(encoding="utf-8", errors="replace")
        except Exception as loi:
            logger.warning("Khong doc duoc file %s: %s", tuong_doi, loi)
            continue

        so_dong = len(noi_dung.splitlines())
        header = _trich_xuat_header(noi_dung, tuong_doi)
        danh_sach.append({
            "path": tuong_doi,
            "lines": so_dong,
            "over_limit": so_dong > NGUONG_CANH_BAO_DONG,
            "module": header["module"],
            "linked_files": header["linked_files"],
            "purpose": header["purpose"],
        })
    return danh_sach


def _tao_noi_dung_map(goc_du_an: Path, cac_file: list[dict[str, Any]], thoi_gian: str) -> str:
    """Dung noi dung Markdown chi tiet cho PROJECT_MAP.md o thu muc goc."""
    canh_bao = [f for f in cac_file if f["over_limit"]]
    nhom_dieu_phoi = [f for f in cac_file if f["path"].startswith(TIEU_TO_NHOM_DIEU_PHOI)]
    dong = [
        "# PROJECT_MAP (Tự động đồng bộ)",
        "",
        f"- **Thư mục gốc:** `{goc_du_an.name}`",
        f"- **Tổng số file quét:** {len(cac_file)}",
        f"- **Số file nhóm điều phối ý định:** {len(nhom_dieu_phoi)}",
        f"- **File vượt ngưỡng >{NGUONG_CANH_BAO_DONG} dòng:** {len(canh_bao)}",
        f"- **Cập nhật lần cuối:** {thoi_gian}",
        "",
        "## Danh sách File, Liên kết & Số dòng",
        "",
        "| File | Dòng | Trạng thái | Linked Files | Chức năng |",
        "| --- | ---: | --- | --- | --- |",
    ]
    for muc in cac_file:
        trang_thai = "⚠️ >300 dòng" if muc["over_limit"] else "✅ Chuẩn"
        dong.append(
            f"| `{muc['path']}` | {muc['lines']} | {trang_thai} | {muc['linked_files']} | {muc['purpose']} |"
        )
    return "\n".join(dong) + "\n"


def _tao_noi_dung_map_gon(goc_du_an: Path, cac_file: list[dict[str, Any]], thoi_gian: str) -> str:
    """Dung ban tom tat gon nhe PROJECT_MAP_COMPACT.md o thu muc goc."""
    canh_bao = [f"`{f['path']}` ({f['lines']} dòng)" for f in cac_file if f["over_limit"]]
    dong = [
        "# PROJECT_MAP_COMPACT",
        "",
        f"- **Dự án:** `{goc_du_an.name}` | **Tổng file:** {len(cac_file)} | **Cập nhật:** {thoi_gian}",
        f"- **Cảnh báo >{NGUONG_CANH_BAO_DONG} dòng:** {', '.join(canh_bao) if canh_bao else 'Không có'}",
        "",
    ]
    for muc in cac_file:
        co_canh_bao = " [>300]" if muc["over_limit"] else ""
        dong.append(f"- `{muc['path']}` ({muc['lines']}d{co_canh_bao}) <- {muc['linked_files']}")
    return "\n".join(dong) + "\n"


def _bo_qua_dong_thoi_gian(noi_dung_md: str) -> str:
    """Loai bo dong thoi gian cap nhat de so sanh thay doi thuc su."""
    return re.sub(r"^- \*\*Cập nhật lần cuối:\*\*.*$", "", noi_dung_md, flags=re.MULTILINE).strip()


def _ghi_tep_neu_doi(dich: Path, noi_dung_moi: str) -> bool:
    """Chi ghi tep ra thu muc goc khi noi dung thuc su thay doi."""
    noi_dung_cu = dich.read_text(encoding="utf-8", errors="replace") if dich.exists() else ""
    if _bo_qua_dong_thoi_gian(noi_dung_cu) == _bo_qua_dong_thoi_gian(noi_dung_moi):
        return False
    dich.write_text(noi_dung_moi, encoding="utf-8")
    return True


def xuat_map_ra_thu_muc_goc(goc_du_an: Path | None = None) -> dict[str, Any]:
    """Quet va xuat PROJECT_MAP.md + PROJECT_MAP_COMPACT.md truc tiep ra thu muc goc."""
    goc = tim_goc_du_an(goc_du_an)
    tep_day_du = goc / TEN_FILE_MAP_GOC
    tep_gon = goc / TEN_FILE_MAP_GON

    cac_file = quet_danh_sach_module(goc)
    moc_thoi_gian = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    doi_day_du = _ghi_tep_neu_doi(tep_day_du, _tao_noi_dung_map(goc, cac_file, moc_thoi_gian))
    doi_gon = _ghi_tep_neu_doi(tep_gon, _tao_noi_dung_map_gon(goc, cac_file, moc_thoi_gian))
    da_cap_nhat = doi_day_du or doi_gon

    ma_hash = (
        hashlib.md5(tep_day_du.read_text(encoding="utf-8").encode("utf-8")).hexdigest()[:8]
        if tep_day_du.exists()
        else ""
    )
    logger.info(
        "Xuat map thu muc goc goc=%s | updated=%s | total_files=%d | hash=%s",
        goc,
        da_cap_nhat,
        len(cac_file),
        ma_hash,
    )
    return {
        "updated": da_cap_nhat,
        "root_dir": str(goc),
        "map_path": str(tep_day_du),
        "compact_map_path": str(tep_gon),
        "total_files": len(cac_file),
        "hash": ma_hash,
    }


def dong_bo_project_map_neu_can(goc_du_an: Path | None = None) -> dict[str, Any]:
    """Ham tuong thich goi tu apps.py / views_project_map.py de xuat file ra thu muc goc."""
    ket_qua = xuat_map_ra_thu_muc_goc(goc_du_an)
    ket_qua["path"] = ket_qua["map_path"]
    return ket_qua


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ket_qua_chay = xuat_map_ra_thu_muc_goc()
    logger.info("Ket qua xuat thu muc goc: %s", ket_qua_chay)