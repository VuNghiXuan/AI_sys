# ============================================================================
# File Path: xuong_tao_app/dich_vu/sinh_ma_sandbox/thuc_thi_sinh_sandbox.py
# Module: Dieu Phoi Sinh Ma Cho Tung Task Trong Moi Truong Test Rieng
# Linked Files: kiem_tra_ma_sinh.py, ../thiet_ke_va_task/chia_task_nguyen_tu.py
# Purpose: Goi model code (qwen2.5-coder:7b) cho tung task nguyen tu, kiem tra
#          va ghi file vao khu vuc test tach biet de nguoi dung test giao dien.
# ============================================================================

import json
import logging
import os
from pathlib import Path
from typing import Any
from urllib import error, request

from xuong_tao_app.dich_vu.sinh_ma_sandbox.kiem_tra_ma_sinh import (
    kiem_tra_va_ghi_tep_sandbox,
)

logger = logging.getLogger(__name__)

OLLAMA_URL_MAC_DINH = "http://127.0.0.1:11434/api/generate"
MODEL_CODE_MAC_DINH = "qwen2.5-coder:7b"
TIMEOUT_SINH_CODE_GIAY = 150


def _goi_ollama_sinh_code(
    prompt: str,
    model_name: str = MODEL_CODE_MAC_DINH,
    ollama_url: str = OLLAMA_URL_MAC_DINH,
    timeout_giay: int = TIMEOUT_SINH_CODE_GIAY,
) -> str:
    """Goi Ollama sinh ma nguon cho mot task cu the."""
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
    logger.info("Goi Ollama model='%s' sinh code sandbox", model_name)
    with request.urlopen(req, timeout=timeout_giay) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return str(data.get("response") or "").strip()


def _tao_prompt_cho_task(
    task: dict[str, Any],
    ban_thiet_ke: dict[str, Any],
    tom_tat_nguon: str,
) -> str:
    """Tao prompt chi tiet, bam quy chuan duoi 300 dong va co log cho tung task."""
    file_muc_tieu = str(task.get("file_muc_tieu") or "")
    tieu_de = str(task.get("tieu_de") or "")
    mo_ta = str(task.get("mo_ta") or "")
    chuc_nang_con = json.dumps(ban_thiet_ke.get("chuc_nang_con") or [], ensure_ascii=False)

    return (
        "Bạn là lập trình viên Python/Web. Hãy viết mã nguồn hoàn chỉnh, sạch, dễ chạy cho đúng 1 file mục tiêu.\n"
        "QUY TẮC BẮT BUỘC:\n"
        "- Tổng số dòng tối đa 260 dòng (tuyệt đối dưới 300 dòng).\n"
        "- Nếu là file .py: có header file ở đầu, có docstring cho hàm, dùng logging.getLogger(__name__), KHÔNG dùng print().\n"
        "- Chỉ trả về mã nguồn của file này (ưu tiên đặt trong 1 khối code ```...```), không giải thích dài dòng.\n\n"
        f"FILE MỤC TIÊU: {file_muc_tieu}\n"
        f"NHIỆM VỤ TASK: {tieu_de}\n"
        f"MÔ TẢ CHI TIẾT: {mo_ta or tieu_de}\n"
        f"TÓM TẮT NGHIỆP VỤ: {ban_thiet_ke.get('tom_tat_nghiep_vu', '')}\n"
        f"DANH SÁCH CHỨC NĂNG CON: {chuc_nang_con}\n"
        f"NGỮ CẢNH TÀI LIỆU NGUỒN (RÚT GỌN): {tom_tat_nguon[:4000]}"
    )


def sinh_ma_cho_danh_sach_task(
    danh_sach_task: list[dict[str, Any]],
    ban_thiet_ke: dict[str, Any],
    thu_muc_goc_du_an: Path,
    tom_tat_nguon: str = "",
    model_name: str | None = None,
) -> dict[str, Any]:
    """Chay sinh code lan luot cho tung task vao thu muc moi truong test rieng."""
    model_su_dung = (model_name or os.environ.get("XUONG_TAO_APP_MODEL_CODE") or MODEL_CODE_MAC_DINH).strip()
    ollama_url = (os.environ.get("OLLAMA_API_URL") or OLLAMA_URL_MAC_DINH).strip()

    ket_qua_task: list[dict[str, Any]] = []
    so_task_thanh_cong = 0

    for task in danh_sach_task:
        ma_task = str(task.get("ma_task") or "TASK")
        file_muc_tieu = str(task.get("file_muc_tieu") or "")
        tieu_de = str(task.get("tieu_de") or "")
        logger.info("Bat dau thuc thi %s -> %s", ma_task, file_muc_tieu)

        prompt_task = _tao_prompt_cho_task(task, ban_thiet_ke, tom_tat_nguon)
        try:
            phan_hoi = _goi_ollama_sinh_code(prompt_task, model_name=model_su_dung, ollama_url=ollama_url)
            ket_qua_ghi = kiem_tra_va_ghi_tep_sandbox(
                thu_muc_goc_du_an=thu_muc_goc_du_an,
                file_muc_tieu=file_muc_tieu,
                phan_hoi_raw=phan_hoi,
                mo_ta_task=tieu_de,
            )
            dat = bool(ket_qua_ghi.get("thanh_cong"))
            if dat:
                so_task_thanh_cong += 1
            ket_qua_task.append({
                "ma_task": ma_task,
                "file_muc_tieu": file_muc_tieu,
                "thanh_cong": dat,
                **ket_qua_ghi,
            })
        except (error.URLError, TimeoutError, OSError) as exc:
            logger.error("Loi goi Ollama o %s (%s): %s", ma_task, file_muc_tieu, exc, exc_info=True)
            ket_qua_task.append({
                "ma_task": ma_task,
                "file_muc_tieu": file_muc_tieu,
                "thanh_cong": False,
                "trang_thai": "loi_ollama",
                "thong_bao": str(exc),
            })

    logger.info(
        "Hoan tat sinh ma sandbox: thanh_cong=%d/%d task",
        so_task_thanh_cong,
        len(danh_sach_task),
    )
    return {
        "tong_so_task": len(danh_sach_task),
        "so_task_thanh_cong": so_task_thanh_cong,
        "model_su_dung": model_su_dung,
        "ket_qua_task": ket_qua_task,
    }