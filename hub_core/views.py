# ==============================================================================
# File Path: hub_core/views.py
# Description: View điều phối workbench, định tuyến, graph, JIT context, repair loop, scaffold và job nền.
# Linked Files: [core/router.py, core/graph_query.py, core/jit_context.py, core/repair_runner.py, core/background_jobs.py, core/slice_scaffolder.py, slices/doc_reconcile/ui_view.py, hub_core/urls.py, hub_core/templates/hub_core/workbench.html]
# Slice Tag: [HUB_CORE: VIEWS]
# ==============================================================================

import json
import logging
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

from django.http import HttpRequest, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from core.background_jobs import get_job_manager
from core.graph_query import GraphIndexer
from core.jit_context import JITContextBuilder
from core.repair_runner import RepairLoopRunner
from core.router import TwoLayerRouter
from core.slice_scaffolder import scaffold_slice_from_prompt
from slices.doc_reconcile.ui_view import doc_reconcile_api_view
from core.slice_expander import expand_slice_from_prompt


def _ensure_diagnostic_logging() -> None:
    """Đảm bảo log chẩn đoán xuất ra cả terminal (stdout) và file logs/vnxbox.log."""
    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = str((logs_dir / "vnxbox.log").resolve())
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    target_loggers = [logging.getLogger(), logging.getLogger("vnxbox"), logging.getLogger(__name__)]
    for lg in target_loggers:
        lg.setLevel(logging.INFO)
        has_stream = any(isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler) for h in lg.handlers)
        has_file = any(
            isinstance(h, logging.FileHandler) and Path(getattr(h, "baseFilename", "")).resolve() == Path(log_file)
            for h in lg.handlers
        )
        if not has_stream:
            sh = logging.StreamHandler(sys.stdout)
            sh.setLevel(logging.INFO)
            sh.setFormatter(formatter)
            lg.addHandler(sh)
        if not has_file:
            fh = logging.FileHandler(log_file, encoding="utf-8")
            fh.setLevel(logging.INFO)
            fh.setFormatter(formatter)
            lg.addHandler(fh)


_ensure_diagnostic_logging()
logger = logging.getLogger(__name__)

DEFAULT_REPAIR_CMD = [
    sys.executable,
    "-m",
    "pytest",
    "--import-mode=importlib",
    "slices/doc_reconcile/test_doc_reconcile.py",
]


def _resolve_jit_target(raw_target_file: str, extra_notes: str, target_tag: str, default_depth: int) -> tuple[str, int]:
    """Chọn target_file và depth phù hợp cho @tao-app, @mo-rong hoặc mặc định."""
    tag = (target_tag or "").lower().strip()
    notes_lower = (extra_notes or "").lower()

    if tag in {"tao-app", "scaffold"} or "@tao-app" in notes_lower or "@scaffold" in notes_lower:
        for cand in ("core/slice_scaffolder.py", "slices/doc_reconcile/contract.py", raw_target_file):
            if Path(cand).exists():
                return cand, 0
        return raw_target_file, 0

    if tag in {"mo-rong", "mở-rộng"} or "@mo-rong" in notes_lower or "@mở-rộng" in notes_lower:
        slices_root = Path("slices")
        if slices_root.exists():
            existing_slices = [p.name for p in slices_root.iterdir() if p.is_dir() and not p.name.startswith("__")]
            for sname in sorted(existing_slices, key=len, reverse=True):
                if sname.replace("_", " ") in notes_lower or sname in notes_lower:
                    cand = f"slices/{sname}/core.py"
                    if Path(cand).exists():
                        return cand, min(default_depth, 1)
            non_doc = [p for p in slices_root.iterdir() if p.is_dir() and p.name not in {"__pycache__", "doc_reconcile"}]
            if non_doc:
                latest = max(non_doc, key=lambda p: p.stat().st_mtime)
                cand = f"slices/{latest.name}/core.py"
                if Path(cand).exists():
                    return cand, min(default_depth, 1)

    return raw_target_file, default_depth


