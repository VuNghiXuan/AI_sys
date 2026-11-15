"""
API tiếp nhận chỉ đạo chiến lược từ Sếp, kích hoạt BOD, Intent Router và DAG Task Engine.
Tương ứng với form nhập chỉ đạo trên giao diện War Room, đồng thời cung cấp dữ liệu khởi tạo tháp động.
"""

import logging
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from enterprise_factory.models import Company, DirectiveLog
from enterprise_factory.services.dag_executor import DAGTaskEngine
from enterprise_factory.models import ToolRegistry, WorkflowBlueprint, AgentRegistry

logger = logging.getLogger(__name__)

@csrf_exempt
def api_submit_directive(request):
    """API tiếp nhận chỉ đạo chiến lược, khởi tạo DirectiveLog và kích hoạt DAG Engine"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        directive_text = data.get('directive_text', '').strip()
        
        if not directive_text:
            return JsonResponse({'status': 'error', 'message': 'Chỉ đạo không được để trống!'}, status=400)
        
        company = Company.objects.first()
        
        directive = DirectiveLog.objects.create(
            company=company,
            directive_text=directive_text,
            status='PROCESSING'
        )
        
        logger.info(f"[*] [API DIRECTIVE] Đang phân rã chỉ đạo ID #{directive.id} qua DAG Engine...")
        success = DAGTaskEngine.decompose_and_create(directive, company)
        
        if success:
            directive.status = 'DECOMPOSED'
            directive.save()
            return JsonResponse({'status': 'success', 'message': 'BOD đã tiếp nhận và phân rã task thành công!'})
        else:
            return JsonResponse({'status': 'warning', 'message': 'Chỉ đạo đã thực thi với task dự phòng.'})
            
    except Exception as e:
        logger.error(f"[-] [API DIRECTIVE ERROR]: {str(e)}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
def api_viber_execute_directive(request):
    """API bổ trợ xử lý chỉ đạo trực tiếp (Legacy/Compat Endpoint)"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
    return api_submit_directive(request)


@csrf_exempt
def api_init_war_room_data(request):
    """Cung cấp toàn bộ danh sách Công cụ (ToolRegistry), Quy trình (WorkflowBlueprint) và Nhân sự AI cho giao diện Live War Room"""
    try:
        tools = list(ToolRegistry.objects.filter(is_active=True).values('tool_name', 'display_name', 'description'))
        workflows = list(WorkflowBlueprint.objects.filter(is_active=True).values('workflow_code', 'workflow_name', 'dag_steps_json'))
        agents = list(AgentRegistry.objects.values('agent_id', 'display_name', 'domain_scope', 'version'))
        
        return JsonResponse({
            "status": "success",
            "tools": tools,
            "workflows": workflows,
            "agents": agents
        })
    except Exception as e:
        logger.error(f"[-] [API INIT DATA ERROR]: {str(e)}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)