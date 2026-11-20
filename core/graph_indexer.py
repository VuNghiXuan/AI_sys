# ==============================================================================
# File Path: core/graph_indexer.py
# Description: Quét AST mã nguồn Python, sinh PROJECT_MAP.json & tính Impact Radius.
# Linked Files: [core/logger_setup.py, core/graph_query.py, PROJECT_MAP.json]
# Slice Tag: [CORE: AST_GRAPH_INDEXER]
# ==============================================================================

import ast
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

from core.logger_setup import setup_logger

logger = logging.getLogger(__name__)

SKIP_DIRS = {
    ".venv",
    "venv",
    "__pycache__",
    ".git",
    ".pytest_cache",
    "node_modules",
    "migrations",
    "logs",
}

HEADER_LINKED_PATTERN = re.compile(r"Linked Files:\s*\[([^\]]*)\]", re.IGNORECASE)
HEADER_SLICE_PATTERN = re.compile(r"Slice Tag:\s*\[([^\]]*)\]", re.IGNORECASE)


def _count_lines(file_path: Path) -> int:
    """Đếm số dòng của file văn bản an toàn."""
    with file_path.open("r", encoding="utf-8", errors="replace") as f:
        return sum(1 for _ in f)


def _parse_header_metadata(content: str) -> tuple[list[str], str]:
    """Đọc Linked Files và Slice Tag từ phần comment đầu file nếu có."""
    linked_files: list[str] = []
    linked_match = HEADER_LINKED_PATTERN.search(content)
    if linked_match:
        raw_items = linked_match.group(1).split(",")
        linked_files = [item.strip().strip("'\"") for item in raw_items if item.strip()]

    slice_tag = ""
    slice_match = HEADER_SLICE_PATTERN.search(content)
    if slice_match:
        slice_tag = slice_match.group(1).strip()

    return linked_files, slice_tag


def _extract_ast_symbols(content: str, file_rel_path: str) -> tuple[list[str], list[str], list[str]]:
    """Dùng AST trích xuất imports, classes và top-level functions."""
    imports: list[str] = []
    classes: list[str] = []
    functions: list[str] = []

    try:
        tree = ast.parse(content, filename=file_rel_path)
    except SyntaxError as exc:
        logger.warning("Lỗi cú pháp AST tại %s: %s", file_rel_path, exc)
        return imports, classes, functions

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            for alias in node.names:
                imports.append(f"{mod}.{alias.name}" if mod else alias.name)

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            classes.append(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)

    return sorted(set(imports)), sorted(set(classes)), sorted(set(functions))


