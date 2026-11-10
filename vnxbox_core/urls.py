# File: vnxbox_core/urls.py
from django.contrib import admin
from django.urls import path
from enterprise_factory import views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Route chính trỏ vào Live War Room
    path('', views.war_room_view, name='war_room'),
    
    # Các API endpoints phục vụ cho Viber Room & Alpine.js
    path('api/viber/state/', views.api_viber_state, name='api_viber_state'),
    path('api/viber/execute/', views.api_viber_execute_directive, name='api_viber_execute'),
    path('api/viber/approve/', views.api_viber_approve_patch, name='api_viber_approve'),
]