# ============================================================================
# File Path: chat_ui/views.py
# Module: View Render Giao Dien Va Endpoint JSON Cho Chat UI
# Linked Files: chat_ui/services.py,
#               core_policy/loader.py
# Purpose: Phuc vu trang giao dien chat/dieu phoi va xu ly request POST /api/chat.
# ============================================================================

from __future__ import annotations

import json
from typing import Any

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from core_policy.loader import tai_cau_hinh_chien_thuat

from .services import xu_ly_prompt_chat


@require_GET
@ensure_csrf_cookie
def trang_chu(request: HttpRequest) -> HttpResponse:
    """Hien thi giao dien chinh kem profile va ngan sach hien hanh."""
    policy = tai_cau_hinh_chien_thuat(bat_buoc_tai_lai=True)
    budget = policy.lay_ngan_sach_hieu_luc()
    return render(
        request,
        "chat_ui/layout/index.html",
        {
            "active_profile": policy.active_profile,
            "profiles": list(policy.profiles.keys()),
            "max_step_tokens": budget.max_total_tokens_per_step,
            "max_llm_calls": budget.max_llm_calls_per_turn,
            "max_output_files": policy.file_limits.max_output_files_per_turn,
        },
    )


@require_POST
def api_chat(request: HttpRequest) -> JsonResponse:
    """Nhan prompt tu UI va tra ve ket qua dieu phoi, token, provider va kiem chung."""
    try:
        payload: dict[str, Any] = json.loads(request.body.decode("utf-8") or "{}")
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"error": "JSON payload không hợp lệ."}, status=400)

    prompt = str(payload.get("prompt") or "")
    ghi_tep = bool(payload.get("ghi_tep", False))
    ket_qua = xu_ly_prompt_chat(prompt=prompt, ghi_tep=ghi_tep)
    return JsonResponse(ket_qua)