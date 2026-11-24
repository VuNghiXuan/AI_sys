# ============================================================================
# File Path: xuong_tao_app/dich_vu/thiet_ke_va_task/tom_tat_va_thiet_ke.py
# Module: Tom Tat Nghiep Vu Va Lap Ban Thiet Ke App
# Linked Files: ../quet_thu_muc/quet_thu_muc_nguon.py, chia_task_nguyen_tu.py
# Purpose: Tong hop noi dung tep da quet va prompt nguoi dung, goi model nhe
#          qwen2.5:3b qua Ollama de tao ban thiet ke app va cac chuc nang con.
# ============================================================================

import json
import logging
import os
import re
from typing import Any
from urllib import error, request

logger = logging.getLogger(__name__)

OLLAMA_URL_MAC_DINH = "http://127.0.0.1:11434/api/generate"
MODEL_THIET_KE_MAC_DINH = "qwen2.5:3b"
TIMEOUT_THIET_KE_GIAY = 90
GIOI_HAN_NGU_CANH_THIET_KE = 18_000


def _goi_ollama_thiet_ke(
    prompt: str,
    model_name: str = MODEL_THIET_KE_MAC_DINH,
    ollama_url: str = OLLAMA_URL_MAC_DINH,
    timeout_giay: int = TIMEOUT_THIET_KE_GIAY,
) -> str:
    """Goi endpoint /api/generate cua Ollama va tra ve chuoi phan hoi."""
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 1200,
        },
    }
    raw_body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        ollama_url,
        data=raw_body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    logger.info("Goi Ollama model='%s' cho buoc lap ban thiet ke", model_name)
    with request.urlopen(req, timeout=timeout_giay) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return str(data.get("response") or "").strip()


def _trich_json_tu_phan_hoi(van_ban: str) -> dict[str, Any] | None:
    """Boc khoi JSON hop le neu model tra kem text mo ta."""
    if not van_ban:
        return None
    try:
        parsed = json.loads(van_ban)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    match = re.search(r"\{[\s\S]*\}", van_ban)
    if not match:
        return None
    try:
        parsed = json.loads(match.group(0))
        return parsed if isinstance(parsed, dict) else None
    except Exception as exc:
        logger.warning("Khong parse duoc JSON tu phan hoi model: %s", exc)
        return None


def _xay_dung_ngu_canh_tep(tep_da_doc: list[dict[str, Any]]) -> str:
    """Gop ten tep va trich doan noi dung ngan gon de tiet kiem context."""
    doan_ngu_canh: list[str] = []
    tong_ky_tu = 0
    for tep in tep_da_doc:
        if tong_ky_tu >= GIOI_HAN_NGU_CANH_THIET_KE:
            break
        ten = tep.get("duong_dan_tuong_doi") or tep.get("ten_tep") or "tep_khong_ten"
        noi_dung = (tep.get("noi_dung") or "").strip()[:2_500]
        khoi = f"--- TEP: {ten} ---\n{noi_dung}"
        if tong_ky_tu + len(khoi) > GIOI_HAN_NGU_CANH_THIET_KE:
            khoi = khoi[: max(0, GIOI_HAN_NGU_CANH_THIET_KE - tong_ky_tu)]
        doan_ngu_canh.append(khoi)
        tong_ky_tu += len(khoi)
    return "\n\n".join(doan_ngu_canh)


