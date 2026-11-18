"""
# File Path: core/router.py
# File Purpose: Tiếp nhận yêu cầu người dùng, sử dụng Pydantic v2 chuẩn hóa cấu trúc dữ liệu,
#               và hỗ trợ phân loại Đa ý định (Multi-Intent Routing) trước khi chuyển giao cho DAG Engine.
# Connected Files: [core/code_graph.py, core/dag_engine.py]
# Logs: Ghi log chi tiết quá trình kiểm định Pydantic, phân loại multi-intent và lỗi định dạng dữ liệu.
"""

import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, ValidationError

# Thiết lập hệ thống Logging tiêu chuẩn cho vnxBox
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] - %(message)s"
)
logger = logging.getLogger("vnxBox.IntentRouter")

class UserRequestPayload(BaseModel):
    """
    # Class: UserRequestPayload
    # Purpose: Sử dụng Pydantic v2 để định nghĩa schema chuẩn hóa cho yêu cầu từ người dùng.
    """
    request_id: str = Field(..., description="Mã định danh duy nhất của yêu cầu.")
    raw_prompt: str = Field(..., min_length=3, description="Nội dung yêu cầu thô từ người dùng.")
    target_module: Optional[str] = Field(default="general", description="Module mục tiêu nếu được chỉ định.")
    priority: int = Field(default=1, ge=1, le=5, description="Mức độ ưu tiên từ 1 (thấp) đến 5 (khẩn cấp).")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Thông tin phụ trợ mở rộng.")


class IntentRouter:
    """
    # Class: IntentRouter
    # Purpose: Phân tích và định tuyến đa ý định (Multi-Intent) dựa trên từ khóa hoặc nội dung yêu cầu.
    """
    def __init__(self):
        logger.info("[INTENT_ROUTER] Khởi tạo Intent Router (Multi-Intent Supported) thành công.")

    def classify_intents(self, payload: UserRequestPayload) -> List[str]:
        """
        # Function: classify_intents
        # Purpose: Phân loại danh sách các intent dựa trên từ khóa prompt thô (Hỗ trợ Đa ý định).
        """
        prompt = payload.raw_prompt.lower()
        detected_intents = set()
        
        # 1. Nhận diện Database Design
        if any(kw in prompt for kw in ["bảng", "database", "sql", "migration", "dữ liệu bảng"]):
            detected_intents.add("DATABASE_DESIGN")
            
        # 2. Nhận diện Code Generation
        if any(kw in prompt for kw in [
            "viết code", "lập trình", "tạo file", "vibe code", 
            "viết module", "tạo module", "viết hàm", 
            "viết chương trình", "tạo app", "xây dựng ứng dụng", "xây dựng chương trình"
        ]):
            detected_intents.add("CODE_GENERATION")
            
        # 3. Nhận diện Testing / QC Execution
        if any(kw in prompt for kw in ["test", "kiểm thử", "sandbox", "chạy thử", "qc"]):
            detected_intents.add("TESTING_EXECUTION")

        # 4. Nhận diện Debugging / Refactoring (Mới bổ sung)
        if any(kw in prompt for kw in ["sửa lỗi", "fix bug", "tối ưu", "refactor", "vá lỗi"]):
            detected_intents.add("DEBUGGING_REFACTOR")

        # Nếu không khớp nhóm nào, gán mặc định là GENERAL_QUERY
        if not detected_intents:
            detected_intents.add("GENERAL_QUERY")
            
        intents_list = list(detected_intents)
        logger.info(f"[INTENT_ROUTER] Phân loại Multi-Intent thành công cho Request [{payload.request_id}]: --> {intents_list}")
        return intents_list

    def process_request(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        # Function: process_request
        # Purpose: Tiếp nhận dữ liệu thô, validate bằng Pydantic schema và trả về kết quả định tuyến đa ý định.
        # Input: raw_data (Dict[str, Any])
        # Output: Dict chứa thông tin request đã validate và danh sách intent.
        """
        logger.info("[INTENT_ROUTER] Đang tiến hành validate dữ liệu đầu vào qua Pydantic...")
        try:
            validated_payload = UserRequestPayload(**raw_data)
            intents = self.classify_intents(validated_payload)
            
            return {
                "success": True,
                "payload": validated_payload.model_dump(),
                "intents": intents,
                "intent": intents[0], # Giữ tương thích ngược với code cũ gọi trường 'intent' đơn
                "error": None
            }
        except ValidationError as e:
            logger.error(f"[INTENT_ROUTER] Lỗi Validation Pydantic: {e}")
            return {
                "success": False,
                "payload": None,
                "intents": [],
                "intent": None,
                "error": str(e)
            }


if __name__ == "__main__":
    logger.info("=== BẮT ĐẦU KIỂM THỬ ĐỘC LẬP INTENT ROUTER (MULTI-INTENT) ===")
    
    router = IntentRouter()
    
    # Test case 1: Yêu cầu phức hợp (Vừa viết code vừa test)
    sample_data = {
        "request_id": "REQ_MULTI_001",
        "raw_prompt": "Hãy viết code module tính toán và test sandbox cho tao.",
        "priority": 2
    }
    result = router.process_request(sample_data)
    logger.info(f"Kết quả xử lý Test Case 1 (Multi-Intent): {result['intents']}")
    
    # Test case 2: Dữ liệu không hợp lệ
    invalid_data = {
        "request_id": "REQ_002",
        "raw_prompt": "Hi"
    }
    result_invalid = router.process_request(invalid_data)
    logger.info(f"Kết quả xử lý Test Case 2 (Lỗi kỳ vọng): {result_invalid['success']}")
    
    logger.info("=== HOÀN TẤT KIỂM THỬ INTENT ROUTER ===")