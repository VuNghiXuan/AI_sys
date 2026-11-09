# Path: enterprise_factory/views.py
from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Company, AgentRegistry, ProjectNode, ExecutionLog
from .boardroom_engine import BoardroomEngine
from .langgraph_engine import factory_app
from django.http import JsonResponse
from django.db import models
boardroom = BoardroomEngine()

import json
from django.core.serializers.json import DjangoJSONEncoder
from django.views.decorators.csrf import csrf_exempt
import requests

def seed_default_corporate_data():
    """Khởi tạo Tập đoàn gốc và các nhân sự AI mặc định nếu DB trống"""
    hold_co, _ = Company.objects.get_or_create(
        code="GLOBAL_HOLDING",
        defaults={"name": "Tập đoàn AI VnxBox (Global)", "domain": "Quản trị & Công nghệ AI"}
    )
    Company.objects.get_or_create(
        code="JEWELRY_CORP",
        defaults={"name": "Công ty Vàng Bạc Đá Quý VNX", "domain": "Quản lý Kho & Thuế Vàng Bạc"}
    )

    default_agents = [
        {"id": "BOD_CEO_01", "name": "Hội đồng Quản trị AI", "dept": "Khối Quản trị", "role": "Mổ xẻ chiến lược & Phân rã DAG Task"},
        {"id": "BA_ANALYST_01", "name": "Chuyên viên BA Nghiệp vụ", "dept": "Khối Phân tích", "role": "Phân tích User Story & Bóc tách yêu cầu"},
        {"id": "ARCH_DESIGNER_01", "name": "Kiến trúc sư Trưởng", "dept": "Khối Kiến trúc", "role": "Thiết kế Schema & Mô hình Dữ liệu"},
        {"id": "ENG_DEV_CORE_01", "name": "Lập trình viên Core Backend", "dept": "Khối Lập trình", "role": "Xây dựng mã nguồn Vibercode chuẩn mực"},
        {"id": "QA_AUDITOR_01", "name": "Chuyên gia Thẩm định QA", "dept": "Khối Kiểm thử", "role": "Kiểm duyệt An toàn Sandbox & Thẩm định Code"}
    ]

    for ag in default_agents:
        AgentRegistry.objects.get_or_create(
            agent_id=ag["id"],
            defaults={
                "display_name": ag["name"],
                "company": hold_co,
                "department": ag["dept"],
                "role_desc": ag["role"],
                "system_prompt": f"Bạn là {ag['name']} phụ trách {ag['role']}.",
                "status": "READY"
            }
        )

def index_view(request):
    seed_default_corporate_data()
    return render(request, 'index.html')

@api_view(['GET'])
def api_get_companies(request):
    companies = Company.objects.all().values()
    return Response({"status": "SUCCESS", "companies": list(companies)})

@api_view(['GET'])
def api_get_agents(request):
    company_code = request.GET.get('company_code')
    qs = AgentRegistry.objects.all()
    if company_code:
        qs = qs.filter(models.Q(company__code=company_code) | models.Q(company__isnull=True))
    
    agents = list(qs.values('agent_id', 'display_name', 'department', 'role_desc', 'status', 'company__name'))
    return Response({"status": "SUCCESS", "agents": agents})

@api_view(['GET'])
def api_get_logs(request):
    logs = ExecutionLog.objects.all().order_by('-created_at')[:20].values()
    return Response({"status": "SUCCESS", "recent_logs": list(logs)})

@api_view(['POST'])
def api_boardroom_debate(request):
    prompt = request.data.get("prompt", "").strip()
    company_code = request.data.get("company_code", "GLOBAL_HOLDING")
    
    if not prompt:
        return Response({"status": "ERROR", "message": "Prompt không được để trống."}, status=400)

    try:
        debate_res = boardroom.conduct_multi_agent_debate(prompt)
        transcript = debate_res.get("debate_transcript", "")
        questions = boardroom.generate_clarification_questions(prompt, transcript)

        return Response({
            "status": "SUCCESS",
            "debate_transcript": transcript,
            "clarification_questions": questions
        })
    except Exception as e:
        return Response({"status": "ERROR", "message": str(e)}, status=500)

