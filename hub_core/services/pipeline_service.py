"""
# File Path: hub_core/services/pipeline_service.py
# File Purpose: Service điều phối luồng Autonomous Multi-Agent Pipeline (PM -> Coder -> Sandbox QC -> Self-Correction)
#               kết hợp Workspace Manager và Domain/Sub-Domain Context để chạy kiểm thử trên venv độc lập.
# Connected Files: [hub_core/services/workspace_manager.py, hub_core/services/domain_injector.py, core/router.py, core/dag_engine.py, core/agent_executor.py]
"""

import os
import re
import time
import uuid
import logging
import unicodedata
import subprocess
from typing import Dict, Any, Optional

from hub_core.models import RequestJob, TaskExecutionLog
from .domain_injector import DomainContextInjector
from .workspace_manager import IsolatedWorkspaceManager

# IMPORT CÁC ENGINE GỐC TỪ THƯ MỤC core/
from core.router import IntentRouter
from core.dag_engine import BlueprintDAGEngine
from core.agent_executor import AgentExecutor

logger = logging.getLogger("vnxBox.PipelineService")


class DjangoPipelineService:
    """Điều phối vòng đời xử lý job qua Router, DAG, PM Agent, Coder Agent và Sandbox QC."""

    def __init__(self, max_retries: int = 2, base_output_dir: str = "generated_apps"):
        self.max_retries = max_retries
        self.workspace_manager = IsolatedWorkspaceManager(base_output_dir=base_output_dir)

        self.router = IntentRouter()
        self.dag_engine = BlueprintDAGEngine()
        self.agent_executor = AgentExecutor()

    def execute_job(
        self,
        request_id: str,
        raw_prompt: str,
        domain: str = "software",
        sub_domain: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Thực thi toàn bộ vòng đời job với domain và sub_domain (tùy chọn)."""
        job = self._init_or_update_job(request_id, raw_prompt, domain)
        logger.info(
            f"[DJANGO_SERVICE] Bắt đầu thực thi Job [{request_id}] "
            f"với Domain [{domain}], SubDomain [{sub_domain or 'default'}]."
        )

        try:
            domain_context = DomainContextInjector.get_domain_context(
                domain,
                sub_domain=sub_domain,
            )

            if not self._validate_request(job, request_id, raw_prompt):
                return {"status": "FAILED", "reason": "Validation Error"}

            refined_spec = self._run_pm_agent_step(job, raw_prompt, domain_context)

            # 1. Coder Agent sinh mã nguồn & dựng Workspace độc lập
            code_result = self._run_coder_agent_step(job, raw_prompt, refined_spec, domain_context)
            if not code_result["success"]:
                return {
                    "status": "FAILED",
                    "reason": "LLM Generation Error",
                    "details": code_result.get("error"),
                }

            generated_code = code_result["generated_code"]
            workspace_info = code_result["workspace_info"]

            # 2. Sandbox QC & Vòng lặp Tự vá lỗi trên môi trường Venv độc lập
            pipeline_success = self._run_isolated_sandbox_qc_loop(
                job, refined_spec, workspace_info, generated_code
            )

            if pipeline_success:
                self._finalize_success_job(job, workspace_info["app_file"])
                return {
                    "status": "SUCCESS",
                    "job_id": str(job.job_id),
                    "request_id": request_id,
                    "domain": domain,
                    "sub_domain": sub_domain,
                    "output_dir": workspace_info["proj_dir"],
                    "output_file": workspace_info["app_file"],
                    "requirements_file": workspace_info["req_file"],
                    "attempts": job.attempts,
                }

            job.status = "FAILED"
            job.save()
            return {
                "status": "NEED_HUMAN_REVIEW",
                "job_id": str(job.job_id),
                "request_id": request_id,
                "attempts": self.max_retries,
            }

        except Exception as e:
            logger.error(f"[DJANGO_SERVICE] Lỗi ngoại lệ hệ thống trong Job {request_id}: {e}", exc_info=True)
            job.status = "FAILED"
            job.save()
            return {"status": "FAILED", "error": str(e)}

    def _slugify_vietnamese(self, text: str) -> str:
        """Chuẩn hóa chuỗi tiếng Việt thành tên thư mục/file ASCII an toàn."""
        nfkd_form = unicodedata.normalize("NFKD", text)
        only_ascii = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
        slug = re.sub(r"[^a-zA-Z0-9]+", "_", only_ascii).lower().strip("_")
        words = [w for w in slug.split("_") if w][:5]
        return "_".join(words) if words else f"feature_{uuid.uuid4().hex[:6]}"

    def _init_or_update_job(self, request_id: str, raw_prompt: str, domain: str) -> RequestJob:
        """Khởi tạo hoặc cập nhật bản ghi RequestJob trước khi chạy."""
        job, created = RequestJob.objects.get_or_create(
            request_id=request_id,
            defaults={"raw_prompt": raw_prompt, "domain": domain, "status": "RUNNING"},
        )
        if not created:
            job.status = "RUNNING"
            job.raw_prompt = raw_prompt
            job.domain = domain
            job.save()
        return job

    def _validate_request(self, job: RequestJob, request_id: str, raw_prompt: str) -> bool:
        """Validate payload qua IntentRouter và dựng đồ thị DAG theo danh sách intents."""
        raw_req = {"request_id": request_id, "raw_prompt": raw_prompt, "priority": 3}
        routing_result = self.router.process_request(raw_req)
        if not routing_result.get("success", True):
            job.status = "FAILED"
            job.save()
            return False

        intents = routing_result.get("intents", [routing_result.get("intent", "CODE_GENERATION")])
        self.dag_engine.build_dag_from_multiple_intents(intents, request_id)
        return True

    def _run_pm_agent_step(self, job: RequestJob, raw_prompt: str, domain_context: str) -> str:
        """Gọi PM Agent phân tích yêu cầu thành đặc tả kỹ thuật tiếng Việt."""
        task_log = TaskExecutionLog.objects.create(
            job=job,
            task_name="Task_1_Design_Spec",
            agent_assigned="pm_agent",
            status="RUNNING",
            input_payload=raw_prompt,
        )
        pm_prompt = (
            f"QUAN TRỌNG: Toàn bộ nội dung phân tích, User Story, và tiêu chuẩn kỹ thuật PHẢI ĐƯỢC VIẾT HOÀN TOÀN BẰNG TIẾNG VIỆT.\n\n"
            f"Hãy bóc tách yêu cầu sau thành User Story và tiêu chuẩn kỹ thuật chi tiết:\n{raw_prompt}\n\n"
            f"{domain_context}"
        )
        pm_result = self.agent_executor.run_agent(agent_id="pm_agent", task_context=pm_prompt)
        refined_spec = pm_result.get("output", raw_prompt)
        task_log.status = "SUCCESS"
        task_log.output_result = refined_spec
        task_log.save()
        return refined_spec

    def _run_coder_agent_step(
        self,
        job: RequestJob,
        raw_prompt: str,
        refined_spec: str,
        domain_context: str,
    ) -> Dict[str, Any]:
        """Gọi Coder Agent sinh mã nguồn và chuẩn bị workspace độc lập."""
        task_log = TaskExecutionLog.objects.create(
            job=job,
            task_name="Task_3_VibeCode",
            agent_assigned="coder_agent",
            status="RUNNING",
            input_payload=refined_spec,
        )
        coder_prompt = (
            f"Triển khai yêu cầu sau bằng mã nguồn Python:\n{raw_prompt}\n\n"
            f"Đặc tả kỹ thuật:\n{refined_spec}\n\n"
            f"{domain_context}\n\n"
            f"LƯU Ý KỸ THUẬT:\n"
            f"- Được phép tự do sử dụng các thư viện ngoài cần thiết (pandas, numpy, openpyxl, requests,...).\n"
            f"- Mã nguồn dễ đọc, có docstring giải thích tham số và kiểu trả về bằng Tiếng Việt."
        )

        agent_result = self.agent_executor.run_coder_agent(task_name=raw_prompt, design_spec=coder_prompt)
        if agent_result.get("status") == "FAILED":
            task_log.status = "FAILED"
            task_log.error_message = agent_result.get("error", "LLM Error")
            task_log.save()
            job.status = "FAILED"
            job.save()
            return {"success": False, "error": agent_result.get("error")}

        raw_code = agent_result.get("source_code", "")
        generated_code = self._clean_llm_code_output(raw_code)

        project_name = self._slugify_vietnamese(raw_prompt)
        workspace_info = self.workspace_manager.prepare_isolated_workspace(project_name, generated_code)

        job.output_file_path = workspace_info["app_file"]
        job.save()

        task_log.status = "SUCCESS"
        task_log.output_result = f"# Project Dir: {workspace_info['proj_dir']}\n\n{generated_code}"
        task_log.save()

        return {
            "success": True,
            "project_name": project_name,
            "generated_code": generated_code,
            "workspace_info": workspace_info,
        }

    def _run_isolated_sandbox_qc_loop(
        self,
        job: RequestJob,
        refined_spec: str,
        workspace_info: dict,
        generated_code: str,
    ) -> bool:
        """Chạy pytest trong venv độc lập và kích hoạt vòng lặp tự vá lỗi khi thất bại."""
        current_attempt = 1
        task_qc_log = TaskExecutionLog.objects.create(
            job=job,
            task_name="Task_4_SandboxQC",
            agent_assigned="qc_agent",
            status="RUNNING",
            attempt_count=current_attempt,
        )

        python_exe = workspace_info["venv_python"]
        test_file = workspace_info["test_file"]
        app_file = workspace_info["app_file"]
        pip_exe = workspace_info["pip_executable"]

        while current_attempt <= self.max_retries:
            try:
                cmd = [python_exe, "-m", "pytest", test_file]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                test_passed = res.returncode == 0
                test_output = res.stdout + "\n" + res.stderr
            except Exception as e:
                test_passed = False
                test_output = str(e)

            if test_passed:
                task_qc_log.status = "SUCCESS"
                task_qc_log.output_result = "Pytest PASSED in Isolated Venv (Exit Code: 0)\n\n" + test_output
                task_qc_log.save()
                job.attempts = current_attempt
                job.save()
                return True

            match = re.search(r"ModuleNotFoundError: No module named '([^']+)'", test_output)
            if match:
                missing_lib = match.group(1).split(".")[0]
                logger.info(f"[ISOLATED_QC] Phát sinh thiếu thư viện [{missing_lib}] trong venv, đang cài bổ sung...")
                try:
                    subprocess.run([pip_exe, "install", missing_lib], check=True, capture_output=True, text=True)
                    with open(workspace_info["req_file"], "a", encoding="utf-8") as f:
                        f.write(f"{missing_lib}\n")
                    continue
                except Exception:
                    pass

            task_qc_log.error_message = test_output
            task_qc_log.save()

            logger.warning(f"[PIPELINE] Pytest thất bại ở lần thử {current_attempt}. Đang gọi Agent tự vá lỗi...")

            qc_result = self.agent_executor.run_agent(
                agent_id="qc_agent",
                task_context=(
                    f"Mã nguồn gây lỗi:\n{generated_code}\n\n"
                    f"Log lỗi pytest:\n{test_output}\nPhân tích nguyên nhân."
                ),
            )
            qc_analysis = qc_result.get("output", "")

            fix_result = self.agent_executor.run_coder_agent(
                task_name=f"Vá lỗi pytest lần {current_attempt}",
                design_spec=(
                    f"Spec: {refined_spec}\n\nCode cũ:\n{generated_code}\n\n"
                    f"QC Phân tích:\n{qc_analysis}\n\nYêu cầu: Viết lại code hoàn chỉnh đã sửa lỗi."
                ),
            )

            if fix_result.get("status") == "SUCCESS":
                new_code = self._clean_llm_code_output(fix_result.get("source_code", ""))
                if new_code:
                    generated_code = new_code
                    with open(app_file, "w", encoding="utf-8") as f:
                        f.write(generated_code)

                    third_party_libs = self.workspace_manager.extract_third_party_libs(generated_code)
                    with open(workspace_info["req_file"], "w", encoding="utf-8") as f:
                        for lib in third_party_libs:
                            f.write(f"{lib}\n")
                    subprocess.run([pip_exe, "install", "-r", workspace_info["req_file"]], capture_output=True, text=True)

            current_attempt += 1
            job.attempts = current_attempt
            job.save()
            time.sleep(1)

        return False

    def _clean_llm_code_output(self, raw_output: str) -> str:
        """Lọc sạch markdown code block nếu LLM trả về dạng ```python ... ```."""
        if "```python" in raw_output:
            try:
                parts = raw_output.split("```python")
                return parts[1].split("```")[0].strip()
            except Exception:
                pass
        return raw_output.strip()

    def _finalize_success_job(self, job: RequestJob, target_file: str):
        """Cập nhật trạng thái job thành công và đồng bộ Code Graph."""
        job.status = "SUCCESS"
        job.output_file_path = target_file
        job.save()
        try:
            from core.code_graph import ProjectCodeGraph
            cg = ProjectCodeGraph(root_dir=".")
            cg.scan_project_directory()
            cg.save_graph_to_disk()
            logger.info("[DJANGO_SERVICE] Đã cập nhật Code Graph vào PROJECT_MAP.json thành công.")
        except Exception as e:
            logger.warning(f"[DJANGO_SERVICE] Không thể cập nhật Code Graph: {e}")