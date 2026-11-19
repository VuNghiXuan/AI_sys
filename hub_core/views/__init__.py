# ==========================================
# File Path: hub_core/views/__init__.py
# Module: Views Package Export
# Linked Files: [hub_core/views/dashboard_views.py, hub_core/views/stream_api_views.py, hub_core/urls.py]
# Purpose: Xuất các view và API chính để tương thích với cấu hình urls.py hiện tại.
# ==========================================

from .dashboard_views import (
    run_pipeline_background,
    dashboard_view,
    job_detail_view,
)
from .stream_api_views import (
    file_content_api,
    job_stream_view,
    delete_job_api,
)

__all__ = [
    "run_pipeline_background",
    "dashboard_view",
    "job_detail_view",
    "file_content_api",
    "job_stream_view",
    "delete_job_api",
]