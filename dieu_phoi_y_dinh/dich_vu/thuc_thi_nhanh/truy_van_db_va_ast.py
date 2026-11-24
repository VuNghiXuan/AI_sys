# ============================================================================
# File Path: dieu_phoi_y_dinh/dich_vu/thuc_thi_nhanh/truy_van_db_va_ast.py
# Module: Truy Van DB Linh Dong, Telemetry Va Quet AST Du An
# Linked Files: dieu_phoi_y_dinh/dich_vu/thuc_thi_nhanh/trinh_xu_ly_chung.py,
#               quan_ly_du_an/services_telemetry.py,
#               PROJECT_MAP_COMPACT.md,
#               PROJECT_MAP.md
# Purpose: Sinh bang DB (so sanh theo app hoac liet ke/thong ke theo model),
#          xuat telemetry/model, doc ban do file va quet AST ham/bien thuc te.
# ============================================================================

import ast
from collections import defaultdict
import logging
from pathlib import Path
import re

from django.apps import apps

from quan_ly_du_an.services_telemetry import thu_thap_telemetry_thuc_te

logger = logging.getLogger(__name__)

MAX_TRUONG_MODEL_HIEN_THI = 8
MAX_KY_TU_MAP_NGU_CANH = 4000
MAX_TEP_QUET_AST = 80
MAX_MUC_LIET_KE_MOI_LOAI = 25
TEN_TEP_MAP_COMPACT = "PROJECT_MAP_COMPACT.md"
TEN_TEP_MAP_GOC = "PROJECT_MAP.md"
THU_MUC_BO_QUA_AST = {".venv", "venv", ".git", "__pycache__", "migrations", "node_modules"}

MAU_YEU_CAU_BANG = re.compile(
    r"\b(?:thành\s+bảng|lập\s+bảng|dạng\s+bảng|kẻ\s+bảng|tạo\s+bảng|so\s+sánh|đối\s+chiếu)\b",
    flags=re.IGNORECASE,
)


def doc_tom_tat_project_map(goc_du_an: Path) -> str:
    """Doc PROJECT_MAP_COMPACT.md (hoac fallback PROJECT_MAP.md) lam ngu canh cau truc."""
    for ten_tep in (TEN_TEP_MAP_COMPACT, TEN_TEP_MAP_GOC):
        tep_map = goc_du_an / ten_tep
        if not tep_map.is_file():
            continue
        try:
            noi_dung = tep_map.read_text(encoding="utf-8", errors="replace").strip()
        except Exception as loi:
            logger.warning("Khong doc duoc %s: %s", tep_map, loi)
            continue
        if noi_dung:
            return noi_dung[:MAX_KY_TU_MAP_NGU_CANH]
    return ""


def liet_ke_file_he_thong_nhanh(goc_du_an: Path) -> str:
    """Doc nhanh danh sach file tu PROJECT_MAP_COMPACT.md/PROJECT_MAP.md (fallback quet tep)."""
    tom_tat = doc_tom_tat_project_map(goc_du_an)
    if tom_tat:
        return f"📂 **Danh sách file hệ thống (từ bản đồ dự án):**\n\n{tom_tat[:2500]}"
    ds_tep = [
        f"- `{p.relative_to(goc_du_an).as_posix()}`"
        for p in sorted(goc_du_an.rglob("*.py"))
        if not any(part in THU_MUC_BO_QUA_AST for part in p.parts)
    ][:40]
    return "📂 **Danh sách file hệ thống:**\n" + ("\n".join(ds_tep) if ds_tep else "- Chưa tìm thấy file.")