@api_view(['POST'])
def api_boardroom_matrix(request):
    prompt = request.data.get("prompt", "").strip()
    transcript = request.data.get("transcript", "").strip()
    answers = request.data.get("answers", {})

    try:
        matrix = boardroom.build_solution_matrix(prompt, transcript, answers)
        return Response({"status": "SUCCESS", "solution_matrix": matrix})
    except Exception as e:
        return Response({"status": "ERROR", "message": str(e)}, status=500)

@api_view(['POST'])
def api_orchestrate(request):
    prompt = request.data.get("prompt", "").strip()
    selected_option = request.data.get("selected_option", {})
    company_code = request.data.get("company_code", "GLOBAL_HOLDING")
    
    if not prompt:
        return Response({"status": "ERROR", "message": "Prompt không được để trống."}, status=400)

    # Đăng ký tự động nhân sự AI mới vào DB nếu phát hiện vai trò nghiệp vụ mới
    Company.objects.get_or_create(code=company_code, defaults={"name": company_code, "domain": "Chuyên ngành Mới"})

    full_context = f"[{company_code}] {prompt}\n[Phương án: {selected_option.get('title', '')}]"

    initial_state = {
        "user_prompt": full_context,
        "ba_analysis": "",
        "architect_design": "",
        "generated_code": "",
        "qa_audit_result": "",
        "logs": []
    }

    try:
        final_state = factory_app.invoke(initial_state)
        return Response({
            "status": "SUCCESS",
            "workflow_logs": final_state.get("logs", []),
            "ba_analysis": final_state.get("ba_analysis", ""),
            "architect_design": final_state.get("architect_design", ""),
            "generated_code": final_state.get("generated_code", ""),
            "qa_audit_result": final_state.get("qa_audit_result", "")
        })
    except Exception as e:
        return Response({"status": "ERROR", "message": str(e)}, status=500)

def api_get_apps(request):
    # Logic trả về danh sách các app của bạn
    apps = [] # Lấy danh sách app từ DB hoặc cấu hình
    return JsonResponse({"apps": apps})

def index_view(request):
    # Lấy danh sách công ty và chuyển thành list dict để đưa vào JS
    companies_qs = Company.objects.all().order_by('name')
    companies_list = list(companies_qs.values('code', 'name', 'domain', 'description'))

    # Lấy danh sách nhân viên AI
    agents_qs = AgentRegistry.objects.select_related('company').all().order_by('agent_id')
    agents_list = []
    for agent in agents_qs:
        agents_list.append({
            'agent_id': agent.agent_id,
            'display_name': agent.display_name,
            'company_code': agent.company.code if agent.company else None,
            'department': agent.department,
            'role_desc': agent.role_desc,
            'status': agent.status
        })

    context = {
        'companies_json': json.dumps(companies_list, cls=DjangoJSONEncoder),
        'agents_json': json.dumps(agents_list, cls=DjangoJSONEncoder),
    }
    return render(request, 'enterprise_factory/index.html', context)