def _execute_repair_loop(
    target_file: str,
    verify_cmd: list[str],
    use_llm: bool,
    job_id: str = "",
) -> dict[str, Any]:
    """Hàm thực thi RepairLoopRunner bên trong luồng nền và ghi log vào JobManager + file/terminal."""
    manager = get_job_manager()
    manager.update_progress(
        job_id,
        "Đang chạy vòng lặp kiểm thử & tự sửa",
        f"Khởi chạy RepairLoopRunner cho '{target_file}' (use_llm={use_llm}).",
    )
    logger.info("[repair_loop job=%s] Bắt đầu cho target_file='%s' cmd=%s", job_id, target_file, verify_cmd)
    runner = RepairLoopRunner(project_root=".")
    result = runner.run_loop(
        target_file=target_file,
        verify_cmd=list(verify_cmd),
        use_llm_suggestion=use_llm,
    )
    msg = f"Kết thúc RepairLoopRunner: success={result.success}, breaker={result.breaker_status.state}."
    manager.append_log(job_id, msg)
    logger.info("[repair_loop job=%s] %s", job_id, msg)
    return {
        "target_file": result.target_file,
        "success": result.success,
        "breaker_status": asdict(result.breaker_status),
        "context_files": result.context_files,
        "last_output": result.last_output[-2000:],
    }


def _execute_scaffold_slice(
    prompt_text: str,
    slice_name: str | None,
    overwrite: bool,
    reindex: bool,
    job_id: str = "",
) -> dict[str, Any]:
    """Chạy sinh khung lát cắt trong luồng nền và đẩy log về JobManager + file/terminal."""
    mgr = get_job_manager()
    mgr.update_progress(
        job_id,
        "Đang sinh khung lát cắt",
        f"Bắt đầu job sinh lát cắt từ prompt: '{prompt_text}'.",
    )
    logger.info(
        "[scaffold_slice job=%s] prompt='%s' slice_name=%s overwrite=%s reindex=%s",
        job_id,
        prompt_text,
        slice_name,
        overwrite,
        reindex,
    )
    try:
        res = scaffold_slice_from_prompt(
            prompt_text=prompt_text,
            project_root=".",
            slice_name=slice_name,
            overwrite=overwrite,
            reindex=reindex,
            job_id=job_id,
        )
        done_msg = f"Hoàn tất tạo lát cắt '{res.get('slice_name')}' -> {res.get('created_files')}."
        mgr.append_log(job_id, done_msg)
        logger.info("[scaffold_slice job=%s] %s", job_id, done_msg)
        return res
    except Exception as exc:
        err_msg = f"Thất bại khi sinh lát cắt: {exc}"
        mgr.append_log(job_id, err_msg)
        logger.exception("[scaffold_slice job=%s] %s", job_id, err_msg)
        raise


@require_http_methods(["GET"])
def workbench_view(request: HttpRequest):
    """Render trang làm việc chính (Workbench) kế thừa base.html và các partials."""
    logger.info("Đang render giao diện workbench cho path=%s", request.path)
    context = {
        "default_target_file": "slices/doc_reconcile/core.py",
        "default_mode": "Auto",
    }
    return render(request, "hub_core/workbench.html", context)


@require_http_methods(["GET"])
def health_check_view(request: HttpRequest) -> JsonResponse:
    """Kiểm tra trạng thái hoạt động cơ bản của hub_core."""
    return JsonResponse({"status": "ok", "service": "hub_core"})


@csrf_exempt
@require_http_methods(["POST"])
def route_prompt_view(request: HttpRequest) -> JsonResponse:
    """Định tuyến prompt 2 lớp qua TwoLayerRouter."""
    try:
        body: dict[str, Any] = json.loads(request.body.decode("utf-8") or "{}")
        prompt = str(body.get("prompt", ""))
        router = TwoLayerRouter()
        decision = router.route(prompt)
        return JsonResponse(
            {
                "status": "ok",
                "route": {
                    "mode": decision.mode,
                    "domain": decision.domain,
                    "sub_domain": decision.sub_domain,
                    "matched_keywords": decision.matched_keywords,
                    "default_tolerance": decision.default_tolerance,
                },
            }
        )
    except Exception as exc:
        logger.exception("Lỗi khi định tuyến prompt: %s", exc)
        return JsonResponse({"status": "error", "message": str(exc)}, status=500)


