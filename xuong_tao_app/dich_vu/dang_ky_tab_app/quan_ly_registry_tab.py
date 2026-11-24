# ============================================================================
# File Path: xuong_tao_app/dich_vu/dang_ky_tab_app/quan_ly_registry_tab.py
# Module: Quan Ly File Registry Cau Hinh Tab App & Chuc Nang Con
# Linked Files: nap_app_vao_he_thong.py
# Purpose: Doc va ghi cau hinh tab app da dang ky (1 tab chinh + cac chuc nang
#          con) ra file JSON thay vi hardcode danh sach tab trong code.
# ============================================================================

import json
import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

TEN_FILE_REGISTRY_MAC_DINH = "config/tab_apps_da_dang_ky.json"


def lay_duong_dan_registry(thu_muc_goc_du_an: Path) -> Path:
    """Tra ve duong dan file JSON luu danh sach tab app da dang ky."""
    return (thu_muc_goc_du_an / TEN_FILE_REGISTRY_MAC_DINH).resolve()


def _chuan_hoa_ma(ma: str) -> str:
    """Chuan hoa ma tab/chuc nang con thanh dinh dang snake_case an toan."""
    sach = re.sub(r"[^a-z0-9_]+", "_", (ma or "").strip().lower()).strip("_")
    return sach or "chuc_nang_con"


def _chuan_hoa_chuc_nang_con(ds_chuc_nang: list[Any]) -> list[dict[str, str]]:
    """Chuan hoa danh sach chuc nang con hien thi tren 1 tab app."""
    ket_qua: list[dict[str, str]] = []
    ma_da_dung: set[str] = set()

    for idx, item in enumerate(ds_chuc_nang or [], start=1):
        if isinstance(item, dict):
            ten = str(item.get("ten") or item.get("tieu_de") or f"Chức năng {idx}").strip()
            ma_goc = _chuan_hoa_ma(str(item.get("ma") or ten))
            mo_ta = str(item.get("mo_ta") or "").strip()
        else:
            ten = str(item).strip() or f"Chức năng {idx}"
            ma_goc = _chuan_hoa_ma(ten)
            mo_ta = ""

        ma_duy_nhat = ma_goc
        if ma_duy_nhat in ma_da_dung:
            ma_duy_nhat = f"{ma_goc}_{idx}"
        ma_da_dung.add(ma_duy_nhat)

        ket_qua.append({
            "ma": ma_duy_nhat,
            "ten": ten,
            "mo_ta": mo_ta,
        })

    return ket_qua


def doc_danh_sach_tab_app(thu_muc_goc_du_an: Path) -> list[dict[str, Any]]:
    """Doc danh sach cac tab app da dang ky tu file JSON."""
    tep_registry = lay_duong_dan_registry(thu_muc_goc_du_an)
    if not tep_registry.exists():
        logger.debug("Chua co file registry tab app tai '%s'", tep_registry)
        return []

    try:
        du_lieu = json.loads(tep_registry.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.error("Loi doc file registry tab app '%s': %s", tep_registry, exc, exc_info=True)
        return []

    if isinstance(du_lieu, dict):
        ds = du_lieu.get("tabs")
        return ds if isinstance(ds, list) else []
    return du_lieu if isinstance(du_lieu, list) else []


def _ghi_danh_sach_tab_app(thu_muc_goc_du_an: Path, danh_sach_tab: list[dict[str, Any]]) -> bool:
    """Ghi danh sach tab app ra file JSON an toan."""
    tep_registry = lay_duong_dan_registry(thu_muc_goc_du_an)
    try:
        tep_registry.parent.mkdir(parents=True, exist_ok=True)
        noi_dung = json.dumps({"tabs": danh_sach_tab}, ensure_ascii=False, indent=2) + "\n"
        tep_registry.write_text(noi_dung, encoding="utf-8")
        logger.info("Da cap nhat registry tab app (%d tab) tai '%s'", len(danh_sach_tab), tep_registry)
        return True
    except OSError as exc:
        logger.error("Loi ghi file registry tab app '%s': %s", tep_registry, exc, exc_info=True)
        return False


def luu_hoac_cap_nhat_tab_app(
    thu_muc_goc_du_an: Path,
    ma_app: str,
    tieu_de_tab: str,
    chuc_nang_con: list[Any],
    duong_dan_ung_dung: str = "",
    nguon_tu_sandbox: str = "",
) -> dict[str, Any]:
    """Them moi hoac cap nhat 1 tab app kem danh sach chuc nang con vao registry."""
    ma_tab = _chuan_hoa_ma(ma_app)
    tieu_de = (tieu_de_tab or "").strip() or ma_tab
    ds_chuc_nang = _chuan_hoa_chuc_nang_con(chuc_nang_con)

    tab_moi: dict[str, Any] = {
        "ma_tab": ma_tab,
        "tieu_de_tab": tieu_de,
        "duong_dan_ung_dung": (duong_dan_ung_dung or f"/ung-dung/{ma_tab}/").strip(),
        "nguon_tu_sandbox": (nguon_tu_sandbox or "").strip(),
        "chuc_nang_con": ds_chuc_nang,
        "kich_hoat": True,
    }

    danh_sach_hien_tai = doc_danh_sach_tab_app(thu_muc_goc_du_an)
    da_ton_tai = False
    for idx, tab in enumerate(danh_sach_hien_tai):
        if isinstance(tab, dict) and _chuan_hoa_ma(str(tab.get("ma_tab") or "")) == ma_tab:
            danh_sach_hien_tai[idx] = tab_moi
            da_ton_tai = True
            break

    if not da_ton_tai:
        danh_sach_hien_tai.append(tab_moi)

    if not _ghi_danh_sach_tab_app(thu_muc_goc_du_an, danh_sach_hien_tai):
        return {"thanh_cong": False, "thong_bao": "Không ghi được cấu hình tab app vào file registry."}

    return {
        "thanh_cong": True,
        "da_cap_nhat_tab_cu": da_ton_tai,
        "tab": tab_moi,
        "tong_so_tab": len(danh_sach_hien_tai),
        "thong_bao": f"Đã {'cập nhật' if da_ton_tai else 'đăng ký'} tab '{tieu_de}' ({len(ds_chuc_nang)} chức năng con).",
    }


def go_dang_ky_tab_app(thu_muc_goc_du_an: Path, ma_app: str) -> dict[str, Any]:
    """Go 1 tab app khoi danh sach tab da dang ky."""
    ma_can_go = _chuan_hoa_ma(ma_app)
    danh_sach_hien_tai = doc_danh_sach_tab_app(thu_muc_goc_du_an)
    danh_sach_moi = [
        tab for tab in danh_sach_hien_tai
        if not (isinstance(tab, dict) and _chuan_hoa_ma(str(tab.get("ma_tab") or "")) == ma_can_go)
    ]
    if len(danh_sach_moi) == len(danh_sach_hien_tai):
        return {"thanh_cong": False, "thong_bao": f"Không tìm thấy tab '{ma_can_go}' để gỡ."}

    if not _ghi_danh_sach_tab_app(thu_muc_goc_du_an, danh_sach_moi):
        return {"thanh_cong": False, "thong_bao": "Lỗi khi ghi lại registry sau khi gỡ tab."}

    return {"thanh_cong": True, "ma_tab": ma_can_go, "thong_bao": f"Đã gỡ tab '{ma_can_go}'."}