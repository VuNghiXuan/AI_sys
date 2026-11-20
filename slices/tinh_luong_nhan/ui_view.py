# ==============================================================================
# File Path: slices/tinh_luong_nhan/ui_view.py
# Description: Endpoint API cho lát cắt 'tinh_luong_nhan' (hỗ trợ payload, rules, options).
# Linked Files: [slices/tinh_luong_nhan/contract.py, slices/tinh_luong_nhan/core.py, slices/tinh_luong_nhan/test_tinh_luong_nhan.py, hub_core/urls.py]
# Slice Tag: [SLICE: TINH_LUONG_NHAN_UI_VIEW]
# ==============================================================================

import json
import logging
from dataclasses import asdict
from typing import Any

from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from slices.tinh_luong_nhan.contract import SliceRequest
from slices.tinh_luong_nhan.core import execute_slice

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def slice_api_view(request: HttpRequest) -> JsonResponse:
    """Nhận JSON request và gọi execute_slice mở rộng của lát cắt tinh_luong_nhan."""
    logger.info("[%s] Nhận request tới slice_api_view", "tinh_luong_nhan")
    try:
        raw_body = request.body.decode("utf-8") if request.body else "{}"
        body: dict[str, Any] = json.loads(raw_body or "{}")
        req = SliceRequest(
            payload=dict(body.get("payload") or body),
            rules=dict(body.get("rules") or {}),
            options=dict(body.get("options") or {}),
        )
        res = execute_slice(req)
        return JsonResponse({"status": "ok" if res.ok else "error", "result": asdict(res)})
    except Exception as exc:
        logger.exception("[%s] Lỗi trong slice_api_view: %s", "tinh_luong_nhan", exc)
        return JsonResponse({"status": "error", "message": str(exc)}, status=500)
