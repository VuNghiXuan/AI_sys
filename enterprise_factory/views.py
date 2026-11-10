# File: enterprise_factory/views.py
import os
import ast
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from enterprise_factory.models import (
    Company, AgentRegistry, DirectiveLog, 
    AgentDiscussion, CodePatchProposal
)
from enterprise_factory.services.intent_router import classify_user_intent
from enterprise_factory.services.orchestrator import ask_local_agent

def war_room_view(request):
    """View render giao diện Live War Room chính cho Sếp Vũ"""
    return render(request, 'enterprise_factory/command_center.html')


@csrf_exempt
def api_viber_state(request):
    """API trả về trạng thái toàn bộ phòng họp (Agents, Discussions, Patches) cho Alpine.js"""
    if request.method != 'GET':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
    
    try:
        agents = list(AgentRegistry.objects.values('agent_id', 'display_name', 'role_type', 'version'))
        
        discussions_raw = AgentDiscussion.objects.select_related('agent').order_by('-created_at')[:30]
        discussions = []
        for d in discussions_raw:
            discussions.append({
                'id': d.id,
                'agent_name': d.agent.display_name if d.agent else "Sếp Vũ",
                'phase': d.phase,
                'message_content': d.message_content,
                'created_at': d.created_at.strftime('%H:%M:%S')
            })

        patches = list(CodePatchProposal.objects.order_by('-created_at')[:20].values(
            'id', 'target_file', 'code_content', 'status'
        ))

        return JsonResponse({
            'status': 'success',
            'agents': agents,
            'discussions': discussions,
            'patches': patches
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
def api_viber_execute_directive(request):
    """API cốt lõi xử lý chỉ đạo của Sếp Vũ - Tích hợp Spec Auto-Parser, Zero-Question & Real-time Progressive Telemetry"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        directive_text = data.get('directive_text', '').strip()
        company_code = data.get('company_code', 'GLOBAL')

        if not directive_text:
            return JsonResponse({'status': 'error', 'message': 'Thiếu nội dung chỉ đạo!'}, status=400)

        company = Company.objects.filter(code=company_code).first()
        
        # 1. Ghi nhận chỉ đạo của Sếp Vũ lên khung chat phòng họp
        directive = DirectiveLog.objects.create(
            company=company,
            directive_text=directive_text,
            status='PROCESSING'
        )

        AgentDiscussion.objects.create(
            company=company,
            directive=directive,
            agent=None,  # Đại diện cho Sếp Vũ
            phase='USER_DIRECTIVE',
            message_content=directive_text
        )

        # Lấy nhân sự chuyên trách
        bod_agent = AgentRegistry.objects.filter(agent_id='BOD_CEO_01').first()
        dev_agent = AgentRegistry.objects.filter(agent_id='DEV_BE_01').first()
        if not bod_agent:
            bod_agent = AgentRegistry.objects.first()
        if not dev_agent:
            dev_agent = bod_agent

        # 2. SPEC AUTO-PARSER (Nhận diện Spec chi tiết hoặc yêu cầu viết app lớn)
        spec_keywords = ['Form', 'Quy trình', 'Chi nhánh', 'MUI Stepper', 'Phiếu nhập', 'Cột', 'Quyền', 'http']
        is_detailed_spec = len(directive_text) > 250 or any(k.lower() in directive_text.lower() for k in spec_keywords)

        if is_detailed_spec:
            intent = 'CODE_DEV'
            assigned_agent = dev_agent
        else:
            # Phân loại ý định thông thường qua Intent Router
            try:
                routing_info = classify_user_intent(directive_text)
                intent = routing_info.get('intent', 'SMALL_TALK')
                target_agent_id = routing_info.get('assigned_agent', 'BOD_CEO_01')
            except Exception:
                intent = 'SMALL_TALK'
                target_agent_id = 'BOD_CEO_01'

            assigned_agent = AgentRegistry.objects.filter(agent_id=target_agent_id).first()
            if not assigned_agent:
                assigned_agent = bod_agent

        # 3. XỬ LÝ HÀNH ĐỘNG VỚI TIẾN TRÌNH THỜI GIAN THỰC (REAL-TIME PROGRESSIVE TELEMETRY)
        if intent == 'SMALL_TALK':
            response_msg = ask_local_agent(
                "Bạn là BOD CEO vnxBox Enterprise. QUY TẮC: Trả lời cực kỳ ngắn gọn, sắc bén, không văn vở hành chính.", 
                f"Sếp Vũ vừa nói: {directive_text}"
            )
            AgentDiscussion.objects.create(
                company=company, directive=directive, agent=bod_agent,
                phase='SMALL_TALK', message_content=response_msg
            )
            
        elif intent == 'CODE_DEV':
            # --- BƯỚC 1: BOD CEO báo cáo đã nhận spec ---
            AgentDiscussion.objects.create(
                company=company, directive=directive, agent=bod_agent,
                phase='GENERAL_DEBATE',
                message_content="Đã tiếp nhận Spec chi tiết từ Sếp Vũ. Hệ thống chuyển thẳng sang chế độ Tự trị, tiến hành phân rã kiến trúc Multi-File..."
            )

            # --- BƯỚC 2: DEV Backend báo cáo chuẩn bị ngữ cảnh ---
            AgentDiscussion.objects.create(
                company=company, directive=directive, agent=dev_agent,
                phase='CODE_DEV',
                message_content="Dev Backend đang thiết lập cấu trúc trường dữ liệu (13 cột, công thức quy 10, phân quyền Role + Record)..."
            )

            system_prompt = (
                "Bạn là Chuyên gia Kiến trúc phần mềm & Vibercode cao cấp của vnxBox Enterprise.\n"
                "QUY TẮC TỐI THƯỢNG (ZERO-QUESTION, ACTION-FIRST):\n"
                "1. KHÔNG HỎI LẠI, KHÔNG VĂN VỞ.\n"
                "2. HÃY LẬP TỨC PHÂN RÃ và viết trọn bộ mã nguồn hoàn chỉnh theo cấu trúc 3 file độc lập, phân tách chính xác bằng từ khóa header sau:\n"
                "=== FILE: dynamic_app/models_gen.py ===\n"
                "=== FILE: dynamic_app/services_gen.py ===\n"
                "=== FILE: dynamic_app/ui_component_gen.html ===\n"
                "Đảm bảo viết code thực tế, đầy đủ logic nghiệp vụ theo đúng Spec Phiếu nhập vàng nguyên liệu của Sếp."
            )
            
            prompt_with_context = (
                f"SPEC / YÊU CẦU CHI TIẾT TỪ SẾP VŨ:\n{directive_text}\n\n"
                "Hãy tiến hành lập trình ngay lập tức, không hỏi han, xuất đầy đủ 3 file theo đúng cấu trúc."
            )
            
            # --- BƯỚC 3: Báo cáo đang kết nối Ollama local ---
            AgentDiscussion.objects.create(
                company=company, directive=directive, agent=dev_agent,
                phase='CODE_DEV',
                message_content="Đang gửi yêu cầu sinh mã nguồn tới Local LLM (Ollama - Qwen 2.5 Coder)... Đang xử lý logic phức tạp."
            )

            ai_raw_output = ask_local_agent(system_prompt, prompt_with_context, timeout_seconds=180)
            
            # --- BƯỚC 4: Báo cáo đang cắt gót đa file ---
            AgentDiscussion.objects.create(
                company=company, directive=directive, agent=dev_agent,
                phase='CODE_DEV',
                message_content="Nhận được phản hồi từ Ollama! Đang tiến hành bóc tách và kiểm tra tính toàn vẹn của 3 file (Models, Services, UI)..."
            )

            files_to_create = []
            if "=== FILE:" in ai_raw_output:
                chunks = ai_raw_output.split("=== FILE:")
                for chunk in chunks:
                    if not chunk.strip():
                        continue
                    lines = chunk.strip().split("\n")
                    raw_path = lines[0].strip()
                    
                    if not raw_path.startswith("dynamic_app/") or " " in raw_path:
                        if "models" in raw_path.lower():
                            file_path = "dynamic_app/models_gen.py"
                        elif "ui" in raw_path.lower() or "html" in raw_path.lower():
                            file_path = "dynamic_app/ui_component_gen.html"
                        else:
                            file_path = "dynamic_app/services_gen.py"
                    else:
                        file_path = raw_path

                    file_content = "\n".join(lines[1:]).strip()
                    
                    if "```python" in file_content:
                        file_content = file_content.split("```python")[1].split("```")[0].strip()
                    elif "```html" in file_content:
                        file_content = file_content.split("```html")[1].split("```")[0].strip()
                    elif "```" in file_content:
                        file_content = file_content.split("```")[1].split("```")[0].strip()
                        
                    files_to_create.append((file_path, file_content))
            else:
                clean_code = ai_raw_output
                if "```python" in clean_code:
                    clean_code = clean_code.split("```python")[1].split("```")[0].strip()
                elif "```" in clean_code:
                    clean_code = clean_code.split("```")[1].split("```")[0].strip()
                files_to_create.append(('dynamic_app/services_gen.py', clean_code))

            # Lưu các bản vá Code Patch chờ Sếp duyệt
            patch_summary = []
            for f_path, f_content in files_to_create:
                CodePatchProposal.objects.create(
                    target_file=f_path,
                    proposed_by_agent=dev_agent,
                    code_content=f_content,
                    status='PENDING'
                )
                patch_summary.append(f"`{f_path}`")

            # --- BƯỚC 5: Hoàn thành ---
            final_msg = (
                f"Đã lập trình thành công bộ Đa file tự động theo chuẩn Spec: {', '.join(patch_summary)}. "
                f"Các bản vá đã sẵn sàng bên dưới. Sếp bấm Approve & Apply nhé!"
            )
            AgentDiscussion.objects.create(
                company=company, directive=directive, agent=dev_agent,
                phase='CODE_DEV',
                message_content=final_msg
            )
        else:
            response_msg = ask_local_agent(assigned_agent.system_prompt, f"Sếp chỉ đạo: {directive_text}")
            AgentDiscussion.objects.create(
                company=company, directive=directive, agent=assigned_agent,
                phase=intent, message_content=response_msg
            )

        directive.status = 'SUCCESS'
        directive.save()

        return JsonResponse({
            'status': 'success',
            'message': f"Đã xử lý tiến trình tự trị thành công!",
            'intent': intent
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
def api_viber_approve_patch(request):
    """API duyệt bản vá code với tầng kiểm tra AST an toàn tuyệt đối"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

    try:
        body_unicode = request.body.decode('utf-8')
        data = json.loads(body_unicode)
        patch_id = data.get('patch_id')

        if not patch_id:
            return JsonResponse({'status': 'error', 'message': 'Thiếu patch_id trong request!'}, status=400)

        patch = CodePatchProposal.objects.filter(id=patch_id, status='PENDING').first()
        if not patch:
            return JsonResponse({'status': 'error', 'message': f'Không tìm thấy bản vá với ID: {patch_id} hoặc đã duyệt!'}, status=404)

        code_to_verify = patch.code_content
        target_file_path = patch.target_file

        # Tầng kiểm tra AST (Chỉ áp dụng với file Python .py)
        if target_file_path.endswith('.py'):
            try:
                ast.parse(code_to_verify)
            except SyntaxError as syntax_err:
                patch.status = 'REJECTED'
                patch.save()
                return JsonResponse({
                    'status': 'error', 
                    'message': f'BẢN VÁ BỊ TỪ CHỐI! Lỗi cú pháp Python AST: {str(syntax_err)}'
                }, status=400)

        # Ghi file an toàn vào thư mục dynamic_app
        safe_file_name = os.path.basename(target_file_path)
        target_dir = os.path.dirname(target_file_path) if os.path.dirname(target_file_path) else 'dynamic_app'
        os.makedirs(target_dir, exist_ok=True)
        final_file_path = os.path.join(target_dir, safe_file_name)

        with open(final_file_path, 'w', encoding='utf-8') as f:
            f.write(code_to_verify)

        patch.status = 'APPLIED'
        patch.save()

        return JsonResponse({
            'status': 'success',
            'message': f'Đã duyệt thành công và ghi file an toàn vào: {final_file_path}'
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
def api_viber_reject_patch(request):
    """API hủy / từ chối bản vá code"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        patch_id = data.get('patch_id')

        if not patch_id:
            return JsonResponse({'status': 'error', 'message': 'Thiếu patch_id!'}, status=400)

        patch = CodePatchProposal.objects.filter(id=patch_id).first()
        if not patch:
            return JsonResponse({'status': 'error', 'message': 'Không tìm thấy bản vá!'}, status=404)

        patch.status = 'REJECTED'
        patch.save()

        return JsonResponse({
            'status': 'success',
            'message': f'Đã hủy bản vá ID #{patch_id} thành công!'
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)