@csrf_exempt
def api_get_agents(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            prompt = data.get('prompt', '').strip()
            company_code = data.get('company_code', '')
            target_company = company_code if company_code else 'GLOBAL'
            
            prompt_lower = prompt.lower()
            
            # ==========================================
            # NHÓM 1: CHÀO HỎI / GỌI HỌP NHANH (GREETING)
            # ==========================================
            greetings = ['alo', 'chào', 'hi', 'ae ơi', 'có ai không', 'hú', 'hello', 'họp đi']
            if any(prompt_lower == g or prompt_lower.startswith(g + ' ') for g in greetings) and len(prompt.split()) <= 4:
                return JsonResponse({
                    "status": "success",
                    "response": (
                        "🏛️ **[BOD CEO]**: Chào Sếp! Anh em nhân sự AI đã tề tựu đông đủ tại phòng họp vnxBox.\n\n"
                        "- 📊 **Chuyên gia BA & Nhân sự**: Sẵn sàng hỗ trợ tra cứu lịch trình, dữ liệu.\n"
                        "- 🏗️ **Kiến trúc sư Trưởng**: Sẵn sàng vận hành hệ thống.\n\n"
                        "👉 Sếp có chỉ đạo hay cần tra cứu thông tin gì hôm nay không ạ?"
                    )
                })

            # ==========================================
            # NHÓM 2: HỎI ĐÁP NGHIỆP VỤ / TRA CỨU THÔNG TIN (GENERAL_QUERY)
            # (Ví dụ: kiểm tra lịch họp, nhân sự, báo cáo, v.v. Không viết code)
            # ==========================================
            query_keywords = ['hôm nay có ai họp', 'lịch họp', 'nhân sự', 'ai họp', 'kiểm tra', 'báo cáo', 'thống kê']
            is_general_query = any(kw in prompt_lower for kw in query_keywords) and not any(sw in prompt_lower for sw in ['viết app', 'làm phần mềm', 'xây dựng hệ thống', 'tạo ứng dụng', 'code'])

            if is_general_query:
                # Gọi Ollama đóng vai Chuyên gia Nhân sự & Trợ lý điều hành để trả lời trực tiếp câu hỏi nghiệp vụ
                system_instruction = (
                    f"Bạn là Trợ lý Điều hành và Chuyên gia Quản trị Nhân sự của tập đoàn vnxBox (Khối: {target_company}). "
                    f"Sếp đang hỏi câu hỏi nghiệp vụ: '{prompt}'. "
                    "Hãy trả lời trực tiếp, ngắn gọn, chuyên nghiệp và đúng trọng tâm vào vấn đề Sếp đang thắc mắc (ví dụ về lịch họp, nhân sự, tình hình công việc), "
                    "tuyệt đối KHÔNG tự ý lập ma trận phần mềm hay đòi viết code."
                )
                
                ollama_payload = {
                    "model": "qwen2.5-coder",
                    "prompt": f"{system_instruction}\n\nCâu hỏi của Sếp: {prompt}",
                    "stream": False
                }
                
                ai_response_text = ""
                try:
                    ollama_res = requests.post("http://localhost:11434/api/generate", json=ollama_payload, timeout=60)
                    if ollama_res.status_code == 200:
                        ai_response_text = ollama_res.json().get("response", "")
                    else:
                        ai_response_text = "⚠️ Hệ thống Ollama đang bận xử lý."
                except Exception as e:
                    ai_response_text = f"[Lỗi kết nối Ollama]: {str(e)}"

                return JsonResponse({
                    "status": "success",
                    "response": ai_response_text
                })

            # ==========================================
            # NHÓM 3: YÊU CẦU PHÁT TRIỂN PHẦN MỀM (SOFTWARE_REQUEST)
            # (Chỉ khi Sếp muốn viết app, làm hệ thống mới chạy quy trình 4 bước)
            # ==========================================
            system_instruction = (
                f"Bạn là Hội đồng Quản trị AGI của tập đoàn đa ngành vnxBox (Mã khối: {target_company}). "
                f"Sếp vừa giao yêu cầu phát triển phần mềm/hệ thống: '{prompt}'.\n"
                "Hãy tổ chức phiên họp thực chiến gồm:\n"
                "1. [Bóc tách nghiệp vụ chuyên ngành]: Triệu tập chuyên gia lĩnh vực tương ứng để liệt kê các tính năng cốt lõi.\n"
                "2. [Giải pháp Local-First]: Kiến trúc sư & Dev bàn về Django, SQLite, Alpine.js, thư viện Python tối ưu.\n"
                "3. [Mở rộng & Bảo mật]: Phân quyền bảo mật và tích hợp.\n"
                "4. [Solution Matrix & Thư mục]: Lập Bảng Ma Trận Giải Pháp và yêu cầu Sếp duyệt phương án, chỉ định tên thư mục dự án trước khi sinh Vibercode."
            )
            
            ollama_payload = {
                "model": "qwen2.5-coder",
                "prompt": f"{system_instruction}\n\nYêu cầu thực chiến từ Sếp: {prompt}",
                "stream": False
            }
            
            ai_response_text = ""
            try:
                ollama_res = requests.post("http://localhost:11434/api/generate", json=ollama_payload, timeout=90)
                if ollama_res.status_code == 200:
                    ai_response_text = ollama_res.json().get("response", "")
                else:
                    ai_response_text = "⚠️ Ollama local đang bận."
            except Exception as e:
                ai_response_text = f"[Lỗi kết nối Ollama Local]: {str(e)}"

            return JsonResponse({
                "status": "success",
                "response": ai_response_text
            })
            
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
            
    return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)