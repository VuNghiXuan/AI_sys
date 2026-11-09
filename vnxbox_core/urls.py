# File: vnxbox_core/urls.py
from django.contrib import admin
from django.urls import path
from enterprise_factory import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index_view, name='index'),
    path('api/agents/', views.api_get_agents, name='api_get_agents'), # <--- Thêm dấu / ở cuối
    path('api/apps', views.api_get_apps, name='api_get_apps'),
    path('api/logs', views.api_get_logs, name='api_get_logs'),
    
    # Endpoints cho luồng AI Boardroom 4 bước
    path('api/boardroom/debate', views.api_boardroom_debate, name='api_boardroom_debate'),
    path('api/boardroom/matrix', views.api_boardroom_matrix, name='api_boardroom_matrix'),
    path('api/orchestrate', views.api_orchestrate, name='api_orchestrate'),
]