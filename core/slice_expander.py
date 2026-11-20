# ==============================================================================
# File Path: core/slice_expander.py
# Description: Phân tích & mở rộng lát cắt hiện có (<300 dòng/file), cập nhật test & Graph.
# Linked Files: [core/background_jobs.py, core/graph_indexer.py, core/slice_scaffolder.py, hub_core/views.py]
# Slice Tag: [CORE: SLICE_EXPANDER]
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
        logger.warning("[Expander] %s", msg)
    elif level == "error":
        logger.error("[Expander] %s", msg)
    else:
        logger.info("[Expander] %s", msg)

    if job_id:
        mgr = get_job_manager()
        if progress:
            mgr.update_progress(job_id, progress, msg)
        else:
            mgr.append_log(job_id, msg)


def _normalize_ascii(text: str) -> str:
    """Chuẩn hóa chuỗi tiếng Việt có dấu sang ASCII thường để đối khớp tên lát cắt."""
    cleaned = re.sub(r"@[a-zA-Z0-9_-]+", " ", text or "")
    norm = unicodedata.normalize("NFKD", cleaned)
    return norm.encode("ascii", "ignore").decode("ascii").lower()


def resolve_target_slice(prompt_text: str, project_root: Path, explicit_slice: str | None = None) -> str:
    """Xác định tên lát cắt cần mở rộng theo tham số rõ ràng, tên khớp trong slices/ hoặc lát cắt mới nhất."""
    slices_dir = project_root / "slices"
    if not slices_dir.exists():
        raise FileNotFoundError(f"Không tìm thấy thư mục lát cắt '{slices_dir}'.")

    available = sorted(
        [p.name for p in slices_dir.iterdir() if p.is_dir() and not p.name.startswith("__")],
    )
    if not available:
        raise FileNotFoundError("Chưa có lát cắt nào trong thư mục slices/ để mở rộng.")

    if explicit_slice and explicit_slice.strip():
        candidate = explicit_slice.strip()
        if candidate in available:
            return candidate
        raise FileNotFoundError(f"Không tìm thấy lát cắt '{candidate}' trong {available}.")

    ascii_prompt = _normalize_ascii(prompt_text)
    prompt_tokens = set(re.findall(r"[a-z0-9]+", ascii_prompt))

    best_slug: str | None = None
    best_score = 0
    for slug in available:
        slug_tokens = set(slug.split("_"))
        overlap = len(prompt_tokens & slug_tokens)
        phrase_hit = 2 if slug.replace("_", " ") in ascii_prompt else 0
        score = overlap + phrase_hit
        if score > best_score:
            best_score = score
            best_slug = slug

    if best_slug and best_score > 0:
        return best_slug

    non_default = [
        slices_dir / s
        for s in available
        if s != "doc_reconcile"
    ]
    if non_default:
        latest = max(non_default, key=lambda p: p.stat().st_mtime)
        return latest.name

    return available[0]


def _build_expanded_contract(slug: str, tag_upper: str, existing_prompt: str, expansion_note: str) -> str:
    """Sinh bản contract.py mở rộng hỗ trợ cấu hình tham số/quy tắc động từ đầu vào."""
    rel = f"slices/{slug}/contract.py"
    linked = f"[slices/{slug}/core.py, slices/{slug}/ui_view.py, slices/{slug}/test_{slug}.py]"
    safe_source = json.dumps(existing_prompt, ensure_ascii=False)
    safe_expand = json.dumps(expansion_note, ensure_ascii=False)
    return f'''# ==============================================================================
# File Path: {rel}
# Description: Hợp đồng dữ liệu mở rộng (hỗ trợ cấu hình tham số & quy tắc) cho '{slug}'.
# Linked Files: {linked}
# Slice Tag: [SLICE: {tag_upper}_CONTRACT]
# ==============================================================================

from dataclasses import dataclass, field
from typing import Any

SOURCE_PROMPT = {safe_source}
LAST_EXPANSION_PROMPT = {safe_expand}


@dataclass
class SliceRequest:
    """Dữ liệu đầu vào chuẩn cho lát cắt {slug}."""

    payload: dict[str, Any] = field(default_factory=dict)
    rules: dict[str, Any] = field(default_factory=dict)
    options: dict[str, Any] = field(default_factory=dict)


@dataclass
class SliceResult:
    """Kết quả đầu ra chuẩn của lát cắt {slug}."""

    ok: bool
    slice_name: str
    summary: str
    data: dict[str, Any] = field(default_factory=dict)
'''


