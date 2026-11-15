# enterprise_factory/views/state_api.py
"""
API cung cấp trạng thái nhân sự, lịch sử thảo luận và bản vá code chờ duyệt.
Tương ứng với file JS frontend: war_room_progress.js & war_room.js
"""

import logging
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from enterprise_factory.models import AgentRegistry, AgentDiscussion, CodePatchProposal

logger = logging.getLogger(__name__)

def api_viber_state(request):
    """API trả về danh sách nhân sự hiện tại của tập đoàn"""
    agents_list = []
    try:
        for a in AgentRegistry.objects.select_related('role').all():
            agents_list.append({
                'agent_id': getattr(a, 'agent_id', ''),
                'display_name': getattr(a, 'display_name', ''),
                'title_name': getattr(a, 'title_name', ''),
                'avatar_url': getattr(a, 'avatar_url', ''),
                'role__role_code': a.role.role_code if (hasattr(a, 'role') and a.role) else 'UNKNOWN',
                'version': getattr(a, 'version', '1.0.0'),
                'domain_scope': getattr(a, 'domain_scope', '')
            })
    except Exception as e:
        logger.error(f"[-] [API STATE ERROR] Lỗi query agents: {str(e)}", exc_info=True)

    return JsonResponse({'status': 'success', 'agents': agents_list})


def war_room_init_data(request):
    """API cung cấp dữ liệu toàn diện khởi tạo cho Live War Room (Nhân sự, Thảo luận, Bản vá)"""
    try:
        # 1. Danh sách nhân sự
        raw_agents = AgentRegistry.objects.select_related('role').all()
        agents = []
        for agent_obj in raw_agents:
            r_code = agent_obj.role.role_code if agent_obj.role else 'GENERAL'
            agents.append({
                'agent_id': agent_obj.agent_id,
                'display_name': agent_obj.display_name,
                'title_name': agent_obj.title_name or '',
                'avatar_url': agent_obj.avatar_url or '',
                'domain_scope': agent_obj.domain_scope,
                'role_type': r_code
            })

        # 2. Lịch sử thảo luận (Chuẩn model mới: sender_type, agent foreign key)
        raw_discussions = AgentDiscussion.objects.select_related('agent').order_by('-created_at')[:50]
        discussions = []
        for d in raw_discussions:
            discussions.append({
                'id': d.id,
                'sender_type': d.sender_type,
                'sender': d.get_sender_display_name(),
                'agent_name': d.agent.display_name if d.agent else '',
                'message_content': d.message_content,
                'phase': d.phase,
                'created_at': d.created_at.strftime('%H:%M:%S') if d.created_at else ''
            })

        # 3. Bản vá code chờ duyệt (PENDING)
        pending_patches = CodePatchProposal.objects.filter(status='PENDING').values('id', 'target_file', 'status', 'created_at')
        patches = [{
            'id': p['id'],
            'target_file': p['target_file'],
            'status': p['status'],
            'created_at': p['created_at'].strftime('%H:%M:%S') if p['created_at'] else ''
        } for p in pending_patches]

        return JsonResponse({'agents': agents, 'discussions': discussions, 'patches': patches})
    except Exception as e:
        logger.error(f"[-] [INIT DATA ERROR]: {str(e)}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
def api_war_room_feedback(request):
    """API ghi nhận phản hồi Self-Learning Feedback từ Sếp"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            feedback_type = data.get('feedback_type')
            message_content = data.get('content')
            agent_name = data.get('agent_name')
            
            logger.info(f"[+] [FEEDBACK RECEIVED] Type: {feedback_type} | Agent: {agent_name} | Content: {message_content[:50]}...")
            
            # TODO: Lưu log feedback vào bảng SelfLearningMemory hoặc AgentFeedback nếu cần
            
            return JsonResponse({'status': 'success', 'message': 'Đã ghi nhận feedback thành công'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)