def quet_ham_va_bien_du_an(goc_du_an: Path) -> str:
    """Quet AST cac tep .py trong du an de liet ke ham va bien cap module thuc te."""
    logger.info("Bat dau quet AST ham va bien tai %s", goc_du_an)
    ds_ham: list[str] = []
    ds_bien: list[str] = []
    so_tep = 0

    for tep in sorted(goc_du_an.rglob("*.py")):
        if any(part in THU_MUC_BO_QUA_AST for part in tep.parts):
            continue
        so_tep += 1
        if so_tep > MAX_TEP_QUET_AST:
            break
        try:
            cay = ast.parse(tep.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError as loi:
            logger.warning("Bo qua tep loi cu phap khi quet AST %s: %s", tep, loi)
            continue

        rel_tep = tep.relative_to(goc_du_an).as_posix()
        for node in cay.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("__"):
                if len(ds_ham) < MAX_MUC_LIET_KE_MOI_LOAI:
                    doc = (ast.get_docstring(node) or "").splitlines()[0].strip() if ast.get_docstring(node) else ""
                    ds_ham.append(f"- `{rel_tep}`: `{node.name}()`" + (f" — {doc}" if doc else ""))
            elif isinstance(node, ast.Assign) and len(ds_bien) < MAX_MUC_LIET_KE_MOI_LOAI:
                for target in node.targets:
                    if isinstance(target, ast.Name) and not target.id.startswith("_"):
                        ds_bien.append(f"- `{rel_tep}`: `{target.id}`")
                        break

    return "\n".join([
        f"🧩 **Tổng hợp hàm & biến thực tế trong dự án** (đã quét {min(so_tep, MAX_TEP_QUET_AST)} tệp `.py`):",
        "",
        "**Hàm tiêu biểu:**",
        *(ds_ham or ["- Chưa phát hiện hàm tiêu biểu."]),
        "",
        "**Biến cấp module tiêu biểu:**",
        *(ds_bien or ["- Chưa phát hiện biến tiêu biểu."]),
    ])


def _dinh_dang_telemetry_va_model(cau_hoi: str = "") -> str:
    """Tong hop thong so may va model Ollama (ho tro bang linh dong khi prompt yeu cau)."""
    logger.info("Thu thap telemetry va danh sach model Ollama.")
    data = thu_thap_telemetry_thuc_te() or {}
    cpu = data.get("cpu") or {}
    ram = data.get("ram") or {}
    gpu = data.get("gpu") or {}
    ollama = data.get("ollama") or {}

    cpu_pct = cpu.get("usage_pct") if cpu.get("usage_pct") is not None else "N/A"
    ram_pct = ram.get("usage_pct") if ram.get("usage_pct") is not None else "N/A"
    ds_chay = [f"`{m.get('name')}` ({m.get('mem_gb')} GB)" for m in ollama.get("running_models") or []]
    ds_cai = [f"`{m.get('name')}` ({m.get('size_gb')} GB)" for m in ollama.get("installed_models") or []]

    if MAU_YEU_CAU_BANG.search(cau_hoi or ""):
        return "\n".join([
            "🖥️ **Bảng thông số máy & Model Ollama thực tế:**",
            "",
            "| Thành phần | Giá trị hiện tại | Chi tiết / Trạng thái |",
            "| --- | --- | --- |",
            f"| CPU | {cpu.get('name', 'CPU')} | {cpu.get('threads', '?')} luồng · Tải {cpu_pct}% |",
            f"| RAM | {ram.get('used_gb', '?')} / {ram.get('total_gb', '?')} GB | Mức dùng {ram_pct}% |",
            f"| GPU | {gpu.get('label', 'N/A')} | {gpu.get('detail', '')} |",
            f"| Model đang chạy | {', '.join(ds_chay) if ds_chay else 'Không có'} | {ollama.get('message', '')} |",
            f"| Model đã cài | {', '.join(ds_cai) if ds_cai else 'Không có'} | Danh sách `/api/tags` |",
        ])

    return "\n".join([
        "🖥️ **Thông số máy & Model Ollama thực tế:**",
        f"- **CPU:** {cpu.get('name', 'CPU')} ({cpu.get('threads', '?')} luồng) · Tải: {cpu_pct}%",
        f"- **RAM:** {ram.get('used_gb', '?')} / {ram.get('total_gb', '?')} GB ({ram_pct}%)",
        f"- **GPU:** {gpu.get('label', 'N/A')} — {gpu.get('detail', '')}",
        f"- **Ollama:** {ollama.get('message', '')}",
        f"- **Đang chạy (`/api/ps`):** {', '.join(ds_chay) if ds_chay else 'Không có'}",
        f"- **Đã cài (`/api/tags`):** {', '.join(ds_cai) if ds_cai else 'Không có'}",
    ])


def _so_sanh_cac_app_db() -> str:
    """Tong hop va so sanh cac app Django theo so model, tong ban ghi va danh sach model."""
    thong_ke_app: dict[str, dict[str, Any]] = defaultdict(lambda: {"models": [], "tong_ban_ghi": 0})
    for model in apps.get_models():
        app_ten = model._meta.app_label
        try:
            so_luong = model.objects.count()
        except Exception as loi:
            logger.warning("Khong dem duoc ban ghi model %s: %s", model.__name__, loi)
            so_luong = 0
        thong_ke_app[app_ten]["models"].append(model.__name__)
        if so_luong > 0:
            thong_ke_app[app_ten]["tong_ban_ghi"] += so_luong

    dong = [
        "⚖️ **So sánh các App trong hệ thống:**",
        "",
        "| App | Số Model | Tổng bản ghi | Các Model chính |",
        "| --- | ---: | ---: | --- |",
    ]
    for app_ten, info in thong_ke_app.items():
        ds_m = info["models"]
        mo_ta_m = ", ".join(f"`{m}`" for m in ds_m[:5]) + (f" (+{len(ds_m) - 5})" if len(ds_m) > 5 else "")
        dong.append(f"| `{app_ten}` | {len(ds_m)} | {info['tong_ban_ghi']} | {mo_ta_m} |")
    logger.info("Da sinh bang so sanh %d app trong DB.", len(thong_ke_app))
    return "\n".join(dong)


def _chon_cot_bang_db(cau_hoi: str, dem_ban_ghi: bool) -> list[str]:
    """Tuy chon cac cot bang DB linh dong theo tu khoa trong cau hoi."""
    q = (cau_hoi or "").lower()
    if dem_ban_ghi:
        cot = ["App", "Model", "Số bản ghi"]
        if any(k in q for k in ("trường", "truong", "cột", "cot", "field")):
            cot.append("Số trường")
        if any(k in q for k in ("trạng thái", "trang thai", "có dữ liệu", "co du lieu", "rỗng", "rong")):
            cot.append("Trạng thái dữ liệu")
        return cot

    cot = ["App", "Model"]
    if any(k in q for k in ("bản ghi", "ban ghi", "dòng", "dong", "số lượng", "so luong")):
        cot.append("Số bản ghi")
    if any(k in q for k in ("kiểu", "kieu", "type", "chi tiết", "chi tiet")):
        cot.append("Trường & kiểu dữ liệu")
    else:
        cot.append("Các trường chính")
    if any(k in q for k in ("số trường", "so truong", "bao nhiêu trường")):
        cot.append("Số trường")
    return cot


def _lap_bang_model_db(dem_ban_ghi: bool, cau_hoi: str = "") -> str:
    """Lap bang Markdown DB linh dong theo tieu chi cau hoi."""
    q = (cau_hoi or "").lower()
    if re.search(r"\b(?:so\s+sánh|đối\s+chiếu)\b", q) and "app" in q and "model" not in q:
        return _so_sanh_cac_app_db()

    cac_cot = _chon_cot_bang_db(cau_hoi, dem_ban_ghi)
    tieu_de = "📊 **Thống kê số lượng bản ghi theo Model (DB):**" if dem_ban_ghi else "🗄️ **Danh sách App & Model trong hệ thống:**"
    dong = [
        tieu_de,
        "",
        "| " + " | ".join(cac_cot) + " |",
        "| " + " | ".join("---:" if c in {"Số bản ghi", "Số trường"} else "---" for c in cac_cot) + " |",
    ]
    tong_ban_ghi = 0
    for model in apps.get_models():
        try:
            so_luong = model.objects.count()
        except Exception as loi:
            logger.warning("Khong dem duoc ban ghi model %s: %s", model.__name__, loi)
            so_luong = -1
        if so_luong > 0:
            tong_ban_ghi += so_luong

        cac_truong = list(model._meta.fields[:MAX_TRUONG_MODEL_HIEN_THI])
        gia_tri_cot: dict[str, str] = {
            "App": f"`{model._meta.app_label}`",
            "Model": f"`{model.__name__}`",
            "Số bản ghi": str(so_luong),
            "Số trường": str(len(model._meta.fields)),
            "Các trường chính": "`" + ", ".join(f.name for f in cac_truong) + "`",
            "Trường & kiểu dữ liệu": ", ".join(f"`{f.name}` ({f.get_internal_type()})" for f in cac_truong),
            "Trạng thái dữ liệu": "Có dữ liệu" if so_luong > 0 else ("Rỗng" if so_luong == 0 else "Lỗi đọc"),
        }
        dong.append("| " + " | ".join(gia_tri_cot[c] for c in cac_cot) + " |")

    if dem_ban_ghi:
        dong.append(f"\n*Tổng bản ghi ở các model có dữ liệu: **{tong_ban_ghi}**.*")
    return "\n".join(dong)


def truy_van_db_django(muc_tieu: str, cau_hoi: str = "") -> str:
    """Truy van truc tiep Django apps, models, truong du lieu hoac telemetry/model."""
    if muc_tieu == "telemetry_va_model":
        return _dinh_dang_telemetry_va_model(cau_hoi=cau_hoi)
    try:
        logger.info("Truy van DB Django voi muc_tieu=%s", muc_tieu)
        return _lap_bang_model_db(dem_ban_ghi=(muc_tieu == "dem_ban_ghi_model"), cau_hoi=cau_hoi)
    except Exception as loi:
        logger.error("Loi truy van DB trong truy_van_db_va_ast: %s", loi, exc_info=True)
        return f"❌ Không truy vấn được dữ liệu DB: {loi}"