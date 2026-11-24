# ============================================================================
# File Path: dieu_phoi_y_dinh/dich_vu/dinh_tuyen/bo_dinh_tuyen_ngu_nghia.py
# Module: Bo Dinh Tuyen Ngu Nghia Bang Vector Embedding & Trong Tai LLM
# Linked Files: dieu_phoi_y_dinh/dich_vu/dinh_tuyen/bo_dang_ky_y_dinh.py,
#               dieu_phoi_y_dinh/cau_hinh/cau_hinh_y_dinh.json
# Purpose: Tinh vector embedding qua Ollama, do tuong dong cosine voi cau mau
#          va goi model trong tai khi diem trung gian hoac embedding thieu/thap.
# ============================================================================

from dataclasses import dataclass
import json
import logging
import math
import os
from pathlib import Path
import threading
from typing import Any
from urllib import request as url_request

logger = logging.getLogger(__name__)

_LOCK_VEC = threading.Lock()
_CACHE_VEC: dict[str, list[tuple[str, list[float]]]] = {}
OLLAMA_BASE_URL = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
MODEL_EMBED_MAC_DINH = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text")
MODEL_TRONG_TAI_MAC_DINH = os.environ.get("OLLAMA_ROUTER_MODEL", "qwen2.5:3b")


@dataclass(frozen=True)
class KetQuaDinhTuyen:
    """Ket qua dinh tuyen y dinh."""

    ma_y_dinh: str
    diem_cosine: float
    nguon: str


def _cosine(a: list[float], b: list[float]) -> float:
    """Tinh do tuong dong cosine giua 2 vector."""
    if not a or not b or len(a) != len(b):
        return 0.0
    tich_vo_huong = sum(x * y for x, y in zip(a, b))
    do_dai_a = math.sqrt(sum(x * x for x in a))
    do_dai_b = math.sqrt(sum(y * y for y in b))
    if do_dai_a == 0.0 or do_dai_b == 0.0:
        return 0.0
    return tich_vo_huong / (do_dai_a * do_dai_b)


