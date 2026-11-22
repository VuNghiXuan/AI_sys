# ============================================================================
# File Path: dieu_phoi_y_dinh/dich_vu/truy_van_du_lieu.py
# Module: Truy Van Du Lieu DB & File Cho Nhanh Dieu Phoi
# Linked Files: dieu_phoi_nhanh.py, cau_noi_dieu_phoi.py, chi_muc_ma_nguon.py
# Purpose: Quet thuc te cau truc folder, app, file, class, ham, bien, mo ta
#          chuc nang tung file va quan he lien ket 2 chieu trong du an AI_sys.
# ============================================================================

import ast
import logging
from pathlib import Path
import re

from .chi_muc_ma_nguon import truy_van_chi_tiet_ma_nguon

logger = logging.getLogger(__name__)

_THU_MUC_LOAI_TRU = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    "migrations",
    "staticfiles",
    "media",
}


def _lay_goc_du_an() -> Path:
    """Xac dinh thu muc goc du an (thu muc chua manage.py neu co)."""
    hien_tai = Path(__file__).resolve()
    for cha in [hien_tai.parent, *hien_tai.parents]:
        if (cha / "manage.py").exists():
            return cha
    return hien_tai.parents[2]


def _quet_folder_app_va_file(goc: Path, toi_da_file: int = 50) -> tuple[list[str], list[str], list[str]]:
    """Liet ke thu muc (folder), app Django va danh sach file .py/.js/.html."""
    ds_folder: list[str] = []
    ds_app: list[str] = []
    ds_file: list[str] = []

    for thu_muc in sorted(goc.rglob("*"), key=lambda p: str(p).lower()):
        if not thu_muc.is_dir():
            continue
        if any(bo_qua in thu_muc.parts for bo_qua in _THU_MUC_LOAI_TRU) or thu_muc.name.startswith("."):
            continue
        rel_folder = str(thu_muc.relative_to(goc)).replace("\\", "/")
        ds_folder.append(rel_folder)
        if thu_muc.parent == goc and (
            (thu_muc / "apps.py").exists()
            or (thu_muc / "models.py").exists()
            or (thu_muc / "views.py").exists()
        ):
            ds_app.append(thu_muc.name)

    for tep in sorted(goc.rglob("*"), key=lambda p: str(p).lower()):
        if not tep.is_file():
            continue
        if any(bo_qua in tep.parts for bo_qua in _THU_MUC_LOAI_TRU):
            continue
        if tep.suffix.lower() in {".py", ".js", ".html"}:
            ds_file.append(str(tep.relative_to(goc)).replace("\\", "/"))
            if len(ds_file) >= toi_da_file:
                break

    return ds_folder, ds_app, ds_file