def _thiet_ke_du_phong(prompt_goc: str, tep_da_doc: list[dict[str, Any]], ly_do: str) -> dict[str, Any]:
    """Sinh ban thiet ke co ban tu ten tep va prompt khi chua goi duoc Ollama."""
    ds_ten_tep = [str(t.get("ten_tep") or "") for t in tep_da_doc if t.get("ten_tep")]
    logger.warning("Dung ban thiet ke du phong (ly_do=%s, so_tep=%d)", ly_do, len(ds_ten_tep))
    return {
        "hop_le": True,
        "che_do": "du_phong",
        "ly_do_du_phong": ly_do,
        "ten_app_goi_y": "app_nghiep_vu_moi",
        "tieu_de_tab": "App Nghiệp Vụ Mới",
        "tom_tat_nghiep_vu": (
            f"Yêu cầu chính: {prompt_goc or 'Chưa nhập mô tả cụ thể'}. "
            f"Đã đọc {len(ds_ten_tep)} tệp nguồn ({', '.join(ds_ten_tep[:6])})."
        ),
        "chuc_nang_con": [
            {"ma": "tong_quan_du_lieu", "ten": "Tổng quan & tra cứu", "mo_ta": "Xem và lọc dữ liệu nghiệp vụ từ nguồn."},
            {"ma": "nhap_cap_nhat", "ten": "Nhập & cập nhật", "mo_ta": "Thêm mới hoặc chỉnh sửa bản ghi nghiệp vụ."},
            {"ma": "kiem_tra_tong_hop", "ten": "Kiểm tra & tổng hợp", "mo_ta": "Tổng hợp số liệu và kiểm tra tính hợp lệ."},
        ],
        "luu_y_ky_thuat": [
            "Mỗi file code dưới 300 dòng, có header file, docstring và logger.",
            "Test giao diện ở môi trường riêng trước khi gắn vào 1 tab hệ thống.",
        ],
    }


def lap_ban_thiet_ke_app(
    prompt_goc: str,
    tep_da_doc: list[dict[str, Any]],
    model_name: str | None = None,
) -> dict[str, Any]:
    """Lap ban thiet ke app va danh sach chuc nang con tu prompt + tep da doc."""
    model_su_dung = (model_name or os.environ.get("XUONG_TAO_APP_MODEL_THIET_KE") or MODEL_THIET_KE_MAC_DINH).strip()
    ollama_url = (os.environ.get("OLLAMA_API_URL") or OLLAMA_URL_MAC_DINH).strip()
    ngu_canh_tep = _xay_dung_ngu_canh_tep(tep_da_doc)

    prompt_thiet_ke = (
        "Bạn là kiến trúc sư phần mềm. Hãy phân tích yêu cầu và tài liệu sau để thiết kế 1 app chạy trên 1 tab "
        "với các chức năng con rõ ràng. Chỉ trả về JSON hợp lệ (không markdown bao ngoài) theo cấu trúc:\n"
        '{"ten_app_goi_y":"snake_case","tieu_de_tab":"...","tom_tat_nghiep_vu":"...",'
        '"chuc_nang_con":[{"ma":"...","ten":"...","mo_ta":"..."}],"luu_y_ky_thuat":["..."]}\n\n'
        f"PROMPT YÊU CẦU:\n{(prompt_goc or '').strip()}\n\n"
        f"NỘI DUNG TÀI LIỆU NGUỒN:\n{ngu_canh_tep or '(Không có tệp nội dung)'}"
    )

    try:
        phan_hoi = _goi_ollama_thiet_ke(prompt_thiet_ke, model_name=model_su_dung, ollama_url=ollama_url)
        du_lieu = _trich_json_tu_phan_hoi(phan_hoi)
        if not du_lieu:
            return _thiet_ke_du_phong(prompt_goc, tep_da_doc, "phan_hoi_khong_phai_json")

        chuc_nang = du_lieu.get("chuc_nang_con")
        if not isinstance(chuc_nang, list) or not chuc_nang:
            return _thiet_ke_du_phong(prompt_goc, tep_da_doc, "thieu_chuc_nang_con")

        logger.info("Lap ban thiet ke thanh cong qua model '%s' (%d chuc nang con)", model_su_dung, len(chuc_nang))
        return {
            "hop_le": True,
            "che_do": "ollama",
            "model_su_dung": model_su_dung,
            "ten_app_goi_y": str(du_lieu.get("ten_app_goi_y") or "app_nghiep_vu_moi").strip(),
            "tieu_de_tab": str(du_lieu.get("tieu_de_tab") or "App Nghiệp Vụ").strip(),
            "tom_tat_nghiep_vu": str(du_lieu.get("tom_tat_nghiep_vu") or "").strip(),
            "chuc_nang_con": chuc_nang,
            "luu_y_ky_thuat": du_lieu.get("luu_y_ky_thuat") if isinstance(du_lieu.get("luu_y_ky_thuat"), list) else [],
        }
    except (error.URLError, TimeoutError, OSError) as exc:
        logger.error("Loi ket noi/timeout Ollama khi lap thiet ke: %s", exc, exc_info=True)
        return _thiet_ke_du_phong(prompt_goc, tep_da_doc, f"loi_ollama:{exc}")