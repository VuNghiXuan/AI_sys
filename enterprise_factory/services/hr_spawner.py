"""
HR Spawner Service cho vnxBox Enterprise.
Tự động kiểm tra danh mục vai trò, tự sinh role mới nếu cần và tuyển dụng chuyên gia AI 
(AgentRegistry) khi hệ thống phát sinh nhu cầu chuyên môn mới, kèm hệ thống Logging chuẩn Enterprise.
"""
import logging
import json
from enterprise_factory.models import Company, AgentRole, AgentRegistry
from enterprise_factory.services.orchestrator import ask_local_agent

# Khởi tạo logger chuyên dụng cho module hr_spawner
logger = logging.getLogger(__name__)


class HRSpawner:
    """Hệ thống tuyển dụng và tự sinh nhân sự AI tự trị"""

    @staticmethod
    def spawn_agent_if_needed(domain_keyword: str, role_code_hint: str = 'DEV_BE', company_code: str = 'GLOBAL') -> AgentRegistry:
        """
        Kiểm tra xem lĩnh vực `domain_keyword` đã có chuyên gia phụ trách chưa.
        Nếu chưa, Giám đốc Nhân sự (HR_MANAGER_01) sẽ tự động thiết kế và tuyển dụng mới!
        Kèm theo hệ thống ghi log chi tiết từng bước.
        """
        logger.info(f"[*] [HR_SPAWNER] Kiểm tra nhu cầu tuyển dụng chuyên gia cho domain: '{domain_keyword}' (Role hint: {role_code_hint}, Company: {company_code})")
        
        try:
            # 1. Kiểm tra xem đã có Agent nào phụ trách domain này chưa
            logger.debug(f"[*] [HR_SPAWNER] Truy vấn DB kiểm tra Agent hiện có với domain_scope chứa '{domain_keyword}'...")
            existing_agent = AgentRegistry.objects.select_related('role').filter(domain_scope__icontains=domain_keyword).first()
            
            if existing_agent:
                logger.info(f"[+] [HR_SPAWNER] Đã có sẵn chuyên gia phụ trách domain '{domain_keyword}': {existing_agent.agent_id} ({existing_agent.display_name}). Không cần tuyển mới.")
                return existing_agent

            logger.info(f"[!] [HR_SPAWNER] Chưa có chuyên gia cho domain '{domain_keyword}'. Bắt đầu quy trình tuyển dụng tự động...")
            company = Company.objects.filter(code=company_code).first()

            # 2. Đảm bảo Role code tồn tại trong bảng động AgentRole, nếu chưa có thì tự động tạo mới!
            role_code_upper = role_code_hint.upper()
            logger.debug(f"[*] [HR_SPAWNER] Kiểm tra/Khởi tạo AgentRole với code: '{role_code_upper}'...")
            role_obj, created = AgentRole.objects.get_or_create(
                role_code=role_code_upper,
                defaults={
                    'role_name': f"Chuyên gia {domain_keyword.title()}",
                    'description': f"Vai trò tự sinh tự động bởi HR Spawner cho lĩnh vực {domain_keyword}"
                }
            )
            if created:
                logger.info(f"[+] [HR_SPAWNER] Đã tự động tạo Role mới trong DB: {role_obj.role_code} - {role_obj.role_name}")
            else:
                logger.debug(f"[+] [HR_SPAWNER] Role '{role_obj.role_code}' đã tồn tại trong hệ thống.")

            # 3. Sử dụng năng lực LLM của HR Director (HR_MANAGER_01) để thiết kế hồ sơ chuyên gia mới
            hr_agent = AgentRegistry.objects.select_related('role').filter(agent_id='HR_MANAGER_01').first()
            hr_prompt = hr_agent.system_prompt if hr_agent else "Bạn là Giám đốc Nhân sự chuyên nghiệp của vnxBox Enterprise."

            design_instruction = (
                f"{hr_prompt}\n\n"
                f"NHIỆM VỤ: Thiết kế hồ sơ nhân sự AI mới chuyên trách lĩnh vực: '{domain_keyword}'.\n"
                "BẮT BUỘC TRẢ VỀ ĐỊNH DẠNG JSON CHUẨN (KHÔNG KÈM MARKDOWN NÀO KHÁC):\n"
                "{\n"
                f"  \"agent_id\": \"{domain_keyword.upper()}_EXPERT_01\",\n"
                f"  \"display_name\": \"Chuyên gia {domain_keyword.title()}\",\n"
                f"  \"system_prompt\": \"Bạn là Chuyên gia hàng đầu về {domain_keyword} tại vnxBox Enterprise. Nhiệm vụ của bạn là phân tích sâu, viết code hoặc xử lý nghiệp vụ chuẩn xác tuyệt đối trong lĩnh vực này.\",\n"
                "  \"risk_threshold\": \"HITL_REQUIRED\"\n"
                "}"
            )

            logger.info(f"[*] [HR_SPAWNER] Đang gửi yêu cầu thiết kế hồ sơ chuyên gia tới HR LLM (Ollama)...")
            raw_resp = ask_local_agent(design_instruction, f"Yêu cầu tuyển dụng gấp chuyên gia cho domain: {domain_keyword}")
            logger.debug(f"[DEBUG] [HR_SPAWNER] Raw response từ HR LLM:\n{raw_resp}")

            # Làm sạch chuỗi JSON trả về từ LLM
            cleaned_resp = raw_resp.strip()
            if "```json" in cleaned_resp:
                cleaned_resp = cleaned_resp.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned_resp:
                cleaned_resp = cleaned_resp.split("```")[1].split("```")[0].strip()

            profile = json.loads(cleaned_resp)
            logger.info(f"[+] [HR_SPAWNER] HR LLM đã thiết kế thành công hồ sơ: {profile.get('agent_id')} - {profile.get('display_name')}")

            # 4. Khởi tạo và lưu nhân sự mới vào Database
            new_agent_id = profile.get('agent_id', f"{domain_keyword.upper()}_01")
            new_display_name = profile.get('display_name', f"Chuyên gia {domain_keyword}")
            new_sys_prompt = profile.get('system_prompt', f"Bạn là chuyên gia {domain_keyword}.")
            new_risk_threshold = profile.get('risk_threshold', 'HITL_REQUIRED')

            new_agent = AgentRegistry.objects.create(
                agent_id=new_agent_id,
                display_name=new_display_name,
                company=company,
                role=role_obj,
                domain_scope=domain_keyword.upper(),
                system_prompt=new_sys_prompt,
                risk_threshold=new_risk_threshold,
                version='1.0.0'
            )
            
            logger.info(f"🎉 [HR_SPAWNER SUCCESS] Đã tuyển dụng và kích hoạt thành công nhân sự mới: ID='{new_agent.agent_id}' | Name='{new_agent.display_name}' | Domain='{new_agent.domain_scope}'")
            return new_agent

        except Exception as e:
            logger.error(f"[-] [HR_SPAWNER ERROR] Lỗi parse JSON tuyển dụng hoặc tạo agent, tiến hành tạo fallback mặc định: {str(e)}", exc_info=True)
            
            # Tạo fallback an toàn nếu LLM sinh lỗi format
            fallback_id = f"{domain_keyword[:5].upper()}_EXPERT_01"
            fallback_role_obj, _ = AgentRole.objects.get_or_create(
                role_code=role_code_hint.upper(),
                defaults={'role_name': f"Chuyên gia {domain_keyword.title()}"}
            )
            
            fallback_agent = AgentRegistry.objects.create(
                agent_id=fallback_id,
                display_name=f"Chuyên gia {domain_keyword}",
                company=company,
                role=fallback_role_obj,
                domain_scope=domain_keyword.upper(),
                system_prompt=f"Bạn là chuyên gia về {domain_keyword} tại vnxBox Enterprise.",
                risk_threshold='HITL_REQUIRED',
                version='1.0.0'
            )
            
            logger.warning(f"[!] [HR_SPAWNER FALLBACK] Đã tạo fallback Agent thành công: {fallback_agent.agent_id} ({fallback_agent.display_name})")
            return fallback_agent