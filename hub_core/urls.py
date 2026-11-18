"""
# File Path: hub_core/urls.py
# Purpose: Định tuyến URL bao gồm cả API xem nhanh file code.
"""
from django.urls import path
from .views import dashboard_view, job_detail_view, job_stream_view, file_content_api, delete_job_api

app_name = 'hub_core'

urlpatterns = [
    path('', dashboard_view, name='dashboard'),
    path('job/<uuid:job_id>/', job_detail_view, name='job_detail'),
    path('job/<uuid:job_id>/stream/', job_stream_view, name='job_stream'),
    path('api/file-content/', file_content_api, name='file_content_api'),
    # ➔ BỔ SUNG ĐƯỜNG DẪN API XÓA JOB NÀY VÀO:
    path('api/job/<uuid:job_id>/delete/', delete_job_api, name='delete_job_api'),
]