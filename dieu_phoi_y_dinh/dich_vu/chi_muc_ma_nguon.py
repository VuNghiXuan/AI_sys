# ============================================================================
# File Path: dieu_phoi_y_dinh/dich_vu/chi_muc_ma_nguon.py
# Module: Chi Muc Ma Nguon Tinh, Do Thi Lien Ket & Dieu Phoi Tra Cuu Chi Tiet
# Linked Files: bo_dinh_dang_bang_ma_nguon.py, truy_van_du_lieu.py
# Purpose: Quet AST & header comment cua tung file he thong, xay dung do thi
#          lien ket 2 chieu va tra cuu ham/bien/file/bang tong hop.
# ============================================================================

import ast
import logging
from pathlib import Path
import re

from .bo_dinh_dang_bang_ma_nguon import (
    _dinh_dang_mo_ta_tung_file,
    _dinh_dang_quan_he_lien_ket,
    _tao_bang_danh_sach_ham,
    _tao_bang_so_sanh_file_va_ham,
    _tao_bang_so_sanh_ham,
    _tao_bang_tong_hop_thanh_phan,
)

logger = logging.getLogger(__name__)

_THU_MUC_LOAI_TRU = {
    ".git", ".venv", "venv", "__pycache__",
    "node_modules", "migrations", "staticfiles", "media",
}

_MAU_HEADER_MO_TA = re.compile(r"(?:Purpose|Chuc nang|Chức năng)\s*:\s*(.+)", flags=re.IGNORECASE)
_MAU_HEADER_LIEN_KET = re.compile(r"(?:Linked Files|File lien quan|File liên quan)\s*:\s*(.+)", flags=re.IGNORECASE)
_MAU_SO_SANH_PHAN_BIET = re.compile(
    r"\b(phân\s+biệt|phan\s+biet|so\s+sánh|so\s+sanh|khác\s+nhau|khac\s+nhau|giống\s+nhau|giong\s+nhau|đối\s+chiếu|doi\s+chieu)\b",
    flags=re.IGNORECASE,
)
_MAU_LAP_BANG = re.compile(
    r"\b(lập\s+bảng|lap\s+bang|tạo\s+bảng|tao\s+bang|dạng\s+bảng|dang\s+bang|kẻ\s+bảng|ke\s+bang|bảng)\b",
    flags=re.IGNORECASE,
)


def _chuan_hoa_duong_dan(goc: Path, tep: Path) -> str:
    """Chuyen Path thanh duong dan tuong doi dung dau gach cheo xuoi."""
    return str(tep.relative_to(goc)).replace("\\", "/")


def _phan_tich_header_va_mo_ta(ma_nguon: str, cay_ast: ast.AST | None) -> tuple[str, list[str]]:
    """Lay mo ta chuc nang va danh sach file lien quan tu header comment/docstring."""
    mo_ta = ""
    lien_ket_tho: list[str] = []

    for dong in "\n".join(ma_nguon.splitlines()[:25]).splitlines():
        m_mo_ta = _MAU_HEADER_MO_TA.search(dong)
        if m_mo_ta and not mo_ta:
            mo_ta = m_mo_ta.group(1).strip()

        m_lk = _MAU_HEADER_LIEN_KET.search(dong)
        if m_lk:
            for muc in re.split(r"[,;]+", m_lk.group(1)):
                ten = muc.strip().strip("`\"'")
                if ten:
                    lien_ket_tho.append(ten)

    if not mo_ta and cay_ast is not None:
        doc = (ast.get_docstring(cay_ast) or "").strip()
        if doc:
            mo_ta = doc.splitlines()[0].strip()

    return mo_ta, lien_ket_tho


