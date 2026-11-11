# File: enterprise_factory/views.py
"""
Views điều phối Live War Room & Xử lý chỉ đạo tự động cho vnxBox Enterprise.
Tuân thủ nguyên tắc: Không hardcode prompt/keywords, lấy cấu hình động từ Database (AgentRegistry).
"""

import os
import re
import ast
import json
import shutil
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.conf import settings
from django.db.models import Q
from enterprise_factory.models import (
    Company, AgentRegistry, DirectiveLog, 
    AgentDiscussion, CodePatchProposal, AgentTaskDAG
)
from enterprise_factory.services.dag_executor import DAGTaskEngine
from enterprise_factory.services.intent_router import classify_user_intent
from enterprise_factory.services.orchestrator import ask_local_agent

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync



def api_viber_state(request):
    """API trả về trạng thái nhân sự và hệ thống"""
    agents_list = []
    try:
        # Truy vấn trực tiếp qua object và select_related để tối ưu performance
        for a in AgentRegistry.objects.select_related('role').all():
            agents_list.append({
                'agent_id': getattr(a, 'agent_id', ''),
                'display_name': getattr(a, 'display_name', ''),
                'role__role_code': a.role.role_code if (hasattr(a, 'role') and a.role) else 'UNKNOWN',
                'version': getattr(a, 'version', '1.0'),
                'domain_scope': getattr(a, 'domain_scope', '')
            })
    except Exception as e:
        print(f"[-] Lỗi khi query agents trong api_viber_state: {str(e)}")

    return JsonResponse({
        'status': 'success',
        'agents': agents_list
    })


