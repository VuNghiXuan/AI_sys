# ============================================================================
# File Path: dieu_phoi_y_dinh/dich_vu/thuc_thi_nhanh/do_ma_nguon_ast.py
# Module: Do Vi Tri File, Ham Va Lien Ket Ma Nguon Phuc Vu Vibe Code
# Linked Files: dieu_phoi_y_dinh/dich_vu/thuc_thi_nhanh/truy_van_db_va_ast.py,
#               dieu_phoi_y_dinh/dich_vu/thuc_thi_nhanh/trinh_xu_ly_chung.py,
#               PROJECT_MAP_COMPACT.md,
#               PROJECT_MAP.md
# Purpose: Ket hop ban do du an (PROJECT_MAP) va quet AST de tra loi chinh xac
#          vi tri file, vi tri ham/class/bien va lien ket file/ham khi vibe code.
# ============================================================================

import ast
import logging
from pathlib import Path
import re

from .truy_van_db_va_ast import THU_MUC_BO_QUA_AST, doc_tom_tat_project_map

logger = logging.getLogger(__name__)

THU_MUC_BO_QUA_MO_RONG = THU_MUC_BO_QUA_AST | {"migrations", "site-packages"}
MAX_TEP_DO_AST = 400
MAX_GOI_Y_KET_QUA = 12


def _lay_danh_sach_tep_py(goc_du_an: Path) -> list[Path]:
    """Lay danh sach tep .py, uu tien cac app cot loi truoc de khong bi cat som."""
    uu_tien_thu_muc = ("dieu_phoi_y_dinh", "quan_ly_du_an", "he_thong")
    ds_uu_tien: list[Path] = []
    ds_khac: list[Path] = []

    for tep in sorted(goc_du_an.rglob("*.py")):
        if any(part in THU_MUC_BO_QUA_MO_RONG for part in tep.parts):
            continue
        rel = tep.relative_to(goc_du_an).as_posix()
        if any(rel.startswith(f"{tm}/") for tm in uu_tien_thu_muc):
            ds_uu_tien.append(tep)
        else:
            ds_khac.append(tep)

    return (ds_uu_tien + ds_khac)[:MAX_TEP_DO_AST]


def _doc_cay_ast_an_toan(tep: Path) -> ast.Module | None:
    """Parse AST an toan cho mot tep .py."""
    try:
        return ast.parse(tep.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError as loi:
        logger.warning("Bo qua tep loi cu phap khi do AST %s: %s", tep, loi)
        return None


def _lay_dong_dau_docstring(node: ast.AST) -> str:
    """Lay dong dau docstring an toan chi cho ham/async ham/class."""
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return ""
    doc = ast.get_docstring(node)
    if not doc:
        return ""
    return doc.splitlines()[0].strip()


def _trich_tu_khoa_ky_thuat(cau_hoi: str) -> list[str]:
    """Trich cac token giong ten file/ham/module/class tu cau hoi."""
    tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_.-]{1,}", cau_hoi or "")
    loai_tru = {
        "file", "ham", "hàm", "bien", "biến", "class", "app", "model", "db",
        "nam", "nằm", "dau", "đâu", "lien", "liên", "ket", "kết", "voi", "với",
        "nao", "nào", "gi", "gì", "cho", "tôi", "tao", "mình", "minh", "anh", "em",
        "he", "hệ", "thong", "thống", "du", "dự", "an", "án", "code", "vibe",
        "phu", "phụ", "thuoc", "thuộc", "dinh", "định", "nghia", "nghĩa", "trong",
    }
    ket_qua: list[str] = []
    for tok in tokens:
        t_clean = tok.strip(".,!?:;\"'`()")
        if len(t_clean) >= 2 and t_clean.lower() not in loai_tru and t_clean not in ket_qua:
            ket_qua.append(t_clean)
    return ket_qua