def _trich_xuat_ast_python(ma_nguon: str, duong_dan_file: str) -> dict:
    """Phan tich AST file Python de lay ham, bien/hang so va import lien quan."""
    cay_ast = ast.parse(ma_nguon)
    mo_ta, lien_ket_header = _phan_tich_header_va_mo_ta(ma_nguon, cay_ast)
    ds_ham: list[dict] = []
    ds_bien: list[dict] = []
    ds_import: list[str] = list(lien_ket_header)

    for nut in cay_ast.body:
        if isinstance(nut, ast.Import):
            ds_import.extend(alias.name.split(".")[0] for alias in nut.names)
        elif isinstance(nut, ast.ImportFrom):
            if nut.module:
                ds_import.append(nut.module.lstrip("."))
            elif nut.level:
                ds_import.append("." * nut.level)
        elif isinstance(nut, (ast.FunctionDef, ast.AsyncFunctionDef)):
            doc_ham = (ast.get_docstring(nut) or "").strip()
            ds_ham.append({
                "ten": nut.name,
                "file": duong_dan_file,
                "tham_so": [a.arg for a in nut.args.args],
                "mo_ta": doc_ham.splitlines()[0].strip() if doc_ham else "Hàm xử lý cục bộ",
                "dong": nut.lineno,
            })
        elif isinstance(nut, ast.ClassDef):
            doc_lop = (ast.get_docstring(nut) or "").strip()
            ds_bien.append({
                "ten": nut.name,
                "loai": "class",
                "file": duong_dan_file,
                "mo_ta": doc_lop.splitlines()[0].strip() if doc_lop else "Lớp xử lý",
                "dong": nut.lineno,
            })
        elif isinstance(nut, (ast.Assign, ast.AnnAssign)):
            muc_tieu = nut.targets[0] if isinstance(nut, ast.Assign) and nut.targets else getattr(nut, "target", None)
            if isinstance(muc_tieu, ast.Name) and not muc_tieu.id.startswith("__"):
                ds_bien.append({
                    "ten": muc_tieu.id,
                    "loai": "bien/hang",
                    "file": duong_dan_file,
                    "mo_ta": f"Dòng {nut.lineno}",
                    "dong": nut.lineno,
                })

    return {
        "file": duong_dan_file,
        "loai_file": "python",
        "mo_ta": mo_ta or "Module Python trong hệ thống",
        "ham": ds_ham,
        "bien": ds_bien,
        "goi_y_lien_ket": list(dict.fromkeys(ds_import)),
        "so_dong": len(ma_nguon.splitlines()),
    }


def _phan_tich_file_js(ma_nguon: str, duong_dan_file: str) -> dict:
    """Phan tich co ban file JavaScript de lay mo ta, import, ham va bien."""
    mo_ta, lien_ket_header = _phan_tich_header_va_mo_ta(ma_nguon, None)
    ds_ham: list[dict] = []
    ds_bien: list[dict] = []
    ds_import: list[str] = list(lien_ket_header)

    for so_dong, dong in enumerate(ma_nguon.splitlines(), start=1):
        m_imp = re.search(r"""import\s+.*?\s+from\s+["']([^"']+)["']""", dong)
        if m_imp:
            ds_import.append(Path(m_imp.group(1)).name)
        m_fn = re.search(r"(?:async\s+)?function\s+([a-zA-Z0-9_]+)\s*\(([^)]*)\)", dong)
        if m_fn:
            ds_ham.append({
                "ten": m_fn.group(1),
                "file": duong_dan_file,
                "tham_so": [x.strip() for x in m_fn.group(2).split(",") if x.strip()],
                "mo_ta": f"Hàm JS dòng {so_dong}",
                "dong": so_dong,
            })
        m_var = re.search(r"\b(?:const|let|var)\s+([a-zA-Z0-9_]+)\s*=", dong)
        if m_var and so_dong <= 80:
            ds_bien.append({
                "ten": m_var.group(1),
                "loai": "bien_js",
                "file": duong_dan_file,
                "mo_ta": f"Biến JS dòng {so_dong}",
                "dong": so_dong,
            })

    return {
        "file": duong_dan_file,
        "loai_file": "javascript",
        "mo_ta": mo_ta or "Module giao diện JavaScript",
        "ham": ds_ham,
        "bien": ds_bien,
        "goi_y_lien_ket": list(dict.fromkeys(ds_import)),
        "so_dong": len(ma_nguon.splitlines()),
    }


