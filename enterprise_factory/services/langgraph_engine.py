# Path: enterprise_factory/langgraph_engine.py
import operator
from typing import Annotated, TypedDict, List
from langgraph.graph import StateGraph, END
from . import ViberEnterpriseOrchestrator
from ..models import ExecutionLog

orchestrator = ViberEnterpriseOrchestrator()

class FactoryState(TypedDict):
    user_prompt: str
    ba_analysis: str
    architect_design: str
    generated_code: str
    qa_audit_result: str
    logs: Annotated[List[str], operator.add]

def log_and_save(node_name: str, prompt: str, response: str):
    """Hàm hỗ trợ in log ra Terminal và lưu vào DB ExecutionLog"""
    status = "FAILED" if "❌" in response or not response else "SUCCESS"
    
    # In ra Terminal để Sếp quan sát ngay lập tức
    print(f"\n================ [{node_name.upper()}] ================")
    print(f"📤 PROMPT: {prompt[:150]}...")
    print(f"📥 RESPONSE: {response[:300]}...")
    print("==================================================")
    
    # Lưu vào Database cho AI đọc sau này
    try:
        ExecutionLog.objects.create(
            node_name=node_name,
            prompt_sent=prompt,
            response_received=response,
            status=status
        )
    except Exception as e:
        print(f"⚠️ Không thể lưu log vào DB: {str(e)}")

def node_ba_analysis(state: FactoryState):
    """[BA_SYSTEM_ANALYST_01] Phân tích yêu cầu và bóc tách User Story"""
    prompt = f"Phân tích yêu cầu sau thành User Story và các yêu cầu kỹ thuật chi tiết: {state['user_prompt']}"
    response = orchestrator.call_ollama(prompt, system_prompt="Bạn là Chuyên gia Phân tích Nghiệp vụ (BA). Hãy phân tích ngắn gọn, súc tích.")
    
    log_and_save("BA_Node", prompt, response)
    return {
        "ba_analysis": response,
        "logs": ["✅ [BA] Đã hoàn thành phân tích User Story."]
    }

def node_architect_design(state: FactoryState):
    """[ARCH_ERD_DESIGNER_01] Thiết kế cấu trúc dữ liệu và mô hình"""
    prompt = f"Thiết kế cấu trúc dữ liệu và sơ đồ dựa trên phân tích sau:\n{state['ba_analysis']}"
    response = orchestrator.call_ollama(prompt, system_prompt="Bạn là Kiến trúc sư phần mềm. Hãy vạch ra cấu trúc schema và các thành phần file.")
    
    log_and_save("Architect_Node", prompt, response)
    return {
        "architect_design": response,
        "logs": ["✅ [Architect] Đã thiết kế kiến trúc và mô hình dữ liệu."]
    }

# Path: enterprise_factory/langgraph_engine.py

def node_dev_code(state: FactoryState):
    """[ENG_BACKEND_CORE_01] Lập trình mã nguồn Vibercode hoàn chỉnh"""
    prompt = f"""Dựa vào thiết kế kiến trúc sau đây, hãy viết MÃ NGUỒN PYTHON HOÀN CHỈNH (không viết code mẫu hay cắt bớt):\n{state['architect_design']}\n
YÊU CẦU KỸ THUẬT:
1. Dòng đầu tiên phải là chú thích đường dẫn file (VD: # Path: gold_inventory/models.py).
2. Viết mã nguồn sạch, tối ưu, tuân thủ tiêu chuẩn Python.
3. Không chứa văn bản giải thích dài dòng ngoài khối code."""
    
    response = orchestrator.call_ollama(prompt, system_prompt="Bạn là Lập trình viên Python cao cấp. Chỉ xuất mã nguồn hoàn chỉnh trong cặp dấu ```python ... ```.", is_code=True)
    
    log_and_save("Dev_Node", prompt, response)
    return {
        "generated_code": response,
        "logs": ["✅ [Dev] Đã sinh mã nguồn Vibercode hoàn chỉnh."]
    }

def node_qa_audit(state: FactoryState):
    """[QA_SANDBOX_AUDITOR_01] Kiểm định chất lượng code"""
    prompt = f"Kiểm tra chất lượng đoạn code sau xem có lỗi cú pháp hoặc lỗ hổng không:\n{state['generated_code'][:500]}..."
    response = orchestrator.call_ollama(prompt, system_prompt="Bạn là Trưởng nhóm QA. Đánh giá ngắn gọn tính an toàn của đoạn code.")
    
    log_and_save("QA_Node", prompt, response)
    return {
        "qa_audit_result": response,
        "logs": ["✅ [QA] Đã hoàn thành kiểm định an toàn mã nguồn."]
    }

def build_factory_graph():
    workflow = StateGraph(FactoryState)
    workflow.add_node("ba_node", node_ba_analysis)
    workflow.add_node("architect_node", node_architect_design)
    workflow.add_node("dev_node", node_dev_code)
    workflow.add_node("qa_node", node_qa_audit)

    workflow.set_entry_point("ba_node")
    workflow.add_edge("ba_node", "architect_node")
    workflow.add_edge("architect_node", "dev_node")
    workflow.add_edge("dev_node", "qa_node")
    workflow.add_edge("qa_node", END)

    return workflow.compile()

factory_app = build_factory_graph()