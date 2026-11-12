"""
DAG Task Decomposition & Execution Engine cho vnxBox Enterprise.
Tích hợp Intent Router để phân loại ý định trước khi phân rã task DAG.
Đã tinh gọn để chặn đứng hiện tượng multi-agent broadcast đồng loạt.
"""
import logging
import json
from enterprise_factory.models import AgentTaskDAG, AgentRegistry, AgentDiscussion
from enterprise_factory.services.orchestrator import ask_local_agent
from enterprise_factory.services.hr_spawner import HRSpawner
from enterprise_factory.intent_router import IntentRouter

logger = logging.getLogger(__name__)


class DAGTaskEngine:
    """Bộ điều phối biểu đồ công việc tích hợp Intent Router và HR Spawner"""

    @staticmethod
    def decompose_and_create(directive, company):
        """Bóc tách ý định qua Intent Router trước khi phân rã DAG hoặc phản hồi nhanh"""
        directive_text = directive.directive_text
        logger.info(f"[*] [DAG_ENGINE] Tiếp nhận chỉ đạo cho directive ID #{directive.id}: '{directive_text}'")
        
        try:
            # Bước 0: Gọi Intent Router phân loại ý định
            intent_info = IntentRouter.classify(directive_text)
            intent_code = intent_info.get('intent_code', 'BUSINESS_DEBATE')
            
            logger.info(f"[*] [DAG_ENGINE] Intent Router xác định ý định: {intent_code}")

            # Nếu là Small Talk hoặc cuộc gọi họp nhanh, CHỈ DUY NHẤT BOD_CEO_01 phản hồi.
            # Tuyệt đối không kích hoạt HR hay các agent khác nhảy vào tranh luận cùng lúc.
            if intent_code in ['SMALL_TALK', 'MEETING_CALL']:
                quick_msg = intent_info.get('quick_response') or f"BOD CEO đã ghi nhận chỉ đạo '{directive_text}' từ Sếp và sẵn sàng điều phối toàn hệ thống."
                
                AgentDiscussion.objects.create(
                    company=company,
                    directive=directive,
                    agent_name='BOD_CEO_01',
                    message_content=f"🤖 **[BOD CEO (Tổng Giám Đốc AI)]**: {quick_msg}"
                )
                logger.info(f"[+] [DAG_ENGINE] BOD phản hồi nhanh cho Intent {intent_code}, chặn broadcast đa agent thành công.")
                return True

            # 1. Truy vấn toàn bộ nhân sự hiện có trong tập đoàn
            all_agents = AgentRegistry.objects.select_related('role').all()
            agent_roster_desc = "\n".join([
                f"- Mã ID: `{agent.agent_id}` | Chuyên môn: {agent.domain_scope} | Tên: {agent.display_name}"
                for agent in all_agents
            ])
            
            bod_agent = all_agents.filter(role__role_code='BOD').first() or all_agents.first()

            # 2. Xây dựng System Prompt cho BOD phân rã task dựa trên Intent
            system_prompt = (
                f"Bạn là Giám đốc Điều hành (BOD) của vnxBox Enterprise.\n"
                f"Ý định hệ thống vừa nhận diện: [{intent_code}].\n"
                "Nhiệm vụ: Phân rã chỉ đạo của Sếp thành từ 2 đến 4 bước công việc tuần tự.\n"
                "DANH SÁCH NHÂN SỰ ĐANG TRỰC CHIẾN:\n"
                f"{agent_roster_desc}\n\n"
                "Nếu thiếu chuyên gia, hãy chỉ định `agent_id` mới (VD: `GOLD_EXPERT_01`).\n"
                "BẮT BUỘC TRẢ VỀ ĐỊNH DẠNG JSON CHUẨN, KHÔNG KÈM VĂN VỞ NÀO KHÁC:\n"
                "[\n"
                "  {\"step_order\": 1, \"agent_id\": \"MÃ_AGENT\", \"domain_keyword\": \"LĨNH_VỰC\", \"step_name\": \"Tên bước\"}\n"
                "]"
            )
            
            logger.info(f"[*] [DAG_ENGINE] Đang gửi prompt phân rã tới BOD LLM theo intent {intent_code}...")
            raw_response = ask_local_agent(system_prompt, f"Chỉ đạo: {directive_text}")
            
            cleaned_response = raw_response.strip()
            if "```json" in cleaned_response:
                cleaned_response = cleaned_response.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned_response:
                cleaned_response = cleaned_response.split("```")[1].split("```")[0].strip()
                
            steps_data = json.loads(cleaned_response)
            
            for step in steps_data:
                target_agent_id = step.get('agent_id')
                domain_keyword = step.get('domain_keyword', 'GENERAL')
                
                agent_obj = AgentRegistry.objects.select_related('role').filter(agent_id=target_agent_id).first()
                
                # Gọi HR Spawner nếu thiếu nhân sự
                if not agent_obj:
                    logger.warning(f"[!] [DAG_ENGINE] Thiếu nhân sự '{target_agent_id}', gọi HR Spawner...")
                    agent_obj = HRSpawner.spawn_agent_if_needed(
                        domain_keyword=domain_keyword, 
                        role_code_hint='DEV_BE', 
                        company_code=company.code if company else 'GLOBAL'
                    )
                
                AgentTaskDAG.objects.create(
                    directive=directive,
                    assigned_agent=agent_obj or bod_agent,
                    step_name=step.get('step_name', 'Thực thi nhiệm vụ'),
                    step_order=step.get('step_order', 1),
                    status='PENDING'
                )

            logger.info(f"[+] [DAG_ENGINE] Khởi tạo DAG thành công cho directive #{directive.id}")
            return True
            
        except Exception as e:
            logger.error(f"[-] [DAG_ENGINE ERROR] Lỗi xử lý DAG, tạo task fallback: {str(e)}", exc_info=True)
            fallback_agent = AgentRegistry.objects.select_related('role').filter(role__role_code='DEV_BE').first() or bod_agent
            AgentTaskDAG.objects.create(
                directive=directive,
                assigned_agent=fallback_agent,
                step_name="Thực thi trực tiếp chỉ đạo",
                step_order=1,
                status='PENDING'
            )
            return False