def xay_dung_chi_muc_ma_nguon(goc: Path, toi_da_file: int = 80) -> dict:
    """Quet toan bo file .py/.js trong du an va xay dung chi muc + do thi 2 chieu."""
    logger.info("Bat dau xay dung chi muc ma nguon tai: %s", goc)
    cac_file: dict[str, dict] = {}
    tat_ca_ham: list[dict] = []
    tat_ca_bien: list[dict] = []

    ds_tep: list[Path] = []
    for tep in sorted(goc.rglob("*"), key=lambda p: str(p).lower()):
        if not tep.is_file():
            continue
        if any(bo_qua in tep.parts for bo_qua in _THU_MUC_LOAI_TRU) or tep.name.startswith("."):
            continue
        if tep.suffix.lower() in {".py", ".js"}:
            ds_tep.append(tep)
            if len(ds_tep) >= toi_da_file:
                break

    for tep in ds_tep:
        duong_dan = _chuan_hoa_duong_dan(goc, tep)
        try:
            ma_nguon = tep.read_text(encoding="utf-8", errors="ignore")
            thong_tin = (
                _trich_xuat_ast_python(ma_nguon, duong_dan)
                if tep.suffix.lower() == ".py"
                else _phan_tich_file_js(ma_nguon, duong_dan)
            )
            thong_tin["lien_ket_di_ra"] = []
            thong_tin["lien_ket_di_vao"] = []
            cac_file[duong_dan] = thong_tin
            tat_ca_ham.extend(thong_tin["ham"])
            tat_ca_bien.extend(thong_tin["bien"])
        except Exception as loi:
            logger.warning("Loi phan tich file %s: %s", duong_dan, loi, exc_info=True)

    danh_sach_duong_dan = list(cac_file.keys())
    for duong_dan, tt in cac_file.items():
        lien_ket_ra: list[str] = []
        for goi_y in tt.get("goi_y_lien_ket", []):
            goi_y_sach = goi_y.strip().lstrip(".").replace("\\", "/")
            if not goi_y_sach:
                continue
            for dich in danh_sach_duong_dan:
                if dich == duong_dan:
                    continue
                if (
                    dich.endswith(goi_y_sach)
                    or goi_y_sach in dich
                    or goi_y_sach == Path(dich).stem
                    or goi_y_sach == Path(dich).name
                ) and dich not in lien_ket_ra:
                    lien_ket_ra.append(dich)
        tt["lien_ket_di_ra"] = lien_ket_ra

    for duong_dan, tt in cac_file.items():
        for dich in tt["lien_ket_di_ra"]:
            if duong_dan not in cac_file[dich]["lien_ket_di_vao"]:
                cac_file[dich]["lien_ket_di_vao"].append(duong_dan)

    return {"files": cac_file, "ham": tat_ca_ham, "bien": tat_ca_bien}


def _tim_cac_file_khop(cac_file: dict[str, dict], cau_hoi_thuong: str) -> list[str]:
    """Tim danh sach duong dan file he thong duoc nhac den trong cau hoi."""
    khop: list[str] = []
    chuan_cau = cau_hoi_thuong.replace("\\", "/")
    for duong_dan in cac_file:
        ten_tep = Path(duong_dan).name.lower()
        ten_stem = Path(duong_dan).stem.lower()
        rel_lower = duong_dan.lower()
        if (
            rel_lower in chuan_cau
            or (len(ten_tep) >= 5 and ten_tep in chuan_cau)
            or (len(ten_stem) >= 4 and re.search(rf"(?<![a-z0-9_]){re.escape(ten_stem)}(?![a-z0-9_])", chuan_cau))
        ):
            khop.append(duong_dan)
    return khop


def _la_cau_hoi_tong_hop_da_thanh_phan(cau_hoi_thuong: str) -> bool:
    """Kiem tra cau hoi co nhac >= 2 loai thanh phan (app, folder, file, ham, bien/class)."""
    nhom_thanh_phan = [
        r"\b(app)\b",
        r"\b(folder|thư\s+mục|thu\s+muc)\b",
        r"\b(file|tệp|tep)\b",
        r"\b(hàm|ham)\b",
        r"\b(biến|bien|hằng|hang|class)\b",
    ]
    so_loai = sum(1 for mau in nhom_thanh_phan if re.search(mau, cau_hoi_thuong))
    return so_loai >= 2