def _build_expanded_core(slug: str, tag_upper: str) -> str:
    """Sinh bản core.py mở rộng: chuẩn hóa bản ghi, áp dụng cấu hình quy tắc truyền vào & tổng hợp."""
    rel = f"slices/{slug}/core.py"
    linked = f"[slices/{slug}/contract.py, slices/{slug}/ui_view.py, slices/{slug}/test_{slug}.py]"
    return f'''# ==============================================================================
# File Path: {rel}
# Description: Logic xử lý cốt lõi đã mở rộng cho lát cắt '{slug}' (<300 dòng).
# Linked Files: {linked}
# Slice Tag: [SLICE: {tag_upper}_CORE]
# ==============================================================================

import logging
from typing import Any

from slices.{slug}.contract import LAST_EXPANSION_PROMPT, SOURCE_PROMPT, SliceRequest, SliceResult

logger = logging.getLogger(__name__)


def _extract_records(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Chuẩn hóa danh sách bản ghi từ payload (hỗ trợ cả 'records'/'items' hoặc dict đơn)."""
    for key in ("records", "items", "entries"):
        raw_list = payload.get(key)
        if isinstance(raw_list, list):
            return [item if isinstance(item, dict) else {{"value": item}} for item in raw_list]
    return [dict(payload)] if payload else []


def _apply_numeric_rules(record: dict[str, Any], rules: dict[str, Any]) -> dict[str, Any]:
    """Áp dụng các hệ số/quy tắc cấu hình truyền vào lên từng bản ghi (không hardcode công thức)."""
    enriched = dict(record)
    multipliers = rules.get("multipliers") or {{}}
    additions = rules.get("additions") or {{}}

    for field_name, factor in multipliers.items():
        if field_name in enriched and isinstance(enriched[field_name], (int, float)):
            try:
                enriched[f"{{field_name}}_adjusted"] = round(float(enriched[field_name]) * float(factor), 4)
            except (TypeError, ValueError):
                logger.warning("[%s] Bỏ qua multiplier không hợp lệ cho '%s'", "{slug}", field_name)

    for field_name, bonus in additions.items():
        if field_name in enriched and isinstance(enriched[field_name], (int, float)):
            try:
                enriched[f"{{field_name}}_plus_rule"] = round(float(enriched[field_name]) + float(bonus), 4)
            except (TypeError, ValueError):
                logger.warning("[%s] Bỏ qua addition không hợp lệ cho '%s'", "{slug}", field_name)

    return enriched


def execute_slice(req: SliceRequest) -> SliceResult:
    """Thực thi luồng xử lý mở rộng của lát cắt {slug} và ghi log chi tiết."""
    logger.info("[%s] Bắt đầu execute_slice (expanded) | keys=%s", "{slug}", list(req.payload.keys()))
    try:
        raw_records = _extract_records(req.payload)
        processed_records = [_apply_numeric_rules(rec, req.rules) for rec in raw_records]
        result_data: dict[str, Any] = {{
            "source_prompt": SOURCE_PROMPT,
            "last_expansion_prompt": LAST_EXPANSION_PROMPT,
            "record_count": len(processed_records),
            "records": processed_records,
            "rules_applied": list((req.rules or {{}}).keys()),
            "options_used": req.options,
        }}
        logger.info("[%s] Hoàn tất execute_slice | records=%d", "{slug}", len(processed_records))
        return SliceResult(
            ok=True,
            slice_name="{slug}",
            summary=f"Lát cắt '{slug}' đã xử lý mở rộng {{len(processed_records)}} bản ghi thành công.",
            data=result_data,
        )
    except Exception as exc:
        logger.exception("[%s] Lỗi trong execute_slice: %s", "{slug}", exc)
        return SliceResult(
            ok=False,
            slice_name="{slug}",
            summary=f"Lỗi xử lý mở rộng ở lát cắt '{slug}': {{exc}}",
            data={{}},
        )
'''


def _build_expanded_ui_view(slug: str, tag_upper: str) -> str:
    """Cập nhật ui_view.py để truyền cả payload, rules và options vào SliceRequest."""
    rel = f"slices/{slug}/ui_view.py"
    linked = f"[slices/{slug}/contract.py, slices/{slug}/core.py, slices/{slug}/test_{slug}.py, hub_core/urls.py]"
    return f'''# ==============================================================================
# File Path: {rel}
# Description: Endpoint API cho lát cắt '{slug}' (hỗ trợ payload, rules, options).
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
    """Nhận JSON request và gọi execute_slice mở rộng của lát cắt {slug}."""
    logger.info("[%s] Nhận request tới slice_api_view", "{slug}")
    try:
        raw_body = request.body.decode("utf-8") if request.body else "{{}}"
        body: dict[str, Any] = json.loads(raw_body or "{{}}")
        req = SliceRequest(
            payload=dict(body.get("payload") or body),
            rules=dict(body.get("rules") or {{}}),
            options=dict(body.get("options") or {{}}),
        )
        res = execute_slice(req)
        return JsonResponse({{"status": "ok" if res.ok else "error", "result": asdict(res)}})
    except Exception as exc:
        logger.exception("[%s] Lỗi trong slice_api_view: %s", "{slug}", exc)
        return JsonResponse({{"status": "error", "message": str(exc)}}, status=500)
'''