@require_http_methods(["GET"])
def graph_neighbors_view(request: HttpRequest) -> JsonResponse:
    """Trả về thông tin node và các file liên quan từ GraphIndexer."""
    target_file = request.GET.get("file", "slices/doc_reconcile/core.py")
    depth = int(request.GET.get("depth", "1"))
    try:
        indexer = GraphIndexer(".")
        neighbors = indexer.get_neighbors(target_file=target_file, depth=depth)
        return JsonResponse({"status": "ok", "target": target_file, "neighbors": neighbors})
    except Exception as exc:
        logger.exception("Lỗi khi truy vấn neighbors cho '%s': %s", target_file, exc)
        return JsonResponse({"status": "error", "message": str(exc)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def jit_context_view(request: HttpRequest) -> JsonResponse:
    """Gom ngữ cảnh JIT Context quanh file đích theo Impact Radius."""
    try:
        body: dict[str, Any] = json.loads(request.body.decode("utf-8") or "{}")
        raw_target = str(body.get("target_file", "slices/doc_reconcile/core.py"))
        raw_depth = int(body.get("depth", 1))
        extra_notes = str(body.get("extra_notes", ""))
        target_tag = str(body.get("target", ""))

        resolved_target, resolved_depth = _resolve_jit_target(raw_target, extra_notes, target_tag, raw_depth)
        logger.info(
            "API jit_context_view: raw_target='%s' -> target='%s' (depth=%d, tag='%s')",
            raw_target,
            resolved_target,
            resolved_depth,
            target_tag,
        )

        builder = JITContextBuilder(project_root=".")
        ctx = builder.build_context(target_file=resolved_target, depth=resolved_depth, extra_notes=extra_notes)
        return JsonResponse({"status": "ok", "context": ctx})
    except Exception as exc:
        logger.exception("Lỗi khi dựng JIT Context: %s", exc)
        return JsonResponse({"status": "error", "message": str(exc)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def repair_loop_view(request: HttpRequest) -> JsonResponse:
    """Đưa vòng lặp kiểm tra & tự sửa vào ThreadPoolExecutor và trả về job_id."""
    try:
        body: dict[str, Any] = json.loads(request.body.decode("utf-8") or "{}")
        target_file = str(body.get("target_file", "slices/doc_reconcile/core.py"))
        verify_cmd = list(body.get("verify_cmd") or DEFAULT_REPAIR_CMD)
        use_llm = bool(body.get("use_llm_suggestion", False))
        async_mode = bool(body.get("async_mode", True))
        logger.info(
            "API repair_loop_view cho '%s' (use_llm=%s, async=%s)",
            target_file,
            use_llm,
            async_mode,
        )

        manager = get_job_manager()
        created = manager.submit(
            "repair_loop",
            _execute_repair_loop,
            target_file=target_file,
            verify_cmd=verify_cmd,
            use_llm=use_llm,
            _inject_job_id=True,
        )
        job_id = str(created.get("job_id", ""))
        logger.info("Đã tạo job repair_loop job_id=%s", job_id)

        if not async_mode:
            import time

            while True:
                snap = manager.get_job(job_id, log_offset=0) or {}
                if snap.get("status") in {"completed", "failed"}:
                    return JsonResponse({"status": "ok", "job": snap})
                time.sleep(0.05)

        return JsonResponse({"status": "accepted", "job": created}, status=202)
    except Exception as exc:
        logger.exception("Lỗi khi khởi tạo job RepairLoopRunner: %s", exc)
        return JsonResponse({"status": "error", "message": str(exc)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def scaffold_app_view(request: HttpRequest) -> JsonResponse:
    """Nhận prompt @tao-app và xếp hàng sinh lát cắt chạy nền qua ThreadPoolExecutor."""
    logger.info("Nhận request POST tới scaffold_app_view")
    try:
        raw = request.body.decode("utf-8") if request.body else "{}"
        body: dict[str, Any] = json.loads(raw or "{}")
        prompt_text = str(body.get("prompt", "")).strip()
        if not prompt_text:
            logger.warning("scaffold_app_view bị từ chối: thiếu 'prompt'.")
            return JsonResponse({"status": "error", "message": "Thiếu nội dung 'prompt'."}, status=400)

        slice_name = body.get("slice_name")
        overwrite = bool(body.get("overwrite", False))
        reindex = bool(body.get("reindex", True))

        mgr = get_job_manager()
        created = mgr.submit(
            "scaffold_slice",
            _execute_scaffold_slice,
            prompt_text=prompt_text,
            slice_name=slice_name,
            overwrite=overwrite,
            reindex=reindex,
            _inject_job_id=True,
        )
        job_id = str(created.get("job_id", ""))
        logger.info("Đã tạo job sinh lát cắt job_id=%s cho prompt='%s'", job_id, prompt_text)
        return JsonResponse({"status": "accepted", "job": created}, status=202)
    except Exception as exc:
        logger.exception("Lỗi nghiêm trọng trong scaffold_app_view: %s", exc)
        return JsonResponse({"status": "error", "message": str(exc)}, status=500)


@require_http_methods(["GET"])
def job_status_view(request: HttpRequest, job_id: str) -> JsonResponse:
    """Trả về trạng thái, kết quả và log của một job nền theo job_id."""
    try:
        raw_offset = request.GET.get("offset", "0")
        log_offset = max(0, int(raw_offset))
    except ValueError:
        log_offset = 0

    job = get_job_manager().get_job(job_id=job_id, log_offset=log_offset)
    if job is None:
        logger.warning("job_status_view không tìm thấy job_id='%s'", job_id)
        return JsonResponse(
            {"status": "error", "message": f"Không tìm thấy job '{job_id}'."},
            status=404,
        )
    return JsonResponse({"status": "ok", "job": job})


@require_http_methods(["GET"])
def job_list_view(request: HttpRequest) -> JsonResponse:
    """Liệt kê danh sách các tác vụ nền gần nhất."""
    try:
        limit = max(1, min(100, int(request.GET.get("limit", "20"))))
    except ValueError:
        limit = 20

    jobs = get_job_manager().list_jobs(limit=limit)
    return JsonResponse({"status": "ok", "count": len(jobs), "jobs": jobs})

from core.slice_expander import expand_slice_from_prompt


def _execute_expand_slice(
    prompt_text: str,
    slice_name: str | None,
    reindex: bool,
    job_id: str = "",
) -> dict[str, Any]:
    """Chạy mở rộng lát cắt trong luồng nền và đẩy log về JobManager + file/terminal."""
    mgr = get_job_manager()
    mgr.update_progress(
        job_id,
        "Đang mở rộng lát cắt",
        f"Bắt đầu job mở rộng lát cắt từ prompt: '{prompt_text}'.",
    )
    logger.info("[expand_slice job=%s] prompt='%s' slice_name=%s reindex=%s", job_id, prompt_text, slice_name, reindex)
    try:
        res = expand_slice_from_prompt(
            prompt_text=prompt_text,
            project_root=".",
            slice_name=slice_name,
            reindex=reindex,
            job_id=job_id,
        )
        done_msg = f"Hoàn tất mở rộng lát cắt '{res.get('slice_name')}' -> {res.get('created_files')}."
        mgr.append_log(job_id, done_msg)
        logger.info("[expand_slice job=%s] %s", job_id, done_msg)
        return res
    except Exception as exc:
        err_msg = f"Thất bại khi mở rộng lát cắt: {exc}"
        mgr.append_log(job_id, err_msg)
        logger.exception("[expand_slice job=%s] %s", job_id, err_msg)
        raise


@csrf_exempt
@require_http_methods(["POST"])
def expand_slice_view(request: HttpRequest) -> JsonResponse:
    """Nhận prompt @mo-rong và xếp hàng mở rộng lát cắt chạy nền qua ThreadPoolExecutor."""
    logger.info("Nhận request POST tới expand_slice_view")
    try:
        raw = request.body.decode("utf-8") if request.body else "{}"
        body: dict[str, Any] = json.loads(raw or "{}")
        prompt_text = str(body.get("prompt", "")).strip()
        if not prompt_text:
            return JsonResponse({"status": "error", "message": "Thiếu nội dung 'prompt'."}, status=400)

        slice_name = body.get("slice_name")
        reindex = bool(body.get("reindex", True))

        mgr = get_job_manager()
        created = mgr.submit(
            "expand_slice",
            _execute_expand_slice,
            prompt_text=prompt_text,
            slice_name=slice_name,
            reindex=reindex,
            _inject_job_id=True,
        )
        job_id = str(created.get("job_id", ""))
        logger.info("Đã tạo job mở rộng lát cắt job_id=%s cho prompt='%s'", job_id, prompt_text)
        return JsonResponse({"status": "accepted", "job": created}, status=202)
    except Exception as exc:
        logger.exception("Lỗi nghiêm trọng trong expand_slice_view: %s", exc)
        return JsonResponse({"status": "error", "message": str(exc)}, status=500)
    
__all__ = [
    "workbench_view",
    "health_check_view",
    "route_prompt_view",
    "graph_neighbors_view",
    "jit_context_view",
    "repair_loop_view",
    "scaffold_app_view",
    "job_status_view",
    "job_list_view",
    "doc_reconcile_api_view",
    'require_http_methods',
]