def _lay_vector_ollama(van_ban: str, model_embed: str = MODEL_EMBED_MAC_DINH) -> list[float]:
    """Lay vector embedding tu Ollama (ho tro ca /api/embed va /api/embeddings)."""
    for endpoint, body in (
        ("/api/embed", {"model": model_embed, "input": van_ban}),
        ("/api/embeddings", {"model": model_embed, "prompt": van_ban}),
    ):
        req = url_request.Request(
            f"{OLLAMA_BASE_URL}{endpoint}",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with url_request.urlopen(req, timeout=5.0) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
            if "embeddings" in raw and raw["embeddings"]:
                return [float(x) for x in raw["embeddings"][0]]
            if "embedding" in raw and raw["embedding"]:
                return [float(x) for x in raw["embedding"]]
        except Exception as loi:
            logger.debug("Loi goi embedding endpoint=%s model=%s: %s", endpoint, model_embed, loi)
            continue
    return []


def _lay_vector_mau(
    duong_dan_json: Path,
    ds_y_dinh: list[dict[str, Any]],
    model_embed: str = MODEL_EMBED_MAC_DINH,
) -> list[tuple[str, list[float]]]:
    """Tinh va cache vector cho cac cau_mau_ngu_nghia."""
    mtime = str(duong_dan_json.stat().st_mtime_ns) if duong_dan_json.exists() else "0"
    khoa = f"{duong_dan_json}::{model_embed}::{mtime}"

    with _LOCK_VEC:
        if khoa in _CACHE_VEC:
            return list(_CACHE_VEC[khoa])

    ket_qua: list[tuple[str, list[float]]] = []
    for muc in ds_y_dinh:
        ma_yd = str(muc.get("ma_y_dinh") or "").strip()
        if not ma_yd:
            continue
        for cau in muc.get("cau_mau_ngu_nghia") or []:
            cau_sach = str(cau or "").strip()
            if cau_sach:
                vec = _lay_vector_ollama(cau_sach, model_embed=model_embed)
                if vec:
                    ket_qua.append((ma_yd, vec))

    if ket_qua:
        with _LOCK_VEC:
            logger.info("Cap nhat cache vector mau (%d mau) cho %s", len(ket_qua), khoa)
            _CACHE_VEC.clear()
            _CACHE_VEC[khoa] = list(ket_qua)
    return ket_qua


def _trong_tai_qwen(
    prompt: str,
    ds_y_dinh: list[dict[str, Any]],
    du_phong: str,
    model_trong_tai: str = MODEL_TRONG_TAI_MAC_DINH,
) -> str:
    """Goi model trong tai chon dung 1 ma_y_dinh hop le kem mo ta ngan."""
    ds_ma = [str(m.get("ma_y_dinh") or "").strip() for m in ds_y_dinh if m.get("ma_y_dinh")]
    if not ds_ma:
        return du_phong

    dong_mo_ta = [
        f"- {str(m.get('ma_y_dinh') or '').strip()}: {str(m.get('mo_ta_ngu_nghia') or '').strip()[:90]}"
        for m in ds_y_dinh
        if str(m.get("ma_y_dinh") or "").strip()
    ]
    noi_dung = (
        "Cac y dinh hop le:\n"
        + "\n".join(dong_mo_ta)
        + f"\nCau hoi: \"{prompt}\"\n"
        "Chon 1 ma phu hop nhat. Chi tra JSON: {\"ma_y_dinh\": \"...\"}"
    )
    payload = json.dumps({
        "model": model_trong_tai,
        "prompt": noi_dung,
        "stream": False,
        "options": {"temperature": 0.0, "num_predict": 64},
    }).encode("utf-8")

    req = url_request.Request(
        f"{OLLAMA_BASE_URL}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with url_request.urlopen(req, timeout=10.0) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
        text = str(raw.get("response") or "")
        dau, cuoi = text.find("{"), text.rfind("}")
        if dau != -1 and cuoi > dau:
            ma_chon = str(json.loads(text[dau : cuoi + 1]).get("ma_y_dinh") or "").strip()
            if ma_chon in ds_ma:
                return ma_chon
    except Exception as loi:
        logger.warning("Trong tai %s loi/timeout: %s", model_trong_tai, loi)
    return du_phong if du_phong in ds_ma else ds_ma[0]


def dinh_tuyen_ngu_nghia(
    prompt: str,
    duong_dan_json: Path,
    cau_hinh_json: dict[str, Any],
) -> KetQuaDinhTuyen | None:
    """Dinh tuyen qua embedding; diem lung chung hoac thieu vector se nho trong tai."""
    prompt_sach = (prompt or "").strip()
    if not prompt_sach:
        return None

    ds_y_dinh = [m for m in (cau_hinh_json.get("y_dinh") or []) if isinstance(m, dict)]
    nguong_chot = float(cau_hinh_json.get("nguong_cosine_chot") or 0.72)
    nguong_llm = float(cau_hinh_json.get("nguong_cosine_hoi_llm") or 0.42)
    ma_thap = str(cau_hinh_json.get("y_dinh_mac_dinh_thap") or "chat_tu_do")
    model_embed = str(cau_hinh_json.get("model_embed") or MODEL_EMBED_MAC_DINH)
    model_trong_tai = str(cau_hinh_json.get("model_trong_tai") or MODEL_TRONG_TAI_MAC_DINH)

    vec_prompt = _lay_vector_ollama(prompt_sach, model_embed=model_embed)
    ds_mau = _lay_vector_mau(duong_dan_json, ds_y_dinh, model_embed=model_embed)

    ma_tot_nhat = ""
    diem_tot_nhat = -1.0
    if vec_prompt and ds_mau:
        for ma_yd, vec_mau in ds_mau:
            diem = _cosine(vec_prompt, vec_mau)
            if diem > diem_tot_nhat:
                diem_tot_nhat = diem
                ma_tot_nhat = ma_yd

    if ma_tot_nhat and diem_tot_nhat >= nguong_chot:
        logger.debug("Cosine chot '%s' (%.4f >= %.2f)", ma_tot_nhat, diem_tot_nhat, nguong_chot)
        return KetQuaDinhTuyen(ma_tot_nhat, diem_tot_nhat, "embedding")

    if diem_tot_nhat >= nguong_llm or not ds_mau:
        ma_llm = _trong_tai_qwen(
            prompt_sach,
            ds_y_dinh,
            ma_tot_nhat or ma_thap,
            model_trong_tai=model_trong_tai,
        )
        logger.debug("Trong tai chon '%s' (cosine=%.4f)", ma_llm, diem_tot_nhat)
        return KetQuaDinhTuyen(ma_llm, max(0.0, diem_tot_nhat), "qwen_trong_tai")

    return KetQuaDinhTuyen(ma_thap, max(0.0, diem_tot_nhat), "mac_dinh_thap")