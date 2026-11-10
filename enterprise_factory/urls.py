# File: enterprise_factory/urls.py
from django.urls import path
from .views import command_center_view, api_get_enterprise_state, api_submit_directive

urlpatterns = [
    path('war-room/', command_center_view, name='command_center'),
    path('api/state/', api_get_enterprise_state, name='api_enterprise_state'),
    path('api/submit/', api_submit_directive, name='api_submit_directive'),
]