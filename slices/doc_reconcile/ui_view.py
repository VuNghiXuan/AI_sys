# ==============================================================================
# File Path: slices/doc_reconcile/ui_view.py
# Description: Định dạng kết quả đối soát và cung cấp Django API view cho doc_reconcile.
# Linked Files: [slices/doc_reconcile/contract.py, slices/doc_reconcile/core.py, slices/doc_reconcile/test_doc_reconcile.py, hub_core/urls.py, hub_core/views.py]
# Slice Tag: [SLICE: DOC_RECONCILE_UI_VIEW]
# ==============================================================================

import json
import logging
from typing import Any

from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from slices.doc_reconcile.contract import ReconcileReport, build_config_from_dict
from slices.doc_reconcile.core import reconcile_records

logger = logging.getLogger(__name__)


def format_reconcile_summary(report: ReconcileReport) -> dict[str, Any]:
    """Trả về payload tóm tắt và danh sách dòng cần lưu ý cho UI/API."""
    actionable = [
        {
            "key": item.key_value,
            "status": item.status,
            "message": item.message,
            "diffs": item.diffs,
        }
        for item in report.items
        if item.status != "MATCHED"
    ]
    return {
        "summary": {
            "total_source": report.total_source,
            "total_target": report.total_target,
            "matched": report.matched_count,
            "within_tolerance": report.within_tolerance_count,
            "mismatch": report.mismatch_count,
            "missing_target": report.missing_target_count,
            "extra_target": report.extra_target_count,
        },
        "actionable_items": actionable,
    }


@csrf_exempt
@require_http_methods(["GET", "POST"])
def doc_reconcile_api_view(request: HttpRequest) -> JsonResponse:
    """Endpoint đối soát chứng từ/bảng kê theo cấu hình khóa và ngưỡng sai số."""
    try:
        payload: dict[str, Any] = {}
        if request.body:
            payload = json.loads(request.body.decode("utf-8"))

        cfg = build_config_from_dict(payload.get("config"))
        source_rows = payload.get("source_rows") or []
        target_rows = payload.get("target_rows") or []

        report = reconcile_records(source_rows=source_rows, target_rows=target_rows, config=cfg)
        result = format_reconcile_summary(report)
        return JsonResponse({"status": "ok", "data": result}, status=200)
    except json.JSONDecodeError:
        logger.warning("Payload JSON không hợp lệ tại doc_reconcile_api_view.")
        return JsonResponse({"status": "error", "message": "JSON body không hợp lệ."}, status=400)
    except Exception as exc:
        logger.exception("Lỗi hệ thống khi xử lý doc_reconcile_api_view: %s", exc)
        return JsonResponse({"status": "error", "message": str(exc)}, status=500)