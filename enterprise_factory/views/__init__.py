# File: enterprise_factory/__init__.py
default_app_config = 'enterprise_factory.apps.EnterpriseFactoryConfig'

# enterprise_factory/views.py
"""
Views điều phối Live War Room & Xử lý chỉ đạo tự động cho vnxBox Enterprise.
File cầu nối tổng hợp các module con trong thư mục views/ phục vụ Django URL routing.
"""

from .dashboard import war_room_dashboard
from .state_api import api_viber_state, war_room_init_data, api_war_room_feedback
from .directive_api import api_submit_directive, api_viber_execute_directive, api_init_war_room_data
from .patch_api import api_viber_approve_patch, api_viber_reject_patch

__all__ = [
    'war_room_dashboard',
    'api_viber_state',
    'war_room_init_data',
    'api_submit_directive',
    'api_viber_execute_directive',
    'api_viber_approve_patch',
    'api_viber_reject_patch',
    'api_init_war_room_data',
    'api_war_room_feedback'
]