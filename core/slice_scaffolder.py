# ==============================================================================
# File Path: core/slice_scaffolder.py
# Description: Sinh khung lát cắt/app mới chuẩn (<300 dòng/file) kèm header liên kết & test mẫu.
# Linked Files: [core/background_jobs.py, core/graph_indexer.py, core/logger_setup.py, hub_core/views.py]
# Slice Tag: [CORE: SLICE_SCAFFOLDER]
# ==============================================================================

import json
import logging
import re
import unicodedata
from pathlib import Path
from typing import Any

from core.background_jobs import get_job_manager
from core.graph_indexer import ProjectGraphIndexer

logger = logging.getLogger(__name__)


def _emit(job_id: str | None, msg: str, level: str = "info", progress: str | None = None) -> None:
    """Ghi log đồng thời ra hệ thống logger và log của job nền (nếu có job_id)."""
    if level == "warning":
        logger.warning("[Scaffolder] %s", msg)
    elif level == "error":
        logger.error("[Scaffolder] %s", msg)
    else:
        logger.info("[Scaffolder] %s", msg)

    if job_id:
        mgr = get_job_manager()
        if progress:
            mgr.update_progress(job_id, progress, msg)
        else:
            mgr.append_log(job_id, msg)


def slugify_slice_name(raw_text: str) -> str:
    """Chuyển mô tả prompt thành tên thư mục lát cắt hợp lệ (snake_case ASCII)."""
    cleaned = re.sub(r"@[a-zA-Z0-9_-]+", " ", raw_text or "")
    normalized = unicodedata.normalize("NFKD", cleaned)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii").lower()
    tokens = re.findall(r"[a-z0-9]+", ascii_only)
    stop_words = {"tao", "app", "moi", "cho", "he", "thong", "lam", "xay", "dung", "module"}
    meaningful = [t for t in tokens if t not in stop_words]
    chosen = meaningful[:3] if meaningful else (tokens[:3] if tokens else ["custom_app"])
    slug = "_".join(chosen)
    slug = re.sub(r"[^a-z0-9_]", "_", slug).strip("_")
    if not slug or slug[0].isdigit():
        slug = f"app_{slug or 'slice'}"
    return slug[:40]


def _build_contract_content(slug: str, prompt_text: str, tag_upper: str) -> str:
    rel = f"slices/{slug}/contract.py"
    linked = f"[slices/{slug}/core.py, slices/{slug}/ui_view.py, slices/{slug}/test_{slug}.py]"
    safe_prompt = json.dumps(prompt_text, ensure_ascii=False)
    return f'''# ==============================================================================
# File Path: {rel}
# Description: Hợp đồng dữ liệu và tham số cấu hình cho lát cắt '{slug}'.
# Linked Files: {linked}
# Slice Tag: [SLICE: {tag_upper}_CONTRACT]
# ==============================================================================

from dataclasses import dataclass, field
from typing import Any

SOURCE_PROMPT = {safe_prompt}


@dataclass
class SliceRequest:
    """Dữ liệu đầu vào chuẩn cho lát cắt {slug}."""

    payload: dict[str, Any] = field(default_factory=dict)
    options: dict[str, Any] = field(default_factory=dict)


@dataclass
class SliceResult:
    """Kết quả đầu ra chuẩn của lát cắt {slug}."""

    ok: bool
    slice_name: str
    summary: str
    data: dict[str, Any] = field(default_factory=dict)
'''


def _build_core_content(slug: str, tag_upper: str) -> str:
    rel = f"slices/{slug}/core.py"
    linked = f"[slices/{slug}/contract.py, slices/{slug}/ui_view.py, slices/{slug}/test_{slug}.py]"
    return f'''# ==============================================================================
# File Path: {rel}
# Description: Logic xử lý cốt lõi cho lát cắt '{slug}' (sẵn sàng để AI mở rộng).
# Linked Files: {linked}
# Slice Tag: [SLICE: {tag_upper}_CORE]
# ==============================================================================

import logging
from typing import Any

from slices.{slug}.contract import SOURCE_PROMPT, SliceRequest, SliceResult

logger = logging.getLogger(__name__)


def execute_slice(req: SliceRequest) -> SliceResult:
    """Thực thi luồng xử lý cơ bản của lát cắt {slug} và ghi log rõ ràng."""
    logger.info("[%s] Bắt đầu execute_slice | keys_payload=%s", "{slug}", list(req.payload.keys()))
    try:
        items_count = len(req.payload)
        result_data: dict[str, Any] = {{
            "source_prompt": SOURCE_PROMPT,
            "received_keys": list(req.payload.keys()),
            "options_used": req.options,
        }}
        logger.info("[%s] Hoàn tất execute_slice | payload_keys=%d", "{slug}", items_count)
        return SliceResult(
            ok=True,
            slice_name="{slug}",
            summary=f"Lát cắt '{slug}' đã chạy khung xử lý thành công ({{items_count}} trường dữ liệu).",
            data=result_data,
        )
    except Exception as exc:
        logger.exception("[%s] Lỗi trong execute_slice: %s", "{slug}", exc)
        return SliceResult(
            ok=False,
            slice_name="{slug}",
            summary=f"Lỗi xử lý ở lát cắt '{slug}': {{exc}}",
            data={{}},
        )
'''


