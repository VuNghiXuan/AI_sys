"""
enterprise_factory/services/long_prompt_handler.py
Mô đun phân rã prompt dài (Hierarchical Chunker & Map-Reduce Local) cho vnxBox Enterprise.
Chạy hoàn toàn offline trên CPU, chống nghẽn context window và triệt tiêu lỗi Timeout.
"""

import re
import logging
from asgiref.sync import sync_to_async
from enterprise_factory.services.orchestrator.client import ask_local_agent

logger = logging.getLogger(__name__)

class LongPromptHandler:
    """
    Bộ xử lý đặc tả dài dành cho các User Story khổng lồ (như màn hình Giao dịch Mua Bán).
    """

    @staticmethod
    def chunk_spec_by_headers(text: str, max_chunk_chars: int = 1500) -> list[dict]:
        """
        Bước 1: Băm nhỏ Spec theo các tiêu đề Markdown (##, ###) để giữ nguyên cấu trúc logic.
        Áp dụng kỹ thuật Parent Header Anchoring (mỗi chunk con đều mang theo tiêu đề vĩ mô).
        """
        try:
            lines = text.split('\n')
            chunks = []
            current_header = "THÔNG TIN CHUNG & CẤU TRÚC GỐC"
            current_body = []
            current_len = 0

            for line in lines:
                # Phát hiện tiêu đề Markdown cấp 1 hoặc 2 hoặc 3
                if line.startswith('#') or line.startswith('TAB ') or line.startswith('FORM '):
                    if current_body:
                        chunks.append({
                            "header": current_header,
                            "content": "\n".join(current_body).strip()
                        })
                        current_body = []
                        current_len = 0
                    current_header = line.strip()
                
                current_body.append(line)
                current_len += len(line)

                # Nếu khối quá dài, tự động tách an toàn
                if current_len >= max_chunk_chars:
                    chunks.append({
                        "header": current_header,
                        "content": "\n".join(current_body).strip()
                    })
                    current_body = []
                    current_len = 0

            if current_body:
                chunks.append({
                    "header": current_header,
                    "content": "\n".join(current_body).strip()
                })

            logger.info(f"[*] [LONG PROMPT CHUNKER] Đã băm thành công bản đặc tả thành {len(chunks)} phân đoạn nguyên tử.")
            return chunks
        except Exception as e:
            logger.error(f"[-] [CHUNKER ERROR] Lỗi băm Spec: {str(e)}", exc_info=True)
            return [{"header": "FULL_SPEC_FALLBACK", "content": text}]

    @classmethod
    async def process_long_spec_via_map_reduce(cls, system_prompt_base: str, full_spec_text: str, timeout: int = 480) -> str:
        """
        Bước 2: Xử lý Map-Reduce cho prompt siêu dài (> 2000 ký tự).
        - Map: Tóm tắt cấu trúc từng chunk.
        - Reduce: Tổng hợp toàn bộ bản đồ thực thi cho BOD CEO và các Agent lập trình.
        """
        try:
            # Nếu ngắn thì gọi trực tiếp không cần chunking
            if len(full_spec_text) <= 2000:
                return await sync_to_async(ask_local_agent)(system_prompt_base, full_spec_text, timeout_seconds=timeout)

            # Băm nhỏ Spec
            chunks = await sync_to_async(cls.chunk_spec_by_headers)(full_spec_text)
            
            synthesized_summary = []
            for idx, chunk in enumerate(chunks, 1):
                map_prompt = (
                    f"Bạn là chuyên gia phân tích nghiệp vụ vnxBox Enterprise.\n"
                    f"Hãy đọc phân đoạn {idx}/{len(chunks)} thuộc phần '{chunk['header']}':\n"
                    f"----------------------------------------\n"
                    f"{chunk['content']}\n"
                    f"----------------------------------------\n"
                    f"Yêu cầu: Tóm tắt ngắn gọn các yêu cầu cốt lõi, công thức tính toán, quy tắc trạng thái hoặc ràng buộc dữ liệu tại phần này dưới dạng gạch đầu dòng rõ ràng."
                )
                
                logger.info(f"[*] [MAP-REDUCE MAP] Đang xử lý phân đoạn {idx}/{len(chunks)}...")
                chunk_summary = await sync_to_async(ask_local_agent)(
                    "Bạn là Trợ lý phân tích nghiệp vụ kỹ thuật cao cấp.", 
                    map_prompt, 
                    timeout_seconds=120
                )
                synthesized_summary.append(f"### [Phân đoạn {idx}: {chunk['header']}]\n{chunk_summary}")

            # Giai đoạn Reduce: Tổng hợp bức tranh toàn cảnh cho LLM sinh code hoặc báo cáo
            combined_context = "\n\n".join(synthesized_summary)
            reduce_prompt = (
                f"Dưới đây là bản đồ tóm tắt kiến trúc nghiệp vụ đã được bóc tách từ đặc tả gốc:\n\n"
                f"{combined_context}\n\n"
                f"Yêu cầu chung từ Sếp: Hãy phân tích toàn bộ cấu trúc này và lập kế hoạch triển khai Vibercode hoặc báo cáo chi tiết theo chuẩn mực kỹ thuật doanh nghiệp."
            )

            logger.info(f"[*] [MAP-REDUCE REDUCE] Đang tổng hợp bản đồ cuối cùng để gửi cho LLM tổng điều hành...")
            final_response = await sync_to_async(ask_local_agent)(system_prompt_base, reduce_prompt, timeout_seconds=timeout)
            return final_response

        except Exception as e:
            logger.error(f"[-] [MAP-REDUCE ERROR] Lỗi xử lý luồng Map-Reduce: {str(e)}", exc_info=True)
            # Fallback an toàn nếu có lỗi
            return await sync_to_async(ask_local_agent)(system_prompt_base, full_spec_text, timeout_seconds=timeout)