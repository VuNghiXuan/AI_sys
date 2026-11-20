# ==============================================================================
# File Path: core/jit_context.py
# Description: Gom ngữ cảnh JIT Context gọn nhẹ theo Impact Radius từ PROJECT_MAP.
# Linked Files: [core/graph_indexer.py, core/graph_query.py, core/logger_setup.py, PROJECT_MAP.json]
# Slice Tag: [CORE: JIT_CONTEXT_BUILDER]
# ==============================================================================

import logging
from pathlib import Path

from core.graph_indexer import ProjectGraphIndexer

logger = logging.getLogger(__name__)


class JITContextBuilder:
    """Nạp đúng file liên quan trong Impact Radius với giới hạn ký tự an toàn."""

    def __init__(
        self,
        project_root: str = ".",
        map_file: str = "PROJECT_MAP.json",
        max_total_chars: int = 24000,
    ) -> None:
        self.project_root = Path(project_root).resolve()
        self.indexer = ProjectGraphIndexer(project_root=str(self.project_root), map_file=map_file)
        self.max_total_chars = max_total_chars

    def build_context(
        self,
        target_file: str,
        depth: int = 1,
        extra_notes: str = "",
    ) -> dict:
        """Trả về gói ngữ cảnh gọn gồm file đích + các file liên quan trực tiếp."""
        impact = self.indexer.get_impact_radius(target_file=target_file, depth=depth)
        ordered_files = [impact["target_file"]] + [
            f for f in impact["impacted_files"] if f != impact["target_file"]
        ]

        sections: list[str] = []
        included_files: list[str] = []
        skipped_files: list[str] = []
        used_chars = 0

        if extra_notes:
            note_block = f"### GHI CHÚ / LOG NGỮ CẢNH\n{extra_notes.strip()}\n"
            sections.append(note_block)
            used_chars += len(note_block)

        for rel_path in ordered_files:
            full_path = (self.project_root / rel_path).resolve()
            if not full_path.exists() or not full_path.is_file():
                continue

            content = full_path.read_text(encoding="utf-8", errors="replace")
            block = f"### FILE: {rel_path}\n```python\n{content}\n```\n"

            if used_chars + len(block) > self.max_total_chars and included_files:
                skipped_files.append(rel_path)
                continue

            sections.append(block)
            included_files.append(rel_path)
            used_chars += len(block)

        logger.info(
            "JIT Context cho '%s': nạp %d file (%d/%d ký tự), bỏ qua %d file.",
            target_file,
            len(included_files),
            used_chars,
            self.max_total_chars,
            len(skipped_files),
        )
        return {
            "target_file": impact["target_file"],
            "included_files": included_files,
            "skipped_files": skipped_files,
            "char_count": used_chars,
            "context_text": "\n".join(sections),
        }