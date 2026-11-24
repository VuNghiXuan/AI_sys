# ============================================================================
# File Path: xuong_tao_app/giao_dien/api_xuong_tao_app.py
# Module: Bo API Thao Tac Tung Buoc Cho Xuong Tao App
# Linked Files: ../dich_vu/quet_thu_muc/quet_thu_muc_nguon.py,
#               ../dich_vu/thiet_ke_va_task/tom_tat_va_thiet_ke.py,
#               ../dich_vu/thiet_ke_va_task/chia_task_nguyen_tu.py,
#               ../dich_vu/sinh_ma_sandbox/thuc_thi_sinh_sandbox.py,
#               ../dich_vu/tu_sua_va_nang_cap/vong_lap_tu_sua.py,
#               ../dich_vu/tu_sua_va_nang_cap/khoanh_vung_va_sao_luu.py,
#               ../dich_vu/dang_ky_tab_app/nap_app_vao_he_thong.py
# Purpose: Cung cap cac endpoint JSON cho tung buoc tren trang xuong_tao_app
#          va luu trang thai phien lam viec hien tai trong session.
# ============================================================================

import json
import logging
from pathlib import Path
from typing import Any

from django.conf import settings
from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_POST

from xuong_tao_app.dich_vu.dang_ky_tab_app.nap_app_vao_he_thong import (
    nap_app_vao_khung_he_thong,
)
from xuong_tao_app.dich_vu.quet_thu_muc.quet_thu_muc_nguon import (
    quet_va_doc_thu_muc,
)
from xuong_tao_app.dich_vu.sinh_ma_sandbox.thuc_thi_sinh_sandbox import (
    sinh_ma_cho_danh_sach_task,
)
from xuong_tao_app.dich_vu.thiet_ke_va_task.chia_task_nguyen_tu import (
    chia_task_tu_thiet_ke,
)
from xuong_tao_app.dich_vu.thiet_ke_va_task.tom_tat_va_thiet_ke import (
    lap_ban_thiet_ke_app,
)
from xuong_tao_app.dich_vu.tu_sua_va_nang_cap.khoanh_vung_va_sao_luu import (
    hoan_tac_tu_ban_sao_luu,
)
from xuong_tao_app.dich_vu.tu_sua_va_nang_cap.vong_lap_tu_sua import (
    sua_hoac_nang_cap_tu_phan_hoi,
)

logger = logging.getLogger(__name__)

SESSION_KEY_PHIEN_XUONG = "xuong_tao_app_phien_lam_viec"


def _lay_thu_muc_goc_du_an() -> Path:
    """Lay thu muc goc du an tu settings.BASE_DIR."""
    base_dir = getattr(settings, "BASE_DIR", None)
    return Path(base_dir).resolve() if base_dir else Path.cwd().resolve()


def _doc_body_json(request: HttpRequest) -> dict[str, Any]:
    """Doc JSON body an toan, tra dict rong neu loi."""
    try:
        raw = (request.body or b"").decode("utf-8")
        data = json.loads(raw) if raw.strip() else {}
        return data if isinstance(data, dict) else {}
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        logger.warning("Body JSON khong hop le: %s", exc)
        return {}


def _lay_phien(request: HttpRequest) -> dict[str, Any]:
    """Lay trang thai phien lam viec hien tai tu session."""
    session = getattr(request, "session", None)
    if not session:
        return {}
    du_lieu = session.get(SESSION_KEY_PHIEN_XUONG)
    return du_lieu if isinstance(du_lieu, dict) else {}


def _luu_phien(request: HttpRequest, du_lieu: dict[str, Any]) -> None:
    """Cap nhat trang thai phien lam viec vao session."""
    session = getattr(request, "session", None)
    if not session:
        return
    session[SESSION_KEY_PHIEN_XUONG] = du_lieu
    session.modified = True


@require_POST
def api_quet_va_thiet_ke(request: HttpRequest) -> JsonResponse:
    """Buoc 1 + 2: Quet thu muc nguon, lap ban thiet ke va chia task nguyen tu."""
    body = _doc_body_json(request)
    duong_dan = str(body.get("duong_dan_nguon") or "").strip()
    prompt_goc = str(body.get("prompt_goc") or "").strip()

    kq_quet = quet_va_doc_thu_muc(duong_dan)
    if not kq_quet.get("hop_le"):
        return JsonResponse({"thanh_cong": False, "thong_bao": kq_quet.get("loi") or "Thu muc khong hop le."}, status=400)

    tep_da_doc = kq_quet.get("tep_da_doc") or []
    ban_thiet_ke = lap_ban_thiet_ke_app(prompt_goc=prompt_goc, tep_da_doc=tep_da_doc)
    danh_sach_task = chia_task_tu_thiet_ke(ban_thiet_ke)

    tom_tat_nguon = "\n".join(
        f"[{t.get('ten_tep')}]: {(t.get('noi_dung') or '')[:800]}" for t in tep_da_doc[:10]
    )

    phien_moi = {
        "duong_dan_nguon": kq_quet.get("duong_dan_nguon", duong_dan),
        "prompt_goc": prompt_goc,
        "ma_app": ban_thiet_ke.get("ten_app_goi_y", "app_nghiep_vu_moi"),
        "tieu_de_tab": ban_thiet_ke.get("tieu_de_tab", "App Nghiệp Vụ"),
        "tom_tat_nguon": tom_tat_nguon,
        "ban_thiet_ke": ban_thiet_ke,
        "danh_sach_task": danh_sach_task,
        "so_lan_sua": 0,
        "snapshot_gan_nhat": "",
    }
    _luu_phien(request, phien_moi)
    logger.info("Hoan tat quet & thiet ke cho app '%s' (%d task)", phien_moi["ma_app"], len(danh_sach_task))

    return JsonResponse({
        "thanh_cong": True,
        "quet": {
            "tong_so_tep_da_doc": kq_quet.get("tong_so_tep_da_doc", 0),
            "tong_ky_tu": kq_quet.get("tong_ky_tu", 0),
        },
        "ban_thiet_ke": ban_thiet_ke,
        "danh_sach_task": danh_sach_task,
    })