def _build_ui_view_content(slug: str, tag_upper: str) -> str:
    rel = f"slices/{slug}/ui_view.py"
    linked = f"[slices/{slug}/contract.py, slices/{slug}/core.py, slices/{slug}/test_{slug}.py, hub_core/urls.py]"
    return f'''# ==============================================================================
# File Path: {rel}
# Description: Endpoint API tối giản cho lát cắt '{slug}'.
# Linked Files: {linked}
# Slice Tag: [SLICE: {tag_upper}_UI_VIEW]
# ==============================================================================

import json
import logging
from dataclasses import asdict
from typing import Any

from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from slices.{slug}.contract import SliceRequest
from slices.{slug}.core import execute_slice

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def slice_api_view(request: HttpRequest) -> JsonResponse:
    """Nhận JSON request và gọi execute_slice của lát cắt {slug}."""
    logger.info("[%s] Nhận request tới slice_api_view", "{slug}")
    try:
        raw_body = request.body.decode("utf-8") if request.body else "{{}}"
        body: dict[str, Any] = json.loads(raw_body or "{{}}")
        req = SliceRequest(
            payload=dict(body.get("payload") or body),
            options=dict(body.get("options") or {{}}),
        )
        res = execute_slice(req)
        return JsonResponse({{"status": "ok" if res.ok else "error", "result": asdict(res)}})
    except Exception as exc:
        logger.exception("[%s] Lỗi trong slice_api_view: %s", "{slug}", exc)
        return JsonResponse({{"status": "error", "message": str(exc)}}, status=500)
'''


def _build_test_content(slug: str, tag_upper: str) -> str:
    rel = f"slices/{slug}/test_{slug}.py"
    linked = f"[slices/{slug}/contract.py, slices/{slug}/core.py, slices/{slug}/ui_view.py]"
    return f'''# ==============================================================================
# File Path: {rel}
# Description: Unit test khởi đầu cho lát cắt '{slug}'.
# Linked Files: {linked}
# Slice Tag: [SLICE: {tag_upper}_TEST]
# ==============================================================================

from slices.{slug}.contract import SliceRequest
from slices.{slug}.core import execute_slice


def test_{slug}_scaffold_runs_cleanly():
    """Kiểm tra khung lát cắt {slug} chạy được và trả về kết quả hợp lệ."""
    req = SliceRequest(payload={{"sample_key": "sample_value"}}, options={{"dry_run": True}})
    result = execute_slice(req)
    assert result.ok is True
    assert result.slice_name == "{slug}"
'''


def _run_graph_indexer(indexer: Any, root: Path, job_id: str | None) -> dict[str, Any] | None:
    """Gọi phương thức build_map (hoặc method index tương thích) của ProjectGraphIndexer."""
    candidate_methods = [
        "build_map",
        "load_or_build_map",
        "build_and_save",
        "build_index",
        "index_project",
        "scan_and_save",
        "scan_project",
        "run",
        "build",
        "save",
    ]
    for method_name in candidate_methods:
        fn = getattr(indexer, method_name, None)
        if callable(fn):
            _emit(job_id, f"Gọi ProjectGraphIndexer.{method_name}()...")
            try:
                out = fn()
            except TypeError:
                out = fn(str(root))

            if isinstance(out, dict):
                map_path = getattr(indexer, "map_path", None)
                if map_path:
                    try:
                        p = Path(map_path)
                        if not p.exists():
                            p.parent.mkdir(parents=True, exist_ok=True)
                            p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
                            _emit(job_id, f"Đã lưu bản đồ đồ thị vào '{p}'.")
                    except Exception as save_exc:
                        _emit(job_id, f"Cảnh báo khi kiểm tra/ghi map_path '{map_path}': {save_exc}", level="warning")
                return out.get("summary") or {"method": method_name, "keys": list(out.keys())}
            return {"method": method_name, "status": "ok"}

    available = [m for m in dir(indexer) if not m.startswith("_")]
    raise AttributeError(
        f"ProjectGraphIndexer không có method index quen thuộc ({candidate_methods}). "
        f"Public attrs hiện có: {available}"
    )


