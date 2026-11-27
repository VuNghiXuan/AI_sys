# ============================================================================
# File Path: code_map/sitter_index.py
# Module: Chi Muc Cau Truc Ma Nguon Bang Tree-sitter Va Lien Ket Tep
# Linked Files: core_policy/loader.py,
#               code_map/scanner.py,
#               code_map/context_builder.py
# Purpose: Trich xuat symbol (class, ham, bien), dong bat dau/ket thuc va
#          quan he import/phu thuoc giua cac tep qua Tree-sitter (co AST fallback).
# ============================================================================

from __future__ import annotations

import ast
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

from core_policy.loader import FileLimitConfig, tai_cau_hinh_chien_thuat

from .scanner import quet_danh_sach_tep

logger = logging.getLogger(__name__)

NGON_NGU_THEO_DUOI: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".html": "html",
    ".css": "css",
    ".sql": "sql",
    ".json": "json",
}

MAU_IMPORT_TEXT = re.compile(
    r"""(?:^\s*(?:from|import)\s+([\w.]+)|import\s+.*?from\s+['"]([^'"]+)['"]|require\(\s*['"]([^'"]+)['"]\s*\))""",
    re.MULTILINE,
)


@dataclass
class KyHieuCode:
    """Dai dien mot ham, class hoac dinh nghia chinh trong tep."""

    ten: str
    loai: str
    dong_bat_dau: int
    dong_ket_thuc: int


@dataclass
class BanGhiTepCode:
    """Chi muc cau truc va lien ket cua mot tep ma nguon."""

    duong_dan: str
    ngon_ngu: str
    so_dong: int
    ky_hieu: list[KyHieuCode] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    imported_by: list[str] = field(default_factory=list)


def _lay_parser_tree_sitter(ngon_ngu: str):
    """Thu khoi tao parser Tree-sitter neu thu vien grammar kha dung."""
    try:
        from tree_sitter_language_pack import get_parser  # type: ignore

        return get_parser(ngon_ngu)
    except Exception:
        return None


def _trich_ast_python(ma_nguon: str) -> tuple[list[KyHieuCode], list[str]]:
    """Phan tich nhanh Python bang ast chuan khi khong dung parser ngoai."""
    ky_hieu: list[KyHieuCode] = []
    imports: list[str] = []
    try:
        cay = ast.parse(ma_nguon)
    except SyntaxError:
        return ky_hieu, imports

    for node in ast.walk(cay):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            loai = "async_function" if isinstance(node, ast.AsyncFunctionDef) else "function"
            ky_hieu.append(
                KyHieuCode(
                    ten=node.name,
                    loai=loai,
                    dong_bat_dau=getattr(node, "lineno", 1),
                    dong_ket_thuc=getattr(node, "end_lineno", getattr(node, "lineno", 1)),
                )
            )
        elif isinstance(node, ast.ClassDef):
            ky_hieu.append(
                KyHieuCode(
                    ten=node.name,
                    loai="class",
                    dong_bat_dau=getattr(node, "lineno", 1),
                    dong_ket_thuc=getattr(node, "end_lineno", getattr(node, "lineno", 1)),
                )
            )
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)

    return ky_hieu, sorted(set(imports))


def _duyet_node_tree_sitter(node, ma_bytes: bytes, ky_hieu: list[KyHieuCode], do_sau: int = 0) -> None:
    """Duyet cay cu phap Tree-sitter de gom cac node dinh nghia ham/class/component."""
    if do_sau > 10:
        return
    loai_node = getattr(node, "type", "")
    if loai_node in {
        "function_definition",
        "async_function_definition",
        "class_definition",
        "method_definition",
        "function_declaration",
    }:
        ten = ""
        for child in getattr(node, "children", []):
            if "identifier" in getattr(child, "type", ""):
                ten = ma_bytes[child.start_byte:child.end_byte].decode("utf-8", errors="ignore").strip()
                if ten:
                    break
        if ten:
            ky_hieu.append(
                KyHieuCode(
                    ten=ten,
                    loai=loai_node,
                    dong_bat_dau=node.start_point[0] + 1,
                    dong_ket_thuc=node.end_point[0] + 1,
                )
            )
    for child in getattr(node, "children", []):
        _duyet_node_tree_sitter(child, ma_bytes, ky_hieu, do_sau + 1)


def _trich_imports_text(ma_nguon: str) -> list[str]:
    """Trich cac module/duong dan import co ban tu van ban ma nguon."""
    ds: list[str] = []
    for match in MAU_IMPORT_TEXT.finditer(ma_nguon):
        target = next((g for g in match.groups() if g), "")
        if target:
            ds.append(target)
    return sorted(set(ds))


def lap_ban_do_repo(
    goc_du_an: str | Path,
    max_tep: int = 250,
    file_limits: FileLimitConfig | None = None,
) -> dict[str, BanGhiTepCode]:
    """Lap chi muc cau truc cac tep ma nguon va quan he import hai chieu."""
    goc = Path(goc_du_an).resolve()
    limits = file_limits or tai_cau_hinh_chien_thuat().file_limits
    ds_tep = quet_danh_sach_tep(
        goc_du_an=goc,
        duoi_file=list(NGON_NGU_THEO_DUOI.keys()),
        gioi_han_tep=max_tep,
        file_limits=limits,
    )

    ban_do: dict[str, BanGhiTepCode] = {}
    parser_cache: dict[str, object] = {}

    for item in ds_tep:
        ngon_ngu = NGON_NGU_THEO_DUOI.get(item.phan_mo_rong, "text")
        tep_day_du = goc / item.duong_dan_tuong_doi
        try:
            noi_dung = tep_day_du.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        ky_hieu: list[KyHieuCode] = []
        imports: list[str] = []

        if ngon_ngu not in parser_cache:
            parser_cache[ngon_ngu] = _lay_parser_tree_sitter(ngon_ngu)
        parser = parser_cache[ngon_ngu]

        if parser is not None:
            ma_bytes = noi_dung.encode("utf-8", errors="ignore")
            tree = parser.parse(ma_bytes)
            _duyet_node_tree_sitter(tree.root_node, ma_bytes, ky_hieu)
            imports = _trich_imports_text(noi_dung)
        elif ngon_ngu == "python":
            ky_hieu, imports = _trich_ast_python(noi_dung)
        else:
            imports = _trich_imports_text(noi_dung)

        ban_do[item.duong_dan_tuong_doi] = BanGhiTepCode(
            duong_dan=item.duong_dan_tuong_doi,
            ngon_ngu=ngon_ngu,
            so_dong=item.so_dong,
            ky_hieu=ky_hieu,
            imports=imports,
        )

    # Xay dung quan he imported_by dua tren ten module/duong dan
    all_keys = list(ban_do.keys())
    for rel, ghi in ban_do.items():
        for imp in ghi.imports:
            imp_path = imp.replace(".", "/")
            for ung_vien in all_keys:
                if ung_vien == rel:
                    continue
                if imp_path in ung_vien or Path(ung_vien).stem == imp.split(".")[-1]:
                    if rel not in ban_do[ung_vien].imported_by:
                        ban_do[ung_vien].imported_by.append(rel)

    logger.debug("Da lap ban do Tree-sitter/AST cho %d tep", len(ban_do))
    return ban_do