def _build_expanded_test(slug: str, tag_upper: str) -> str:
    """Cập nhật unit test kiểm tra luồng mở rộng của lát cắt."""
    rel = f"slices/{slug}/test_{slug}.py"
    linked = f"[slices/{slug}/contract.py, slices/{slug}/core.py, slices/{slug}/ui_view.py]"
    return f'''# ==============================================================================
# File Path: {rel}
# Description: Unit test cho lát cắt '{slug}' sau khi mở rộng.
# Linked Files: {linked}
# Slice Tag: [SLICE: {tag_upper}_TEST]
# ==============================================================================

from slices.{slug}.contract import SliceRequest
from slices.{slug}.core import execute_slice


def test_{slug}_expanded_records_and_rules():
    """Kiểm tra lát cắt {slug} xử lý danh sách bản ghi và quy tắc cấu hình."""
    req = SliceRequest(
        payload={{"records": [{{"name": "NV_01", "base_amount": 100}}]}},
        rules={{"multipliers": {{"base_amount": 1.2}}, "additions": {{"base_amount": 10}}}},
        options={{"mode": "expanded_check"}},
    )
    res = execute_slice(req)
    assert res.ok is True
    assert res.data["record_count"] == 1
    assert res.data["records"][0]["base_amount_adjusted"] == 120.0
    assert res.data["records"][0]["base_amount_plus_rule"] == 110.0
'''


def _reindex_graph(root: Path, job_id: str | None) -> dict[str, Any] | None:
    """Cập nhật lại PROJECT_MAP.json qua ProjectGraphIndexer.build_map()."""
    indexer = ProjectGraphIndexer(project_root=str(root))
    out = indexer.build_map()
    if isinstance(out, dict):
        return out.get("summary") or {{"keys": list(out.keys())}}
    return {{"status": "ok"}}


def expand_slice_from_prompt(
    prompt_text: str,
    project_root: str = ".",
    slice_name: str | None = None,
    reindex: bool = True,
    job_id: str | None = None,
) -> dict[str, Any]:
    """Đọc lát cắt đích, nâng cấp contract/core/ui_view/test (<300 dòng/file) và cập nhật Graph."""
    root = Path(project_root).resolve()
    _emit(
        job_id,
        f"Bước 1/4: Phân tích yêu cầu mở rộng '{prompt_text}'.",
        progress="Bước 1/4: Xác định lát cắt đích",
    )

    slug = resolve_target_slice(prompt_text, root, explicit_slice=slice_name)
    tag_upper = slug.upper()
    slice_dir = root / "slices" / slug
    _emit(job_id, f"Bước 1/4 xong: lát cắt mục tiêu='{slug}' tại '{slice_dir}'.")

    contract_path = slice_dir / "contract.py"
    existing_prompt = ""
    if contract_path.exists():
        raw_contract = contract_path.read_text(encoding="utf-8")
        m = re.search(r"SOURCE_PROMPT\s*=\s*(.+)", raw_contract)
        if m:
            try:
                existing_prompt = str(json.loads(m.group(1).strip()))
            except Exception:
                existing_prompt = m.group(1).strip()

    _emit(
        job_id,
        f"Bước 2/4: Nâng cấp khung xử lý & test cho lát cắt '{slug}' (<300 dòng/file).",
        progress="Bước 2/4: Nâng cấp file lát cắt",
    )

    updated_files: dict[str, str] = {
        "contract.py": _build_expanded_contract(slug, tag_upper, existing_prompt, prompt_text),
        "core.py": _build_expanded_core(slug, tag_upper),
        "ui_view.py": _build_expanded_ui_view(slug, tag_upper),
        f"test_{slug}.py": _build_expanded_test(slug, tag_upper),
    }

    written_files: list[str] = []
    line_stats: dict[str, int] = {}

    for fname, content in updated_files.items():
        fpath = slice_dir / fname
        rel_str = f"slices/{slug}/{fname}"
        fpath.write_text(content, encoding="utf-8")
        line_cnt = len(content.splitlines())
        line_stats[rel_str] = line_cnt
        written_files.append(rel_str)
        _emit(job_id, f"Đã cập nhật '{rel_str}' ({line_cnt} dòng, limit=300).")
        if line_cnt > 300:
            _emit(job_id, f"CẢNH BÁO: '{rel_str}' vượt 300 dòng ({line_cnt})!", level="warning")

    graph_summary: dict[str, Any] | None = None
    if reindex:
        _emit(job_id, "Bước 3/4: Quét lại AST & cập nhật PROJECT_MAP.json...", progress="Bước 3/4: Cập nhật Graph")
        graph_summary = _reindex_graph(root, job_id)
        _emit(job_id, f"Bước 3/4 xong: PROJECT_MAP.json -> {graph_summary}.")
    else:
        _emit(job_id, "Bước 3/4: Bỏ qua cập nhật PROJECT_MAP.json theo reindex=False.")

    _emit(
        job_id,
        f"Bước 4/4 hoàn tất: Đã mở rộng lát cắt '{slug}' ({len(written_files)} file).",
        progress="4/4 Hoàn tất",
    )
    return {
        "slice_name": slug,
        "slice_dir": str(slice_dir.relative_to(root)),
        "created_files": written_files,
        "line_counts": line_stats,
        "graph_summary": graph_summary,
    }