@csrf_exempt
def api_viber_execute_directive(request):
    """API cốt lõi xử lý chỉ đạo của Sếp - Định hướng động hoàn toàn qua Intent Router & DB Prompt"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        directive_text = data.get('directive_text', '').strip()
        company_code = data.get('company_code', 'GLOBAL')

        if not directive_text:
            return JsonResponse({'status': 'error', 'message': 'Thiếu nội dung chỉ đạo!'}, status=400)

        company = Company.objects.filter(code=company_code).first()
        
        # 1. Bóc tách @mention agent nếu Sếp chỉ định trực tiếp
        mentioned_tags = re.findall(r'@(\w+)', directive_text.lower())
        target_agent = None
        if mentioned_tags and 'all' not in mentioned_tags:
            tag_query = mentioned_tags[0]
            target_agent = AgentRegistry.objects.filter(
                Q(agent_id__icontains=tag_query) | 
                Q(role__role_code__icontains=tag_query) |
                Q(display_name__icontains=tag_query)
            ).first()

        # 2. Tạo log chỉ đạo từ Sếp
        directive = DirectiveLog.objects.create(
            company=company,
            directive_text=directive_text,
            status='PROCESSING'
        )

        AgentDiscussion.objects.create(
            company=company, directive=directive, agent=None,
            sender_type='USER', phase='USER_DIRECTIVE', message_content=directive_text
        )

        # 3. Phân định Intent động thông qua Intent Router hoặc chỉ định @mention
        assigned_agent = target_agent
        intent = 'SMALL_TALK'

        if not assigned_agent:
            try:
                routing_info = classify_user_intent(directive_text)
                intent = routing_info.get('intent', 'SMALL_TALK')
                target_agent_id = routing_info.get('assigned_agent', 'BOD_CEO_01')
            except Exception:
                intent = 'SMALL_TALK'
                target_agent_id = 'BOD_CEO_01'

            assigned_agent = AgentRegistry.objects.filter(agent_id=target_agent_id).first()
            
        # Fallback an toàn nếu chưa có agent nào trong DB
        if not assigned_agent:
            assigned_agent = AgentRegistry.objects.first()
            if not assigned_agent:
                return JsonResponse({'status': 'error', 'message': 'Chưa khởi tạo nhân sự nào trong AgentRegistry!'}, status=400)

        # Nếu là hội thoại thông thường hoặc trao đổi chiến lược
        if intent == 'SMALL_TALK' or (assigned_agent.role and assigned_agent.role.role_code == 'BOD'):
            # SỬ DỤNG DỘNG SYSTEM PROMPT TỪ DATABASE CỦA AGENT ĐÓ
            system_prompt = assigned_agent.system_prompt or f"Bạn là {assigned_agent.display_name} tại vnxBox Enterprise. Trả lời sắc bén, chuyên nghiệp."
            
            response_msg = ask_local_agent(system_prompt, f"Sếp Vũ chỉ đạo: {directive_text}")
            
            AgentDiscussion.objects.create(
                company=company, directive=directive, agent=assigned_agent,
                sender_type='AGENT', phase='SMALL_TALK', message_content=response_msg
            )
        
        # Nếu là nghiệp vụ lập trình / sinh code (CODE_DEV)
        elif intent == 'CODE_DEV' or (assigned_agent.role and assigned_agent.role.role_code in ['DEV_BE', 'ARCHITECT']):
            AgentDiscussion.objects.create(
                company=company, directive=directive, agent=assigned_agent,
                sender_type='AGENT', phase='GENERAL_DEBATE',
                message_content=f"Đã tiếp nhận yêu cầu. {assigned_agent.display_name} đang tiến hành phân rã task và lập trình tự trị..."
            )

            # LẤY SYSTEM PROMPT ĐỘNG CỦA AGENT KẾT HỢP QUY CHUẨN XUẤT FILE MULTI-FILE
            base_prompt = assigned_agent.system_prompt or f"Bạn là {assigned_agent.display_name} - Chuyên gia lập trình Vibercode."
            system_prompt = (
                f"{base_prompt}\n"
                "QUY TẮC TỐI THƯỢNG (ZERO-QUESTION, ACTION-FIRST):\n"
                "1. KHÔNG HỎI LẠI, KHÔNG VĂN VỞ.\n"
                "2. HÃY LẬP TỨC PHÂN RÃ và viết trọn bộ mã nguồn hoàn chỉnh, phân tách bằng tiêu đề:\n"
                "=== FILE: đường_dẫn_file_1 ===\n"
                "=== FILE: đường_dẫn_file_2 ===\n"
            )
            
            prompt_with_context = f"YÊU CẦU TỪ SẾP VŨ:\n{directive_text}\n\nHãy lập trình ngay lập tức."
            ai_raw_output = ask_local_agent(system_prompt, prompt_with_context, timeout_seconds=180)
            
            files_to_create = []
            if "=== FILE:" in ai_raw_output:
                chunks = ai_raw_output.split("=== FILE:")
                for chunk in chunks:
                    if not chunk.strip(): continue
                    lines = chunk.strip().split("\n")
                    raw_path = lines[0].strip()
                    
                    file_path = raw_path if raw_path else "dynamic_app/services_gen.py"
                    file_content = "\n".join(lines[1:]).strip()
                    
                    # Làm sạch block code markdown nếu có
                    for lang in ['python', 'html', 'javascript', 'json', 'sql']:
                        if f"```{lang}" in file_content:
                            file_content = file_content.split(f"```{lang}")[1].split("```")[0].strip()
                    if "```" in file_content:
                        file_content = file_content.split("```")[1].split("```")[0].strip()
                        
                    files_to_create.append((file_path, file_content))
            else:
                clean_code = ai_raw_output
                if "```" in clean_code:
                    clean_code = clean_code.split("```")[1].split("```")[0].strip()
                files_to_create.append(('dynamic_app/services_gen.py', clean_code))

            patch_summary = []
            auto_applied_count = 0
            pending_count = 0

            for f_path, f_content in files_to_create:
                # Kiểm tra ngưỡng rủi ro dựa trên cấu hình Agent hoặc loại file
                is_low_risk = f_path.endswith('.html') or 'ui' in f_path.lower() or assigned_agent.risk_threshold == 'AUTO_APPLY'
                
                if is_low_risk:
                    try:
                        file_path = os.path.join(settings.BASE_DIR, f_path)
                        backup_dir = os.path.join(settings.BASE_DIR, '.vnx_backups')
                        os.makedirs(backup_dir, exist_ok=True)
                        if os.path.exists(file_path):
                            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                            shutil.copy2(file_path, os.path.join(backup_dir, f"{os.path.basename(f_path)}.{timestamp}.bak"))

                        os.makedirs(os.path.dirname(file_path), exist_ok=True)
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(f_content)

                        CodePatchProposal.objects.create(
                            target_file=f_path,
                            proposed_by_agent=assigned_agent,
                            code_content=f_content,
                            status='APPROVED'
                        )
                        auto_applied_count += 1
                        patch_summary.append(f"`{f_path}` (Auto-Applied 🟢)")
                        continue
                    except Exception as ex:
                        print("Lỗi auto-apply, fallback về PENDING:", ex)

                # Rủi ro cao đưa vào hàng đợi chờ Sếp duyệt (PENDING)
                CodePatchProposal.objects.create(
                    target_file=f_path,
                    proposed_by_agent=assigned_agent,
                    code_content=f_content,
                    status='PENDING'
                )
                pending_count += 1
                patch_summary.append(f"`{f_path}` (Chờ duyệt 🟠)")

            final_msg = f"Đã xử lý xong: {', '.join(patch_summary)}. (Tự động áp dụng: {auto_applied_count}, Chờ Sếp duyệt: {pending_count})"
            AgentDiscussion.objects.create(
                company=company, directive=directive, agent=assigned_agent,
                sender_type='AGENT', phase='CODE_DEV', message_content=final_msg
            )

        directive.status = 'SUCCESS'
        directive.save()

        return JsonResponse({
            'status': 'success',
            'message': 'Đã xử lý chỉ đạo thành công!',
            'intent': intent
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
def api_viber_approve_patch(request):
    """API duyệt bản vá: Tự động backup file cũ trước khi ghi đè an toàn"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        patch_id = data.get('patch_id')
        
        patch = CodePatchProposal.objects.filter(id=patch_id).first()
        if not patch:
            return JsonResponse({'status': 'error', 'message': f'Không tìm thấy bản vá với ID: {patch_id}'}, status=404)
            
        if patch.status == 'APPROVED':
            return JsonResponse({'status': 'success', 'message': 'Bản vá này đã được duyệt trước đó rồi!'})

        target_file = patch.target_file
        code_content = patch.code_content
        
        file_path = target_file if os.path.isabs(target_file) else os.path.join(settings.BASE_DIR, target_file)
        
        # Cơ chế bảo hiểm tự động backup
        backup_dir = os.path.join(settings.BASE_DIR, '.vnx_backups')
        os.makedirs(backup_dir, exist_ok=True)
        if os.path.exists(file_path):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"{os.path.basename(target_file)}.{timestamp}.bak"
            shutil.copy2(file_path, os.path.join(backup_dir, backup_filename))

        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code_content)
            
        patch.status = 'APPROVED'
        patch.save()
        
        return JsonResponse({
            'status': 'success', 
            'message': f'Đã duyệt và áp dụng thành công bản vá vào file: {target_file} (Đã backup file cũ an toàn)'
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




def broadcast_to_war_room(sender_name, phase, content):
    """Hàm helper đẩy thông điệp real-time xuống WebSocket Group"""
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "live_war_room_global",
            {
                "type": "broadcast_message",
                "sender": sender_name,
                "phase": phase,
                "content": content
            }
        )
    except Exception as e:
        print("Lỗi broadcast websocket:", e)




def war_room_dashboard(view_request):
    """Render giao diện phòng họp trực tuyến (Live War Room Dashboard)"""
    company = Company.objects.first()
    agents = AgentRegistry.objects.all()
    tasks = AgentTaskDAG.objects.all().order_by('-created_at')[:20]
    
    context = {
        'company': company,
        'agents': agents,
        'tasks': tasks,
    }
    return render(view_request, 'enterprise_factory/war_room.html', context)



@csrf_exempt
def api_submit_directive(request):
    """API tiếp nhận chỉ đạo chiến lược từ Sếp, kích hoạt BOD và DAG Engine"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            directive_text = data.get('directive_text', '').strip()
            
            if not directive_text:
                return JsonResponse({'status': 'error', 'message': 'Chỉ đạo không được để trống!'}, status=400)
            
            company = Company.objects.first()
            
            # 1. Lưu chỉ đạo vào lịch sử DirectiveLog
            directive = DirectiveLog.objects.create(
                company=company,
                directive_text=directive_text,
                status='PROCESSING'
            )
            
            # 2. Kích hoạt BOD phân rã task và tự động gọi HR Spawner nếu thiếu người
            success = DAGTaskEngine.decompose_and_create(directive, company)
            
            if success:
                directive.status = 'DECOMPOSED'
                directive.save()
                return JsonResponse({'status': 'success', 'message': 'BOD đã tiếp nhận và phân rã task thành công!'})
            else:
                return JsonResponse({'status': 'warning', 'message': 'Chỉ đạo đã thực thi với task dự phòng.'})
                
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def broadcast_agent_message(sender_name, message_text, phase="DISCUSSION"):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "live_war_room_global",
        {
            "type": "broadcast_message",
            "sender": sender_name,
            "phase": phase,
            "content": message_text
        }
    )

def war_room_init_data(request):
    """API cung cấp dữ liệu khởi tạo cho Live War Room"""
    raw_agents = AgentRegistry.objects.select_related('role').all()
    agents = []
    for agent_obj in raw_agents:
        # Ưu tiên lấy role_code, nếu không có thì gán nhãn theo agent_id cho chuẩn xác
        r_code = 'GENERAL'
        if agent_obj.role:
            r_code = agent_obj.role.role_code
        elif 'BOD' in agent_obj.agent_id:
            r_code = 'BOD'
        elif 'HR' in agent_obj.agent_id:
            r_code = 'HR'
        elif 'DEV' in agent_obj.agent_id:
            r_code = 'DEV_BE'

        agents.append({
            'agent_id': agent_obj.agent_id,
            'display_name': agent_obj.display_name,
            'domain_scope': agent_obj.domain_scope,
            'role_type': r_code
        })

    # Lấy lịch sử thảo luận
    raw_discussions = AgentDiscussion.objects.values(
        'id', 'agent', 'message_content', 'created_at'
    ).order_by('-created_at')[:50]

    discussions = []
    for d in raw_discussions:
        discussions.append({
            'id': d['id'],
            'agent_name': d['agent'],
            'message_content': d['message_content'],
            'created_at': d['created_at'].strftime('%H:%M:%S') if d['created_at'] else ''
        })

    return JsonResponse({
        'agents': agents,
        'discussions': discussions,
        'patches': []
    })

def war_room_init_data(request):
    """API cung cấp dữ liệu khởi tạo cho Live War Room"""
    
    # 1. Lấy danh sách nhân sự từ DB kèm thông tin Role (Tối ưu select_related để không bị query thừa)
    raw_agents = AgentRegistry.objects.select_related('role').all()
    agents = []
    for agent_obj in raw_agents:
        agents.append({
            'agent_id': agent_obj.agent_id,
            'display_name': agent_obj.display_name,
            'domain_scope': agent_obj.domain_scope,
            # Lấy thẳng role_code từ relation đã select_related, chống query lặp
            'role_type': agent_obj.role.role_code if agent_obj.role else 'GENERAL'
        })

    # 2. Lấy lịch sử thảo luận từ DB (Sửa 'agent_name' thành 'agent' cho khớp với Model AgentDiscussion)
    raw_discussions = AgentDiscussion.objects.values(
        'id', 'agent', 'message_content', 'created_at'
    ).order_by('-created_at')[:50]

    # Map lại trường 'agent' thành 'agent_name' để Frontend nhận đúng định dạng hiển thị
    discussions = []
    for d in raw_discussions:
        discussions.append({
            'id': d['id'],
            'agent_name': d['agent'], # Đổi key từ DB thành key giao diện cần
            'message_content': d['message_content'],
            'created_at': d['created_at'].strftime('%H:%M:%S') if d['created_at'] else ''
        })

    return JsonResponse({
        'agents': agents,
        'discussions': discussions,
        'patches': [] # Danh sách bản vá code chờ duyệt nếu có
    })