def tim_vi_tri_file(goc_du_an: Path, cau_hoi: str) -> str:
    """Tim vi tri file tu PROJECT_MAP truoc, fallback quet tep thuc te tren o dia."""
    logger.info("Do vi tri file cho cau hoi: %s", cau_hoi)
    tokens = [t.lower() for t in _trich_tu_khoa_ky_thuat(cau_hoi)]
    if "setting" in (cau_hoi or "").lower():
        tokens = ["settings.py", "setting"] + tokens

    tom_tat_map = doc_tom_tat_project_map(goc_du_an)
    khop_map: list[str] = []
    if tom_tat_map and tokens:
        for dong in tom_tat_map.splitlines():
            if any(tk in dong.lower() for tk in tokens) and dong.strip():
                khop_map.append(dong.strip())
                if len(khop_map) >= MAX_GOI_Y_KET_QUA:
                    break

    khop_tep: list[str] = []
    for tep in _lay_danh_sach_tep_py(goc_du_an):
        rel = tep.relative_to(goc_du_an).as_posix()
        if tokens and any(tk in rel.lower() for tk in tokens):
            khop_tep.append(f"`{rel}`")
            if len(khop_tep) >= MAX_GOI_Y_KET_QUA:
                break

    if not khop_tep and not khop_map:
        return "Không tìm thấy file khớp tên trong bản đồ dự án hoặc mã nguồn hiện tại."

    phan_kq = ["📍 **Vị trí file tìm được:**"]
    if khop_tep:
        phan_kq.append("- **Đường dẫn mã nguồn:** " + ", ".join(khop_tep))
    if khop_map:
        phan_kq.append("- **Đối chiếu bản đồ dự án:**\n" + "\n".join(f"  {d}" for d in khop_map[:6]))
    return "\n".join(phan_kq)


def tim_vi_tri_ham_hoac_bien(goc_du_an: Path, cau_hoi: str) -> str:
    """Quet AST de tim vi tri dinh nghia ham, class hoac bien cap module."""
    logger.info("Do vi tri ham/bien AST cho cau hoi: %s", cau_hoi)
    tokens = [t.lower().rstrip("()") for t in _trich_tu_khoa_ky_thuat(cau_hoi)]
    khop_chinh_xac: list[str] = []
    khop_gan_dung: list[str] = []

    for tep in _lay_danh_sach_tep_py(goc_du_an):
        cay = _doc_cay_ast_an_toan(tep)
        if cay is None:
            continue
        rel = tep.relative_to(goc_du_an).as_posix()
        for node in cay.body:
            ten_node = ""
            loai_node = ""
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                ten_node, loai_node = node.name, "hàm"
            elif isinstance(node, ast.ClassDef):
                ten_node, loai_node = node.name, "class"
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and not target.id.startswith("__"):
                        ten_node, loai_node = target.id, "biến"
                        break
            if not ten_node:
                continue
            doc = _lay_dong_dau_docstring(node)
            dong_kq = (
                f"- `{rel}` (dòng {node.lineno}): `{ten_node}` ({loai_node})"
                + (f" — {doc}" if doc else "")
            )
            ten_th = ten_node.lower()
            if tokens and any(tk == ten_th for tk in tokens):
                khop_chinh_xac.append(dong_kq)
            elif not tokens or any(tk in ten_th for tk in tokens):
                if len(khop_gan_dung) < MAX_GOI_Y_KET_QUA:
                    khop_gan_dung.append(dong_kq)

    ds_chon = khop_chinh_xac or khop_gan_dung
    if not ds_chon:
        return "Không tìm thấy hàm, class hoặc biến khớp trong AST dự án."
    return "🔎 **Vị trí định nghĩa trong mã nguồn (AST):**\n" + "\n".join(ds_chon[:MAX_GOI_Y_KET_QUA])


def _lay_ten_ham_goi(node: ast.AST) -> list[str]:
    """Lay danh sach ten ham duoc goi ben trong mot AST node."""
    ten_goi: list[str] = []
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call):
            if isinstance(sub.func, ast.Name) and sub.func.id not in ten_goi:
                ten_goi.append(sub.func.id)
            elif isinstance(sub.func, ast.Attribute) and sub.func.attr not in ten_goi:
                ten_goi.append(sub.func.attr)
    return ten_goi


def _tim_ham_lien_ket(
    tep_py: list[Path],
    tokens: list[str],
    khop_chinh_xac: bool,
) -> tuple[Path, ast.FunctionDef | ast.AsyncFunctionDef] | None:
    """Tim ham AST theo ten chinh xac truoc, sau do moi khop gan dung."""
    if not tokens:
        return None
    for tep in tep_py:
        cay = _doc_cay_ast_an_toan(tep)
        if cay is None:
            continue
        for node in cay.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                ten_th = node.name.lower()
                trung = (ten_th in tokens) if khop_chinh_xac else any(tk in ten_th for tk in tokens)
                if trung:
                    return tep, node
    return None


