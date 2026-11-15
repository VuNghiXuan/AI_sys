# enterprise_factory/views/dashboard.py
"""
Render giao diện phòng họp trực tuyến (Live War Room Dashboard) cho vnxBox Enterprise.
Tương ứng với file template: templates/enterprise_factory/war_room.html
"""

import logging
from django.shortcuts import render
from enterprise_factory.models import Company, AgentRegistry, AgentTaskDAG

logger = logging.getLogger(__name__)

def war_room_dashboard(view_request):
    """Render giao diện phòng họp trực tuyến và truyền tải context dữ liệu ban đầu"""
    logger.info("[*] [VIEW DASHBOARD] Đang render Live War Room Dashboard...")
    try:
        company = Company.objects.first()
        agents = AgentRegistry.objects.select_related('role').all()
        tasks = AgentTaskDAG.objects.select_related('assigned_agent', 'directive').all().order_by('-created_at')[:20]
        
        context = {
            'company': company,
            'agents': agents,
            'tasks': tasks,
        }
        return render(view_request, 'enterprise_factory/war_room.html', context)
    except Exception as e:
        logger.error(f"[-] [VIEW DASHBOARD ERROR]: {str(e)}", exc_info=True)
        raise e