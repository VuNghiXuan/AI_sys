# ==============================================================================
# File Path: hub_core/urls.py
# Description: Khai báo URL routes cho workbench, hub_core, job nền và lát cắt doc_reconcile.
# Linked Files: [hub_core/views.py, core/background_jobs.py, slices/doc_reconcile/ui_view.py, hub_core/templates/hub_core/workbench.html]
# Slice Tag: [HUB_CORE: URLS]
# ==============================================================================

from django.urls import path

from hub_core.views import (
    doc_reconcile_api_view,
    graph_neighbors_view,
    health_check_view,
    jit_context_view,
    job_list_view,
    job_status_view,
    repair_loop_view,
    route_prompt_view,
    scaffold_app_view,
    workbench_view,
    expand_slice_view,
)

urlpatterns = [
    path("", workbench_view, name="vnxbox_workbench"),
    path("workbench/", workbench_view, name="vnxbox_workbench_alias"),
    path("health/", health_check_view, name="vnxbox_health"),
    path("route/", route_prompt_view, name="vnxbox_route"),
    path("graph/neighbors/", graph_neighbors_view, name="vnxbox_graph_neighbors"),
    path("context/jit/", jit_context_view, name="vnxbox_jit_context"),
    path("repair/run/", repair_loop_view, name="vnxbox_repair_run"),
    path("slices/scaffold/", scaffold_app_view, name="vnxbox_slice_scaffold"),
    path("jobs/", job_list_view, name="vnxbox_job_list"),
    path("jobs/<str:job_id>/", job_status_view, name="vnxbox_job_status"),
    path("slices/doc-reconcile/", doc_reconcile_api_view, name="vnxbox_doc_reconcile"),
    path("slices/expand/", expand_slice_view, name="vnxbox_slice_expand"),
]