@require_POST
def api_sinh_code_sandbox(request: HttpRequest) -> JsonResponse:
    """Buoc 3: Sinh code cac task vao moi truong test rieng."""
    body = _doc_body_json(request)
    phien = _lay_phien(request)

    danh_sach_task = body.get("danh_sach_task") or phien.get("danh_sach_task") or []
    ban_thiet_ke = body.get("ban_thiet_ke") or phien.get("ban_thiet_ke") or {}
    tom_tat_nguon = str(phien.get("tom_tat_nguon") or "")

    if not danh_sach_task:
        return JsonResponse({"thanh_cong": False, "thong_bao": "Chua co danh sach task de sinh code."}, status=400)

    kq_sinh = sinh_ma_cho_danh_sach_task(
        danh_sach_task=danh_sach_task,
        ban_thiet_ke=ban_thiet_ke,
        thu_muc_goc_du_an=_lay_thu_muc_goc_du_an(),
        tom_tat_nguon=tom_tat_nguon,
    )
    return JsonResponse({"thanh_cong": True, **kq_sinh})


@require_POST
def api_sua_hoac_nang_cap(request: HttpRequest) -> JsonResponse:
    """Buoc 4a: Sua loi hoac nang cap theo phan hoi + mo ta anh tren moi truong test."""
    body = _doc_body_json(request)
    phien = _lay_phien(request)

    ma_app = str(body.get("ma_app") or phien.get("ma_app") or "").strip()
    prompt_phan_hoi = str(body.get("prompt_phan_hoi") or "").strip()
    mo_ta_anh = str(body.get("mo_ta_anh") or "").strip()
    log_loi = str(body.get("log_loi") or "").strip()

    if not ma_app:
        return JsonResponse({"thanh_cong": False, "thong_bao": "Chua xac dinh ma_app can sua/nang cap."}, status=400)

    so_lan_da_thu = int(phien.get("so_lan_sua") or 0)
    kq_sua = sua_hoac_nang_cap_tu_phan_hoi(
        thu_muc_goc_du_an=_lay_thu_muc_goc_du_an(),
        ma_app=ma_app,
        prompt_phan_hoi=prompt_phan_hoi,
        mo_ta_anh=mo_ta_anh,
        log_loi=log_loi,
        so_lan_da_thu=so_lan_da_thu,
    )

    phien["so_lan_sua"] = int(kq_sua.get("so_lan_da_thu") or so_lan_da_thu)
    if kq_sua.get("ma_snapshot"):
        phien["snapshot_gan_nhat"] = str(kq_sua["ma_snapshot"])
    _luu_phien(request, phien)

    return JsonResponse(kq_sua)


@require_POST
def api_hoan_tac_ban_luu(request: HttpRequest) -> JsonResponse:
    """Buoc 4b: Hoan tac tep tren moi truong test ve ban sao luu gan nhat."""
    body = _doc_body_json(request)
    phien = _lay_phien(request)

    ma_app = str(body.get("ma_app") or phien.get("ma_app") or "").strip()
    ma_snapshot = str(body.get("ma_snapshot") or phien.get("snapshot_gan_nhat") or "").strip()

    if not ma_app or not ma_snapshot:
        return JsonResponse({"thanh_cong": False, "thong_bao": "Thieu ma_app hoac ban sao luu de hoan tac."}, status=400)

    kq_hoan_tac = hoan_tac_tu_ban_sao_luu(
        thu_muc_goc_du_an=_lay_thu_muc_goc_du_an(),
        ma_app=ma_app,
        ma_snapshot=ma_snapshot,
    )
    if kq_hoan_tac.get("thanh_cong"):
        phien["so_lan_sua"] = 0
        _luu_phien(request, phien)

    return JsonResponse(kq_hoan_tac)


@require_POST
def api_nap_vao_tab_he_thong(request: HttpRequest) -> JsonResponse:
    """Buoc 5: Nap app da test on vao he thong thanh 1 tab chinh + cac chuc nang con."""
    body = _doc_body_json(request)
    phien = _lay_phien(request)
    ban_thiet_ke = phien.get("ban_thiet_ke") or {}

    ma_app = str(body.get("ma_app") or phien.get("ma_app") or "").strip()
    tieu_de_tab = str(body.get("tieu_de_tab") or phien.get("tieu_de_tab") or ma_app).strip()
    chuc_nang_con = body.get("chuc_nang_con") or ban_thiet_ke.get("chuc_nang_con") or []
    da_test_on = bool(body.get("da_test_on", True))

    if not ma_app:
        return JsonResponse({"thanh_cong": False, "thong_bao": "Chua xac dinh ma_app de nap vao tab he thong."}, status=400)

    kq_nap = nap_app_vao_khung_he_thong(
        thu_muc_goc_du_an=_lay_thu_muc_goc_du_an(),
        ma_app=ma_app,
        tieu_de_tab=tieu_de_tab,
        chuc_nang_con=chuc_nang_con,
        yeu_cau_da_test_on=da_test_on,
    )
    return JsonResponse(kq_nap)