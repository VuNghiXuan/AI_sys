# File: enterprise_factory/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('war-room/', views.war_room_dashboard, name='war_room'),
    path('', views.war_room_dashboard, name='war_room_root'),
    
    # Đảm bảo các API endpoint này nằm đầy đủ trong urls.py
    path('api/viber/state/', views.api_viber_state, name='api_viber_state'),
    path('api/viber/execute/', views.api_viber_execute_directive, name='api_viber_execute'),
    path('api/viber/approve/', views.api_viber_approve_patch, name='api_viber_approve'),
    path('api/viber/reject/', views.api_viber_reject_patch, name='api_viber_reject'),
    path('api/war-room/init-data/', views.war_room_init_data, name='war_room_init_data'),
]
