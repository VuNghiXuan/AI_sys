# ============================================================================
# File Path: xuong_tao_app/dich_vu/tu_sua_va_nang_cap/vong_lap_tu_sua.py
# Module: Vong Lap Tu Sua / Nang Cap Co Circuit Breaker
# Linked Files: khoanh_vung_va_sao_luu.py,
#               ../sinh_ma_sandbox/kiem_tra_ma_sinh.py
# Purpose: Thuc thi sua loi hoac nang cap cac tep duoc khoanh vung dua tren
#          prompt phan hoi + mo ta anh/log, gioi han vong lap bang Circuit Breaker.
# ============================================================================

import json
import logging
import os
from pathlib import Path
from typing import Any
from urllib import error, request

from xuong_tao_app.dich_vu.sinh_ma_sandbox.kiem_tra_ma_sinh import (
    boc_ma_nguon_sach,
    dam_bao_header_va_logger_python,
    kiem_tra_ma_python,
)
from xuong_tao_app.dich_vu.tu_sua_va_nang_cap.khoanh_vung_va_sao_luu import (
    khoanh_vung_tep_lien_quan,
    phan_loai_y_do_phan_hoi,
    sao_luu_cac_tep,
)

logger = logging.getLogger(__name__)

OLLAMA_URL_MAC_DINH = "http://127.0.0.1:11434/api/generate"
MODEL_SUA_CODE_MAC_DINH = "qwen2.5-coder:7b"
GIOI_HAN_VONG_LAP_CIRCUIT_BREAKER = 3
TIMEOUT_SUA_CODE_GIAY = 150


def _goi_ollama_sua_tep(
    prompt: str,
    model_name: str = MODEL_SUA_CODE_MAC_DINH,
    ollama_url: str = OLLAMA_URL_MAC_DINH,
    timeout_giay: int = TIMEOUT_SUA_CODE_GIAY,
) -> str:
    """Goi Ollama de cap nhat mot tep theo phan hoi test giao dien."""
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.15,
            "num_predict": 2200,
        },
    }
    raw_body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        ollama_url,
        data=raw_body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with request.urlopen(req, timeout=timeout_giay) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return str(data.get("response") or "").strip()


def _tao_prompt_sua_tep(
    tep: Path,
    noi_dung_hien_tai: str,
    y_do: str,
    prompt_phan_hoi: str,
    mo_ta_anh: str,
    log_loi: str,
) -> str:
    """Tao prompt sua/nang cap giu nguyen cac ham/phan khong bi yeu cau doi."""
    return (
        f"Bạn đang thực hiện '{y_do}' cho file `{tep.name}` trên môi trường test riêng.\n"
        "QUY TẮC BẮT BUỘC:\n"
        "- Giữ nguyên các hàm, chức năng và phần giao diện không bị yêu cầu sửa/nâng cấp.\n"
        "- Tổng số dòng tối đa 260 dòng (tuyệt đối dưới 300 dòng).\n"
        "- Nếu là .py: giữ header file, docstring và logging.getLogger(__name__), KHÔNG dùng print().\n"
        "- Chỉ trả về toàn bộ nội dung file đã cập nhật trong 1 khối code ```...```.\n\n"
        f"PHẢN HỒI CỦA NGƯỜI DÙNG KHI TEST: {(prompt_phan_hoi or '').strip()}\n"
        f"MÔ TẢ ẢNH CHỤP MÀN HÌNH / VÙNG LỖI: {(mo_ta_anh or '(Không có mô tả ảnh)').strip()}\n"
        f"LOG / LỖI GẦN NHẤT: {(log_loi or '(Không có log lỗi)').strip()}\n\n"
        f"NỘI DUNG HIỆN TẠI CỦA `{tep.name}`:\n{noi_dung_hien_tai[:9000]}"
    )


