# ==============================================================================
# File Path: core/graph_query.py
# Description: Lớp truy vấn láng giềng đồ thị (tương thích ngược get_neighbors).
# Linked Files: [core/graph_indexer.py, core/jit_context.py, PROJECT_MAP.json]
# Slice Tag: [CORE: GRAPH_NEIGHBOR_QUERY]
# ==============================================================================

import logging

from core.graph_indexer import ProjectGraphIndexer

logger = logging.getLogger(__name__)


class GraphIndexer(ProjectGraphIndexer):
    """Lớp truy vấn đồ thị tương thích ngược với giao diện get_neighbors."""

    def get_neighbors(self, target_file: str, depth: int = 1) -> dict:
        """Trả về thông tin node mục tiêu và danh sách file láng giềng theo độ sâu."""
        logger.info("Truy vấn neighbors cho '%s' (depth=%d)", target_file, depth)
        project_map = self.load_or_build_map()
        nodes = project_map.get("nodes", {})
        normalized = target_file.replace("\\", "/").strip("/")
        node_info = nodes.get(normalized) or nodes.get(target_file) or {}

        impact = self.get_impact_radius(target_file=normalized, depth=depth)
        neighbors = [
            {
                "file": rel_file,
                "direction": "impacted",
                "relation": "graph_link",
                "depth": str(depth),
            }
            for rel_file in impact.get("impacted_files", [])
        ]
        return {
            "node": node_info,
            "neighbors": neighbors,
        }