def scaffold_slice_from_prompt(
    prompt_text: str,
    project_root: str = ".",
    slice_name: str | None = None,
    overwrite: bool = False,
    reindex: bool = True,
    job_id: str | None = None,
) -> dict[str, Any]:
    """Sinh bộ file lát cắt chuẩn (<300 dòng/file) và tùy chọn cập nhật PROJECT_MAP.json."""
    root = Path(project_root).resolve()
    _emit(
        job_id,
        f"Bước 1/4: Phân tích prompt '{prompt_text}' tại root='{root}'.",
        progress="Bước 1/4: Phân tích tên lát cắt",
    )

    slug = slugify_slice_name(slice_name or prompt_text)
    tag_upper = slug.upper()
    slice_dir = root / "slices" / slug
    _emit(job_id, f"Bước 1/4 xong: slug='{slug}', thư mục đích='{slice_dir}'.")

    if slice_dir.exists() and not overwrite:
        err_msg = f"Thư mục '{slice_dir}' đã tồn tại và overwrite=False. Dừng để tránh ghi đè ngoài ý muốn."
        _emit(job_id, err_msg, level="error", progress="Lỗi: Thư mục đã tồn tại")
        raise FileExistsError(err_msg)

    _emit(
        job_id,
        f"Bước 2/4: Tạo thư mục '{slice_dir}' và sinh 4 file chuẩn.",
        progress="Bước 2/4: Sinh file khung",
    )
    slice_dir.mkdir(parents=True, exist_ok=True)

    files_to_write: dict[str, str] = {
        "contract.py": _build_contract_content(slug, prompt_text, tag_upper),
        "core.py": _build_core_content(slug, tag_upper),
        "ui_view.py": _build_ui_view_content(slug, tag_upper),
        f"test_{slug}.py": _build_test_content(slug, tag_upper),
    }

    created_files: list[str] = []
    line_stats: dict[str, int] = {}

    for fname, content in files_to_write.items():
        fpath = slice_dir / fname
        rel_str = f"slices/{slug}/{fname}"
        try:
            fpath.write_text(content, encoding="utf-8")
            line_cnt = len(content.splitlines())
            line_stats[rel_str] = line_cnt
            created_files.append(rel_str)
            _emit(job_id, f"Đã ghi '{rel_str}' ({line_cnt} dòng, limit=300).")
            if line_cnt > 300:
                _emit(job_id, f"CẢNH BÁO: '{rel_str}' vượt 300 dòng ({line_cnt})!", level="warning")
        except Exception as exc:
            _emit(job_id, f"Lỗi khi ghi file '{rel_str}': {exc}", level="error", progress="Lỗi ghi file")
            raise

    graph_summary: dict[str, Any] | None = None
    if reindex:
        _emit(job_id, "Bước 3/4: Quét AST & cập nhật PROJECT_MAP.json...", progress="Bước 3/4: Cập nhật Graph")
        try:
            indexer = ProjectGraphIndexer(project_root=str(root))
            graph_summary = _run_graph_indexer(indexer, root, job_id)
            _emit(job_id, f"Bước 3/4 xong: PROJECT_MAP.json cập nhật -> {graph_summary}.")
        except Exception as exc:
            _emit(job_id, f"Lỗi khi chạy ProjectGraphIndexer: {exc}", level="error", progress="Lỗi cập nhật Graph")
            raise
    else:
        _emit(job_id, "Bước 3/4: Bỏ qua cập nhật PROJECT_MAP.json theo cấu hình reindex=False.")

    _emit(
        job_id,
        f"Bước 4/4 hoàn tất: Đã tạo lát cắt '{slug}' với {len(created_files)} file.",
        progress="4/4 Hoàn tất",
    )
    return {
        "slice_name": slug,
        "slice_dir": str(slice_dir.relative_to(root)),
        "created_files": created_files,
        "line_counts": line_stats,
        "graph_summary": graph_summary,
    }