class ProjectGraphIndexer:
    """Quét thư mục dự án, lưu PROJECT_MAP.json và tính Impact Radius."""

    def __init__(self, project_root: str = ".", map_file: str = "PROJECT_MAP.json") -> None:
        self.project_root = Path(project_root).resolve()
        self.map_path = (self.project_root / map_file).resolve()

    def _to_rel_posix(self, path: Path) -> str:
        """Chuẩn hóa đường dẫn tương đối kiểu POSIX để đồng bộ giữa các máy."""
        return path.resolve().relative_to(self.project_root).as_posix()

    def _iter_python_files(self) -> list[Path]:
        """Liệt kê toàn bộ file .py hợp lệ, bỏ qua thư mục hệ thống/cache."""
        py_files: list[Path] = []
        for path in self.project_root.rglob("*.py"):
            rel_parts = set(path.relative_to(self.project_root).parts)
            if rel_parts & SKIP_DIRS:
                continue
            py_files.append(path)
        return sorted(py_files)

    def build_map(self, max_lines_limit: int = 300) -> dict:
        """Quét toàn bộ file Python và ghi ra PROJECT_MAP.json."""
        logger.info("Bắt đầu quét AST dự án tại: %s", self.project_root)
        py_files = self._iter_python_files()

        nodes: dict[str, dict] = {}
        edges: list[dict] = []
        oversized_files: list[dict] = []

        for file_path in py_files:
            rel_path = self._to_rel_posix(file_path)
            content = file_path.read_text(encoding="utf-8", errors="replace")
            line_count = _count_lines(file_path)
            header_links, slice_tag = _parse_header_metadata(content)
            imports, classes, functions = _extract_ast_symbols(content, rel_path)

            is_oversized = line_count > max_lines_limit
            if is_oversized:
                oversized_files.append({"file": rel_path, "lines": line_count})

            nodes[rel_path] = {
                "path": rel_path,
                "lines": line_count,
                "oversized": is_oversized,
                "slice_tag": slice_tag,
                "classes": classes,
                "functions": functions,
                "imports": imports,
                "header_linked_files": header_links,
            }

            for target in header_links:
                edges.append({"from": rel_path, "to": target, "type": "header_link"})
            for imp in imports:
                edges.append({"from": rel_path, "to": imp, "type": "ast_import"})

        project_map = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "project_root": str(self.project_root),
            "max_lines_limit": max_lines_limit,
            "summary": {
                "total_py_files": len(nodes),
                "total_edges": len(edges),
                "oversized_count": len(oversized_files),
            },
            "oversized_files": oversized_files,
            "nodes": nodes,
            "edges": edges,
        }

        try:
            self.map_path.write_text(
                json.dumps(project_map, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            logger.info(
                "Đã xuất %s: %d file Python, %d liên kết, %d file vượt %d dòng.",
                self.map_path.name,
                len(nodes),
                len(edges),
                len(oversized_files),
                max_lines_limit,
            )
        except OSError as exc:
            logger.error("Lỗi ghi file %s: %s", self.map_path, exc, exc_info=True)
            raise

        return project_map

    def load_or_build_map(self) -> dict:
        """Đọc PROJECT_MAP.json nếu đã có, chưa có thì tự quét tạo mới."""
        if self.map_path.exists():
            return json.loads(self.map_path.read_text(encoding="utf-8"))
        return self.build_map()

    def get_impact_radius(self, target_file: str, depth: int = 1) -> dict:
        """Tính danh sách file liên quan trực tiếp (và theo độ sâu) quanh target_file."""
        project_map = self.load_or_build_map()
        nodes = project_map.get("nodes", {})
        edges = project_map.get("edges", [])

        normalized_target = target_file.replace("\\", "/").strip("/")
        logger.info("Tính Impact Radius cho '%s' (depth=%d)", normalized_target, depth)

        visited = {normalized_target}
        frontier = {normalized_target}
        impacted_order: list[str] = []

        for _ in range(max(1, depth)):
            next_frontier: set[str] = set()
            for current in frontier:
                current_node = nodes.get(current, {})
                for linked in current_node.get("header_linked_files", []):
                    if linked not in visited:
                        visited.add(linked)
                        next_frontier.add(linked)
                        impacted_order.append(linked)

                for edge in edges:
                    src = edge.get("from", "")
                    dst = edge.get("to", "")
                    if src == current and dst.endswith(".py") and dst not in visited:
                        visited.add(dst)
                        next_frontier.add(dst)
                        impacted_order.append(dst)
                    elif dst == current and src and src not in visited:
                        visited.add(src)
                        next_frontier.add(src)
                        impacted_order.append(src)

                current_stem = Path(current).stem
                for candidate_path, candidate_info in nodes.items():
                    if candidate_path in visited:
                        continue
                    imp_text = " ".join(candidate_info.get("imports", []))
                    hdr_text = " ".join(candidate_info.get("header_linked_files", []))
                    if current_stem and (current_stem in imp_text or current in hdr_text):
                        visited.add(candidate_path)
                        next_frontier.add(candidate_path)
                        impacted_order.append(candidate_path)

            frontier = next_frontier

        existing_impacted = [f for f in impacted_order if f in nodes]
        logger.info(
            "Impact Radius của '%s': %d file tồn tại trên đĩa -> %s",
            normalized_target,
            len(existing_impacted),
            existing_impacted,
        )
        return {
            "target_file": normalized_target,
            "depth": depth,
            "impacted_files": existing_impacted,
            "all_referenced": impacted_order,
        }


if __name__ == "__main__":
    setup_logger("vnxbox")
    indexer = ProjectGraphIndexer(project_root=".")
    result = indexer.build_map()
    summary = result.get("summary", {})
    print(
        f"[OK] Đã cập nhật PROJECT_MAP.json | "
        f"Files: {summary.get('total_py_files')} | "
        f"Edges: {summary.get('total_edges')} | "
        f"Oversized: {summary.get('oversized_count')}"
    )