def _quet_class_va_ham_python(goc: Path, toi_da_tep: int = 40) -> tuple[list[str], list[str]]:
    """Trich xuat ten class va ham top-level tu cac file .py trong du an."""
    ds_class: list[str] = []
    ds_ham: list[str] = []
    so_tep = 0

    for tep in sorted(goc.rglob("*.py"), key=lambda p: str(p).lower()):
        if any(bo_qua in tep.parts for bo_qua in _THU_MUC_LOAI_TRU):
            continue
        so_tep += 1
        if so_tep > toi_da_tep:
            break
        try:
            ma_nguon = tep.read_text(encoding="utf-8", errors="ignore")
            cay_ast = ast.parse(ma_nguon)
            ten_tep = tep.name
            for nut in cay_ast.body:
                if isinstance(nut, ast.ClassDef):
                    ds_class.append(f"{nut.name} ({ten_tep})")
                elif isinstance(nut, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not nut.name.startswith("_"):
                        ds_ham.append(f"{nut.name}() ({ten_tep})")
        except SyntaxError:
            continue
        except Exception as loi:
            logger.debug("Bo qua file %s khi quet AST: %s", tep, loi)

    return ds_class, ds_ham


def _quet_model_va_bang_db() -> list[str]:
    """Doc danh sach model & ten bang DB tu Django apps registry."""
    ds_model: list[str] = []
    try:
        from django.apps import apps

        for model in apps.get_models():
            app_label = model._meta.app_label
            if app_label in {"admin", "auth", "contenttypes", "sessions"}:
                continue
            ds_model.append(f"{app_label}.{model.__name__} -> {model._meta.db_table}")
    except Exception as loi:
        logger.debug("Khong doc duoc Django models: %s", loi)
    return ds_model


def thuc_hien_truy_van_db_va_file(noi_dung_nhanh: str, ngu_canh: dict | None = None) -> dict:
    """Thuc hien truy van cau truc, chi tiet ham/bien, mo ta file va lien ket file."""
    ngu_canh = ngu_canh or {}
    thuong = (noi_dung_nhanh or "").strip().lower()
    logger.info(
        "Goi thuc_hien_truy_van_db_va_file (do_dai_nhanh=%d, keys_ngu_canh=%s)",
        len(noi_dung_nhanh or ""),
        list(ngu_canh.keys()),
    )

    try:
        goc = _lay_goc_du_an()

        noi_dung_chi_tiet = truy_van_chi_tiet_ma_nguon(goc, noi_dung_nhanh)
        if noi_dung_chi_tiet:
            return {
                "ok": True,
                "co_du_lieu": True,
                "thong_diep": noi_dung_chi_tiet,
                "noi_dung": noi_dung_chi_tiet,
            }

        ds_folder, ds_app, ds_file = _quet_folder_app_va_file(goc)
        ds_class, ds_ham = _quet_class_va_ham_python(goc)
        ds_model = _quet_model_va_bang_db()

        hoi_folder = bool(re.search(r"\b(folder|thư\s+mục|thu\s+muc|cấu\s+trúc|cau\s+truc)\b", thuong))
        hoi_file = bool(re.search(r"\b(file|tệp|tep|app)\b", thuong))
        hoi_class = bool(re.search(r"\b(class|lớp|lop|model|bảng|bang|db|database)\b", thuong))
        hoi_ham = bool(re.search(r"\b(hàm|ham|function|def)\b", thuong))

        if not (hoi_folder or hoi_file or hoi_class or hoi_ham):
            hoi_folder = hoi_file = hoi_class = hoi_ham = True

        cac_muc: list[str] = []

        if hoi_folder and ds_folder:
            cac_muc.append(f"📁 Folder ({len(ds_folder)}):\n- " + "\n- ".join(ds_folder[:20]))

        if hoi_file:
            if ds_app:
                cac_muc.append(f"🧩 App ({len(ds_app)}):\n- " + "\n- ".join(ds_app))
            if ds_file:
                cac_muc.append(f"📄 File ({len(ds_file)}):\n- " + "\n- ".join(ds_file[:20]))

        if hoi_class:
            if ds_model:
                cac_muc.append(f"🗄️ Model/DB ({len(ds_model)}):\n- " + "\n- ".join(ds_model[:12]))
            if ds_class:
                cac_muc.append(f"🏛️ Class ({len(ds_class)}):\n- " + "\n- ".join(ds_class[:15]))

        if hoi_ham and ds_ham:
            cac_muc.append(f"⚙️ Hàm ({len(ds_ham)}):\n- " + "\n- ".join(ds_ham[:20]))

        co_du_lieu = bool(cac_muc)
        thong_diep = (
            "\n\n".join(cac_muc)
            if co_du_lieu
            else f"Không tìm thấy thông tin cấu trúc phù hợp cho: '{noi_dung_nhanh}'."
        )

        return {
            "ok": True,
            "co_du_lieu": co_du_lieu,
            "thong_diep": thong_diep,
            "noi_dung": thong_diep,
            "tong_quan": {
                "goc_du_an": str(goc),
                "so_folder": len(ds_folder),
                "so_app": len(ds_app),
                "so_file": len(ds_file),
                "so_class": len(ds_class),
                "so_ham": len(ds_ham),
                "so_model": len(ds_model),
            },
        }
    except Exception as loi:
        logger.error("Loi thuc_hien_truy_van_db_va_file: %s", loi, exc_info=True)
        return {
            "ok": False,
            "co_du_lieu": False,
            "thong_diep": f"Lỗi khi truy vấn file/DB: {loi}",
            "noi_dung": "",
            "loi": str(loi),
        }