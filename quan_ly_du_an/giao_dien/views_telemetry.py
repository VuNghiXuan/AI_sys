# ============================================================================
# File Path: quan_ly_du_an/views_telemetry.py
# Module: Telemetry API View
# Linked Files: services_telemetry.py, urls.py
# Purpose: Tra ve du lieu CPU, RAM, GPU va model Ollama thuc te dang JSON.
# ============================================================================

from django.http import JsonResponse
from django.views.decorators.http import require_GET

from quan_ly_du_an.services_telemetry import thu_thap_telemetry_thuc_te


@require_GET
def api_telemetry_thuc_te(request):
    """Endpoint tra ve thong so phan cung va model Ollama thuc te."""
    data = thu_thap_telemetry_thuc_te()
    return JsonResponse(data)