def sua_hoac_nang_cap_tu_phan_hoi(
    thu_muc_goc_du_an: Path,
    ma_app: str,
    prompt_phan_hoi: str,
    mo_ta_anh: str = "",
    log_loi: str = "",
    ma_chuc_nang_con: str = "",
    so_lan_da_thu: int = 0,
    gioi_han_vong_lap: int = GIOI_HAN_VONG_LAP_CIRCUIT_BREAKER,
    model_name: str | None = None,
) -> dict[str, Any]:
    """Chay sua/nang cap theo phan hoi test thuc te voi Circuit Breaker."""
    if so_lan_da_thu >= gioi_han_vong_lap:
        logger.warning(
            "Circuit Breaker kich hoat cho app '%s' sau %d/%d lan thu",
            ma_app,
            so_lan_da_thu,
            gioi_han_vong_lap,
        )
        return {
            "thanh_cong": False,
            "circuit_breaker_kich_hoat": True,
            "trang_thai": "ngat_mach_gioi_han_vong_lap",
            "so_lan_da_thu": so_lan_da_thu,
            "gioi_han_vong_lap": gioi_han_vong_lap,
            "thong_bao": (
                f"Đã đạt giới hạn {gioi_han_vong_lap} vòng tự sửa cho app '{ma_app}'. "
                "Hệ thống dừng tự sửa để tránh lặp lỗi; anh có thể xem log hoặc bấm hoàn tác bản sao lưu."
            ),
        }

    y_do = phan_loai_y_do_phan_hoi(prompt_phan_hoi, mo_ta_anh)
    cac_tep = khoanh_vung_tep_lien_quan(
        thu_muc_goc_du_an=thu_muc_goc_du_an,
        ma_app=ma_app,
        prompt_phan_hoi=prompt_phan_hoi,
        mo_ta_anh=mo_ta_anh,
        ma_chuc_nang_con=ma_chuc_nang_con,
    )
    if not cac_tep:
        return {
            "thanh_cong": False,
            "circuit_breaker_kich_hoat": False,
            "trang_thai": "khong_co_tep_muc_tieu",
            "thong_bao": f"Không tìm thấy tệp nào trong khu vực test riêng của app '{ma_app}'.",
        }

    ma_snapshot = sao_luu_cac_tep(thu_muc_goc_du_an, ma_app, cac_tep)
    model_su_dung = (model_name or os.environ.get("XUONG_TAO_APP_MODEL_CODE") or MODEL_SUA_CODE_MAC_DINH).strip()
    ollama_url = (os.environ.get("OLLAMA_API_URL") or OLLAMA_URL_MAC_DINH).strip()

    ket_qua_tep: list[dict[str, Any]] = []
    so_tep_dat = 0

    for tep in cac_tep:
        noi_dung_cu = tep.read_text(encoding="utf-8", errors="replace")
        prompt_sua = _tao_prompt_sua_tep(tep, noi_dung_cu, y_do, prompt_phan_hoi, mo_ta_anh, log_loi)
        try:
            phan_hoi_raw = _goi_ollama_sua_tep(prompt_sua, model_name=model_su_dung, ollama_url=ollama_url)
            ma_moi = boc_ma_nguon_sach(phan_hoi_raw)
            if not ma_moi.strip():
                ket_qua_tep.append({"tep": tep.name, "thanh_cong": False, "thong_bao": "Model trả mã rỗng."})
                continue

            if tep.suffix.lower() == ".py":
                ma_moi = dam_bao_header_va_logger_python(ma_moi, str(tep.name), f"{y_do} theo phan hoi test")
                hop_le, ly_do = kiem_tra_ma_python(ma_moi)
                if not hop_le:
                    ket_qua_tep.append({"tep": tep.name, "thanh_cong": False, "thong_bao": ly_do})
                    continue
            else:
                so_dong = len(ma_moi.splitlines())
                if so_dong > 300:
                    ket_qua_tep.append({"tep": tep.name, "thanh_cong": False, "thong_bao": f"Vượt 300 dòng ({so_dong})."})
                    continue
                ly_do = f"Hợp lệ ({so_dong} dòng)."

            tep.write_text(ma_moi, encoding="utf-8")
            so_tep_dat += 1
            ket_qua_tep.append({"tep": tep.name, "thanh_cong": True, "thong_bao": ly_do})
        except (error.URLError, TimeoutError, OSError) as exc:
            logger.error("Loi Ollama khi sua tep '%s': %s", tep.name, exc, exc_info=True)
            ket_qua_tep.append({"tep": tep.name, "thanh_cong": False, "thong_bao": str(exc)})

    lan_thu_moi = so_lan_da_thu + 1
    dat_tat_ca = so_tep_dat == len(cac_tep)
    ngat_mach_sau_lan_nay = (not dat_tat_ca) and (lan_thu_moi >= gioi_han_vong_lap)

    logger.info(
        "Ket thuc lan sua #%d cho app '%s' (y_do=%s): dat=%d/%d tep, snapshot=%s",
        lan_thu_moi,
        ma_app,
        y_do,
        so_tep_dat,
        len(cac_tep),
        ma_snapshot,
    )
    return {
        "thanh_cong": dat_tat_ca,
        "y_do": y_do,
        "ma_snapshot": ma_snapshot,
        "so_lan_da_thu": lan_thu_moi,
        "gioi_han_vong_lap": gioi_han_vong_lap,
        "circuit_breaker_kich_hoat": ngat_mach_sau_lan_nay,
        "so_tep_cap_nhat": so_tep_dat,
        "ket_qua_tep": ket_qua_tep,
    }