def phan_tich_lien_ket_file_va_ham(goc_du_an: Path, cau_hoi: str) -> str:
    """Tra loi lien ket 2 chieu cua file (Linked Files + import) va ham (goi/duoc goi)."""
    logger.info("Phan tich lien ket file & ham cho cau hoi: %s", cau_hoi)
    tokens = [t.lower().rstrip("()") for t in _trich_tu_khoa_ky_thuat(cau_hoi)]
    tep_py = _lay_danh_sach_tep_py(goc_du_an)

    # 1. Uu tien khop ten ham khi cau hoi nhac den ham
    if any(w in (cau_hoi or "").lower() for w in ("hàm ", "ham ", "hàm(", "ham(")):
        tim_duoc = _tim_ham_lien_ket(tep_py, tokens, True) or _tim_ham_lien_ket(tep_py, tokens, False)
        if tim_duoc:
            tep, node = tim_duoc
            rel = tep.relative_to(goc_du_an).as_posix()
            ham_goi_ra = _lay_ten_ham_goi(node)[:10]
            noi_goi_vao: list[str] = []
            for tep_khac in tep_py:
                cay_khac = _doc_cay_ast_an_toan(tep_khac)
                if not cay_khac:
                    continue
                rel_khac = tep_khac.relative_to(goc_du_an).as_posix()
                for n2 in ast.walk(cay_khac):
                    if isinstance(n2, ast.Call):
                        ten_c = n2.func.id if isinstance(n2.func, ast.Name) else (n2.func.attr if isinstance(n2.func, ast.Attribute) else "")
                        if ten_c == node.name:
                            noi_goi_vao.append(f"`{rel_khac}`")
                            break
            return "\n".join([
                f"🔗 **Liên kết của hàm `{node.name}()` tại `{rel}`:**",
                f"- **Các hàm/lời gọi bên trong:** {', '.join(f'`{g}()`' for g in ham_goi_ra) or 'Không có'}",
                f"- **Các file có tham chiếu/gọi tới:** {', '.join(noi_goi_vao[:10]) or 'Chưa thấy lời gọi trực tiếp'}",
            ])

    # 2. Kiem tra lien ket file theo 3 muc uu tien: ten chuan -> stem chua -> duong dan
    stems_tk = [tk[:-3] if tk.endswith(".py") else tk for tk in tokens]
    tep_khop: Path | None = None

    for tep in tep_py:
        ten_tep = tep.name.lower()
        stem_tep = tep.stem.lower()
        if any(tk == ten_tep or s == stem_tep for tk, s in zip(tokens, stems_tk)):
            tep_khop = tep
            break

    if tep_khop is None:
        for tep in tep_py:
            stem_tep = tep.stem.lower()
            if any(s and s in stem_tep for s in stems_tk):
                tep_khop = tep
                break

    if tep_khop is None:
        for tep in tep_py:
            rel = tep.relative_to(goc_du_an).as_posix().lower()
            if any(s and s in rel for s in stems_tk):
                tep_khop = tep
                break

    if tep_khop is not None:
        rel = tep_khop.relative_to(goc_du_an).as_posix()
        tho = tep_khop.read_text(encoding="utf-8", errors="replace")
        linked_header = ""
        for dong in tho.splitlines()[:15]:
            if "linked files:" in dong.lower():
                linked_header = dong.split(":", 1)[-1].strip()
                break
        cay = _doc_cay_ast_an_toan(tep_khop)
        imports: list[str] = []
        if cay:
            for node in cay.body:
                if isinstance(node, ast.ImportFrom) and node.module:
                    imports.append(f"`{node.module}`")
                elif isinstance(node, ast.Import):
                    imports.extend(f"`{alias.name}`" for alias in node.names)
        return "\n".join([
            f"🔗 **Liên kết của file `{rel}`:**",
            f"- **Linked Files (header):** {linked_header or 'Không khai báo'}",
            f"- **Import / phụ thuộc:** {', '.join(imports[:12]) or 'Không có'}",
        ])