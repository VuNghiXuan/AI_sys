# Path: enterprise_factory/boardroom_engine.py
import json
from . import ViberEnterpriseOrchestrator
from ..models import ExecutionLog

orchestrator = ViberEnterpriseOrchestrator()

class BoardroomEngine:
    """Động cơ điều phối Hội đồng AI tranh luận và tương tác trước khi viết code"""

    def conduct_multi_agent_debate(self, user_prompt: str) -> dict:
        """[Giai đoạn 1] Hội đồng Chuyên gia phân tích và CHỐT NGAY phương án thực thi (Không hỏi lại Sếp)"""
        system_prompt = (
            "Bạn là Hội đồng Quản trị vnxBox Enterprise (BOD, Kiến trúc sư trưởng). "
            "QUY TẮC: Khi Sếp Vũ đã ra lệnh hoặc duyệt phương án, BẠN TUYỆT ĐỐI KHÔNG ĐƯỢC HỎI LẠI HOẶC ĐỀ XUẤT CÁC BƯỚC HÀNH CHÍNH. "
            "Hãy lập tức phân tích kỹ thuật ngắn gọn trong 1-2 dòng và tự động chuyển giao công việc lập trình đa file (models, services, ui) cho đội ngũ DEV thực hiện ngay lập tức."
        )
        prompt = f"Yêu cầu thực thi từ Sếp Vũ: {user_prompt}"
        debate_result = orchestrator.call_ollama(prompt, system_prompt=system_prompt)

        # Ghi log
        ExecutionLog.objects.create(
            node_name="BOD_Multi_Agent_Debate",
            prompt_sent=prompt,
            response_received=debate_result,
            status="SUCCESS" if debate_result else "FAILED"
        )
        return {"debate_transcript": debate_result}

    def generate_clarification_questions(self, user_prompt: str, debate_transcript: str) -> list:
        """[Giai đoạn 2] Trích xuất 2-4 câu hỏi cốt lõi/điểm mơ hồ cần Sếp làm rõ"""
        system_prompt = (
            "Bạn là Chuyên gia Phân tích Nghiệp vụ (BA Lead). Dựa trên yêu cầu ban đầu và biên bản tranh luận, "
            "hãy liệt kê chính xác từ 2 đến 4 câu hỏi cốt lõi (dạng JSON Array các chuỗi văn bản) để người dùng làm rõ. "
            "Ví dụ format output duy nhất: [\"Câu hỏi 1?\", \"Câu hỏi 2?\"]"
        )
        prompt = f"Yêu cầu: {user_prompt}\nBiên bản tranh luận: {debate_transcript}"
        raw_response = orchestrator.call_ollama(prompt, system_prompt=system_prompt, is_code=True)

        try:
            # Lọc bỏ markdown codeblock nếu có
            clean_json = raw_response.strip().strip("```json").strip("```").strip()
            questions = json.loads(clean_json)
            if isinstance(questions, list):
                return questions
        except Exception:
            pass
        
        return [
            "Phương án ưu tiên của Sếp là tối ưu tốc độ xử lý hay bảo mật tuyệt đối?",
            "Sếp muốn tích hợp giao diện này vào SPA Dashboard hiện tại hay tách phân hệ riêng?"
        ]

    def build_solution_matrix(self, user_prompt: str, debate_transcript: str, user_answers: dict) -> list:
        """[Giai đoạn 3] Lập Ma trận Phương án (2-3 lựa chọn) sau khi Sếp trả lời câu hỏi"""
        system_prompt = (
            "Bạn là Kiến trúc sư Trưởng (Chief Architect). Dựa trên yêu cầu, biên bản tranh luận và các câu trả lời làm rõ của người dùng, "
            "hãy đưa ra đúng 2-3 phương án kỹ thuật tối ưu dưới dạng danh sách cấu trúc JSON.\n"
            "Mỗi phần tử gồm: id (str), title (str), description (str), pros (list str), cons (list str).\n"
            "Chỉ trả về JSON Array hợp lệ."
        )
        answers_text = "\n".join([f"- {q}: {a}" for q, a in user_answers.items()])
        prompt = f"Yêu cầu: {user_prompt}\nTranh luận: {debate_transcript}\nPhản hồi người dùng:\n{answers_text}"
        raw_response = orchestrator.call_ollama(prompt, system_prompt=system_prompt, is_code=True)

        try:
            clean_json = raw_response.strip().strip("```json").strip("```").strip()
            matrix = json.loads(clean_json)
            if isinstance(matrix, list) and len(matrix) > 0:
                return matrix
        except Exception:
            pass

        return [
            {
                "id": "OPT_01",
                "title": "Phương án 1: Kiến trúc Tinh gọn (Rapid Execution)",
                "description": "Tích hợp trực tiếp vào Django Core + WebSockets hiện tại, tối ưu thời gian phản hồi.",
                "pros": ["Triển khai nhanh", "Tốn ít bộ nhớ RAM", "Dễ bảo trì"],
                "cons": ["Mở rộng đa server cần cấu hình lại Redis"]
            },
            {
                "id": "OPT_02",
                "title": "Phương án 2: Kiến trúc Phân tán (Micro-services Headless)",
                "description": "Tách riêng Boardroom Service thành Worker độc lập giao tiếp qua REST/gRPC.",
                "pros": ["Khả năng mở rộng cao", "Cô lập hoàn toàn rủi ro"],
                "cons": ["Tốn thêm tài nguyên CPU/RAM local"]
            }
        ]