def _dinh_dang_tra_cuu_ham_hoac_bien(chi_muc: dict, cau_hoi_thuong: str, file_khop: list[str]) -> str:
    """Tra cuu chi tiet ham hoac bien/class, hoac liet ke theo file de de doc."""
    cac_file = chi_muc.get("files", {})
    ds_ham = chi_muc.get("ham", [])
    ds_bien = chi_muc.get("bien", [])
    ham_trung = [h for h in ds_ham if re.search(rf"\b{re.escape(h['ten'].lower())}\b", cau_hoi_thuong)]
    bien_trung = [b for b in ds_bien if re.search(rf"\b{re.escape(b['ten'].lower())}\b", cau_hoi_thuong)]

    if _MAU_LAP_BANG.search(cau_hoi_thuong) and _la_cau_hoi_tong_hop_da_thanh_phan(cau_hoi_thuong):
        return _tao_bang_tong_hop_thanh_phan(chi_muc)

    if _MAU_SO_SANH_PHAN_BIET.search(cau_hoi_thuong):
        if len(file_khop) >= 2:
            return _tao_bang_so_sanh_file_va_ham(cac_file, file_khop)
        if len(ham_trung) >= 2:
            return _tao_bang_so_sanh_ham(ham_trung)

    ket_qua: list[str] = []
    if ham_trung:
        ket_qua.append("⚙️ Chi tiết hàm khớp câu hỏi:")
        for h in ham_trung[:10]:
            ts = ", ".join(h.get("tham_so", []))
            ket_qua.append(f"- `{h['ten']}({ts})` tại `{h['file']}` (dòng {h['dong']}): {h.get('mo_ta') or 'Hàm xử lý'}")

    if bien_trung:
        ket_qua.append("🧩 Chi tiết biến / class khớp câu hỏi:")
        for b in bien_trung[:12]:
            ket_qua.append(f"- `{b['ten']}` [{b['loai']}] tại `{b['file']}` (dòng {b['dong']}): {b['mo_ta']}")

    if ket_qua:
        return "\n".join(ket_qua)

    if file_khop:
        dong_loc: list[str] = []
        for f in file_khop[:6]:
            tt = cac_file[f]
            dong_loc.append(f"### `{f}` — {tt.get('mo_ta', '')}")
            for h in tt.get("ham", []):
                ts = ", ".join(h.get("tham_so", []))
                dong_loc.append(f"- `{h['ten']}({ts})` (dòng {h['dong']}): {h.get('mo_ta') or 'Hàm xử lý'}")
        return "\n".join(dong_loc)

    if re.search(r"\b(biến|bien|hằng|hang|class)\b", cau_hoi_thuong):
        nhom_bien: dict[str, list[str]] = {}
        for b in ds_bien:
            nhom_bien.setdefault(b["file"], []).append(f"`{b['ten']}` [{b['loai']}]")
        dong = [f"🧩 Danh sách biến / class theo file ({len(ds_bien)} mục):"]
        for tep, ds in list(nhom_bien.items())[:18]:
            dong.append(f"- `{tep}`: {', '.join(ds[:8])}")
        return "\n".join(dong)

    if _MAU_LAP_BANG.search(cau_hoi_thuong) and re.search(r"\b(hàm|ham)\b", cau_hoi_thuong):
        return _tao_bang_danh_sach_ham(ds_ham)

    nhom_ham: dict[str, list[str]] = {}
    for h in ds_ham:
        ts = ", ".join(h.get("tham_so", []))
        mo_ta = f" — {h['mo_ta']}" if h.get("mo_ta") else ""
        nhom_ham.setdefault(h["file"], []).append(f"`{h['ten']}({ts})`{mo_ta}")
    dong = [f"⚙️ Danh sách hàm theo file ({len(ds_ham)} hàm):"]
    for tep, ds in list(nhom_ham.items())[:18]:
        dong.append(f"- `{tep}`:\n  " + "\n  ".join(f"* {x}" for x in ds[:8]))
    return "\n".join(dong)


def truy_van_chi_tiet_ma_nguon(goc: Path, noi_dung_nhanh: str) -> str | None:
    """Xu ly cau hoi sau ve mo ta tung file, ham, bien, so sanh hoac lien ket file."""
    thuong = (noi_dung_nhanh or "").strip().lower()
    if not thuong:
        return None

    chi_muc = xay_dung_chi_muc_ma_nguon(goc)
    cac_file = chi_muc.get("files", {})
    file_khop = _tim_cac_file_khop(cac_file, thuong)

    if _MAU_LAP_BANG.search(thuong) and _la_cau_hoi_tong_hop_da_thanh_phan(thuong):
        return _tao_bang_tong_hop_thanh_phan(chi_muc)

    if _MAU_SO_SANH_PHAN_BIET.search(thuong) and len(file_khop) >= 2:
        return _tao_bang_so_sanh_file_va_ham(cac_file, file_khop)

    la_hoi_lien_ket = bool(
        re.search(r"\b(liên\s+quan|lien\s+quan|phụ\s+thuộc|phu\s+thuoc|import|gọi\s+tới|goi\s+toi)\b", thuong)
    )
    la_hoi_mo_ta_file = (
        bool(re.search(r"\b(từng\s+file|tung\s+file|mô\s+tả|mo\s+ta|chức\s+năng|chuc\s+nang)\b", thuong))
        and any(k in thuong for k in ("file", "hệ thống", "he thong", "dự án", "du an"))
    )
    la_hoi_ham_bien = bool(re.search(r"\b(hàm|ham|biến|bien|hằng|hang|tham\s+số|tham\s+so|class)\b", thuong))

    if not (la_hoi_lien_ket or la_hoi_mo_ta_file or la_hoi_ham_bien):
        return None

    if la_hoi_lien_ket:
        return _dinh_dang_quan_he_lien_ket(chi_muc, file_khop)
    if la_hoi_mo_ta_file and any(k in thuong for k in ("hàm", "ham", "từng", "tung")):
        return _dinh_dang_mo_ta_tung_file(chi_muc, goi_nhieu_ham=True)
    if la_hoi_ham_bien:
        return _dinh_dang_tra_cuu_ham_hoac_bien(chi_muc, thuong, file_khop)
    if la_hoi_mo_ta_file:
        return _dinh_dang_mo_ta_tung_file(chi_muc, goi_nhieu_ham=False)

    return None