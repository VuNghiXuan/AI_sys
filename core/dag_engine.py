"""
# File Path: core/dag_engine.py
# File Purpose: Xây dựng Blueprint-Driven DAG Engine sử dụng NetworkX để tự động 
#               bóc tách yêu cầu thành chuỗi task nguyên tử có thứ tự phụ thuộc (Hỗ trợ Multi-Intent).
# Connected Files: [core/router.py, core/code_graph.py]
# Logs: Ghi log chi tiết quá trình tạo node tác vụ, thiết lập ràng buộc thứ tự DAG và Topological Sort.
"""

import logging
import networkx as nx
from typing import Dict, List, Any

# Thiết lập hệ thống Logging tiêu chuẩn cho vnxBox
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] - %(message)s"
)
logger = logging.getLogger("vnxBox.DAGEngine")

class BlueprintDAGEngine:
    """
    # Class: BlueprintDAGEngine
    # Purpose: Quản lý và lập lịch thực thi các tác vụ dựa trên Đồ thị có hướng không có chu trình (DAG) 
    #          hỗ trợ cả đơn ý định (Single Intent) và đa ý định (Multi-Intent).
    """
    def __init__(self):
        self.dag = nx.DiGraph()
        logger.info("[DAG_ENGINE] Khởi tạo Blueprint-Driven DAG Engine (Multi-Intent Supported) thành công.")

    def build_dag_from_intent(self, intent: str, request_id: str) -> List[str]:
        """
        # Function: build_dag_from_intent
        # Purpose: Xây dựng sơ đồ DAG cho một Intent đơn lẻ.
        """
        return self.build_dag_from_multiple_intents([intent], request_id)

    def build_dag_from_multiple_intents(self, intents: List[str], request_id: str) -> List[str]:
        """
        # Function: build_dag_from_multiple_intents
        # Purpose: Tổng hợp danh sách các Multi-Intent thành một sơ đồ DAG thống nhất,
        #          khử trùng lặp node và thiết lập luồng phụ thuộc tối ưu.
        """
        logger.info(f"[DAG_ENGINE] Đang xây dựng sơ đồ Multi-Intent DAG cho Request [{request_id}] với Intents: {intents}")
        
        self.dag.clear()
        
        # Định nghĩa blueprint mẫu cho từng loại intent
        blueprints = {
            "DATABASE_DESIGN": {
                "tasks": [
                    ("Task_1_Schema", {"description": "Thiết kế cấu trúc bảng và khóa ngoại."}),
                    ("Task_2_Migration", {"description": "Sinh script Migration tương thích."})
                ],
                "edges": [("Task_1_Schema", "Task_2_Migration")]
            },
            "CODE_GENERATION": {
                "tasks": [
                    ("Task_1_Design", {"description": "Phân tích yêu cầu và thiết kế cấu trúc class/hàm."}),
                    ("Task_2_TestSchema", {"description": "Xây dựng kịch bản kiểm thử (Test Cases) trước."}),
                    ("Task_3_VibeCode", {"description": "Triển khai mã nguồn tuân thủ quy chuẩn dưới 300 dòng."})
                ],
                "edges": [
                    ("Task_1_Design", "Task_2_TestSchema"),
                    ("Task_2_TestSchema", "Task_3_VibeCode")
                ]
            },
            "TESTING_EXECUTION": {
                "tasks": [
                    ("Task_4_SandboxQC", {"description": "Chạy kiểm thử tự động trong Staging Sandbox/Venv độc lập."})
                ],
                "edges": []
            },
            "DEBUGGING_REFACTOR": {
                "tasks": [
                    ("Task_Debug_Fix", {"description": "Phân tích log lỗi và thực hiện vòng lặp tự vá code (Self-Correction)."}),
                    ("Task_4_SandboxQC", {"description": "Chạy kiểm thử lại sau khi vá lỗi."})
                ],
                "edges": [("Task_Debug_Fix", "Task_4_SandboxQC")]
            },
            "GENERAL_QUERY": {
                "tasks": [
                    ("Task_1_GeneralQuery", {"description": "Xử lý yêu cầu tổng quát từ người dùng."})
                ],
                "edges": []
            }
        }

        # Gộp các task từ các intent được phát hiện
        added_nodes = set()
        all_edges = []

        for intent in intents:
            bp = blueprints.get(intent, blueprints["GENERAL_QUERY"])
            for task_id, attr in bp["tasks"]:
                if task_id not in added_nodes:
                    self.dag.add_node(task_id, **attr)
                    added_nodes.add(task_id)
                    logger.info(f"   + Thêm Task Node: [{task_id}] - {attr['description']}")
            for source, target in bp["edges"]:
                all_edges.append((source, target))

        # Thêm các cạnh liên kết và tự động nối chuỗi tuần tự giữa các cụm task nếu có nhiều intent
        for source, target in all_edges:
            if not self.dag.has_edge(source, target):
                self.dag.add_edge(source, target)
                logger.info(f"   + Liên kết DAG nội bộ: [{source}] --> [{target}]")

        # Đảm bảo luồng chạy tuần tự hợp lý giữa các node độc lập nếu có từ 2 intent trở lên
        node_list = list(self.dag.nodes())
        for i in range(len(node_list) - 1):
            s, t = node_list[i], node_list[i+1]
            # Nếu chưa có đường đi và không tạo chu trình thì nối tiếp
            if not self.dag.has_edge(s, t) and not nx.has_path(self.dag, t, s):
                self.dag.add_edge(s, t)
                logger.info(f"   + Liên kết DAG tuần tự tự động: [{s}] --> [{t}]")

        # Kiểm tra xem đồ thị có hợp lệ không (không có chu trình - cycle)
        if not nx.is_directed_acyclic_graph(self.dag):
            logger.error("[DAG_ENGINE] Lỗi nghiêm trọng: Phát hiện chu trình (Cycle) trong sơ đồ DAG!")
            raise ValueError("DAG contains cycles!")

        # Trả về thứ tự thực thi tối ưu bằng Topological Sort
        execution_order = list(nx.topological_sort(self.dag))
        logger.info(f"[DAG_ENGINE] Thứ tự thực thi Multi-Intent chuẩn hóa (Topological Order): {execution_order}")
        
        return execution_order


if __name__ == "__main__":
    logger.info("=== BẮT ĐẦU KIỂM THỬ ĐỘC LẬP DAG ENGINE (MULTI-INTENT) ===")
    
    dag_engine = BlueprintDAGEngine()
    
    # Kiểm thử với tập Multi-Intents (Vừa viết code vừa test)
    multi_intents = ["CODE_GENERATION", "TESTING_EXECUTION"]
    order = dag_engine.build_dag_from_multiple_intents(multi_intents, request_id="REQ_DAG_MULTI_01")
    logger.info(f"Kế hoạch thực thi Multi-Intent DAG hoàn tất: {order}")
    
    logger.info("=== HOÀN TẤT KIỂM THỬ DAG ENGINE ===")