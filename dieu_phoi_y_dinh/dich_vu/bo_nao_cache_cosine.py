# ============================================================================
# File Path: dieu_phoi_y_dinh/dich_vu/bo_nao_cache_cosine.py
# Module: Bo Nao Dung Chung (Cosine, Cache Lich Su & Goi Ollama)
# Linked Files: tach_da_y_dinh.py, dieu_phoi_nhanh.py
# Purpose: Tinh do tuong dong cosine, luu/tra cuu cache lich su cau hoi va goi Ollama local.
# ============================================================================

import hashlib
import json
import logging
import math
import os
import re
import time
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)

DIA_CHI_OLLAMA = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
MODEL_SUY_LUAN = os.environ.get("OLLAMA_MODEL", "qwen2.5-coder:7b")
MODEL_NHUNG_VECTOR = os.environ.get("OLLAMA_EMBED_MODEL", "bge-m3")
NGUONG_TUONG_DONG = float(os.environ.get("INTENT_CACHE_THRESHOLD", "0.85"))
THOI_GIAN_SONG_CACHE = int(os.environ.get("INTENT_CACHE_TTL", "86400"))

_BO_NHO_LICH_SU: list[dict] = []


def chuan_hoa_van_ban(van_ban: str) -> str:
    """Chuan hoa khoang trang va chu thuong de so sanh/cache on dinh."""
    return re.sub(r"\s+", " ", (van_ban or "").strip().lower())


def tinh_do_tuong_dong_cosine(vec_a: list[float], vec_b: list[float]) -> float:
    """Tinh do tuong dong cosine giua 2 vector (0.0 -> 1.0)."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    tich_vo_huong = sum(a * b for a, b in zip(vec_a, vec_b))
    do_dai_a = math.sqrt(sum(a * a for a in vec_a))
    do_dai_b = math.sqrt(sum(b * b for b in vec_b))
    if do_dai_a == 0.0 or do_dai_b == 0.0:
        return 0.0
    return max(0.0, min(1.0, tich_vo_huong / (do_dai_a * do_dai_b)))


def _tao_vector_du_phong(van_ban: str) -> list[float]:
    """Vector du phong nhe khi Ollama embedding chua san sang."""
    tu_khoa = re.findall(r"[a-zA-Z0-9_à-ỹ]+", chuan_hoa_van_ban(van_ban))
    chieu = 128
    vector = [0.0] * chieu
    for tu in tu_khoa:
        bam = hashlib.md5(tu.encode("utf-8")).digest()
        chi_so = bam[0] % chieu
        dau = 1.0 if (bam[1] % 2 == 0) else -1.0
        vector[chi_so] += dau
    return vector


def lay_vector_nhung(van_ban: str, timeout: float = 4.0) -> list[float]:
    """Lay vector nhung tu Ollama neu co; fallback sang vector du phong."""
    chuan = chuan_hoa_van_ban(van_ban)
    if not chuan:
        return []

    for duong_dan, khoa_kq in (("/api/embed", "embeddings"), ("/api/embeddings", "embedding")):
        du_lieu = {"model": MODEL_NHUNG_VECTOR, "input" if duong_dan == "/api/embed" else "prompt": chuan}
        try:
            req = urllib.request.Request(
                f"{DIA_CHI_OLLAMA}{duong_dan}",
                data=json.dumps(du_lieu).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                kq = json.loads(resp.read().decode("utf-8", errors="replace"))
                if duong_dan == "/api/embed" and isinstance(kq.get(khoa_kq), list) and kq[khoa_kq]:
                    return [float(x) for x in kq[khoa_kq][0]]
                if duong_dan == "/api/embeddings" and isinstance(kq.get(khoa_kq), list) and kq[khoa_kq]:
                    return [float(x) for x in kq[khoa_kq]]
        except Exception as loi:
            logger.debug("Khong lay duoc vector tu %s, dung du phong: %s", duong_dan, loi)

    return _tao_vector_du_phong(chuan)


def tim_cau_hoi_tuong_tu(prompt: str, nguong: float = NGUONG_TUONG_DONG) -> dict | None:
    """Tim cau hoi tuong tu trong cache lich su bang cosine similarity."""
    chuan = chuan_hoa_van_ban(prompt)
    if not chuan:
        return None

    hien_tai = time.time()
    global _BO_NHO_LICH_SU
    _BO_NHO_LICH_SU = [m for m in _BO_NHO_LICH_SU if (hien_tai - m["thoi_diem"]) <= THOI_GIAN_SONG_CACHE]

    for muc in reversed(_BO_NHO_LICH_SU):
        if muc["van_ban_chuan"] == chuan:
            logger.info("Trung cache chinh xac cho prompt: %s", chuan[:80])
            return {**muc["ket_qua"], "trung_cache": True, "diem_cosine": 1.0, "cau_hoi_khop": muc["prompt"]}

    vec_cau_hoi = lay_vector_nhung(chuan)
    diem_cao_nhat = 0.0
    muc_khop_nhat = None

    for muc in _BO_NHO_LICH_SU:
        diem = tinh_do_tuong_dong_cosine(vec_cau_hoi, muc.get("vector") or [])
        if diem > diem_cao_nhat:
            diem_cao_nhat = diem
            muc_khop_nhat = muc

    if muc_khop_nhat and diem_cao_nhat >= nguong:
        logger.info("Trung cache cosine (%.3f) cho prompt: %s", diem_cao_nhat, chuan[:80])
        return {
            **muc_khop_nhat["ket_qua"],
            "trung_cache": True,
            "diem_cosine": round(diem_cao_nhat, 3),
            "cau_hoi_khop": muc_khop_nhat["prompt"],
        }

    return None


def luu_lich_su_cau_hoi(prompt: str, ket_qua: dict) -> None:
    """Luu ket qua xu ly vao cache lich su."""
    chuan = chuan_hoa_van_ban(prompt)
    if not chuan:
        return
    vec = lay_vector_nhung(chuan)
    ma_khoa = hashlib.sha256(chuan.encode("utf-8")).hexdigest()[:16]

    _BO_NHO_LICH_SU[:] = [m for m in _BO_NHO_LICH_SU if m["ma_khoa"] != ma_khoa]
    _BO_NHO_LICH_SU.append({
        "ma_khoa": ma_khoa,
        "prompt": prompt,
        "van_ban_chuan": chuan,
        "vector": vec,
        "ket_qua": ket_qua,
        "thoi_diem": time.time(),
    })
    if len(_BO_NHO_LICH_SU) > 300:
        _BO_NHO_LICH_SU.pop(0)
    logger.info("Da luu cache lich su [%s] cho prompt: %s", ma_khoa, chuan[:80])


def goi_ollama_phan_tich(noi_dung_prompt: str, timeout: float = 15.0) -> str | None:
    """Goi Ollama local de phan tich ngu canh; tra None neu chua bat hoac loi."""
    try:
        du_lieu = {
            "model": MODEL_SUY_LUAN,
            "prompt": noi_dung_prompt,
            "stream": False,
        }
        req = urllib.request.Request(
            f"{DIA_CHI_OLLAMA}/api/generate",
            data=json.dumps(du_lieu).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            kq = json.loads(resp.read().decode("utf-8", errors="replace"))
            phan_hoi = (kq.get("response") or "").strip()
            return phan_hoi or None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as loi:
        logger.warning("Khong goi duoc Ollama phan tich: %s", loi)
        return None

_LICH_SU_HOI_THOAI: list[dict] = []


def ghi_nhan_luot_hoi_thoai(
    prompt: str,
    ma_linh_vuc: str,
    loai_nhanh: str,
    ket_qua_hien_thi: str = "",
    ten_linh_vuc: str = "",
    trung_cache: bool = False,
) -> None:
    """Luu luot hoi thoai (ca prompt va ket qua hien thi) de ho tro cau hoi noi tiep va tra lich su."""
    sach = (prompt or "").strip()
    if not sach:
        return

    ban_ghi = {
        "prompt": sach,
        "ket_qua_hien_thi": (ket_qua_hien_thi or "").strip(),
        "ma_linh_vuc": ma_linh_vuc or "tong_quat",
        "ten_linh_vuc": ten_linh_vuc or "Đa ngành / Tổng quát",
        "loai_nhanh": loai_nhanh or "",
        "trung_cache": bool(trung_cache),
    }

    _LICH_SU_HOI_THOAI.append(ban_ghi)
    if len(_LICH_SU_HOI_THOAI) > 30:
        _LICH_SU_HOI_THOAI.pop(0)

    try:
        from ..models import LichSuDieuPhoi

        LichSuDieuPhoi.objects.create(
            prompt=ban_ghi["prompt"],
            ket_qua_hien_thi=ban_ghi["ket_qua_hien_thi"],
            y_dinh=ban_ghi["loai_nhanh"],
            ma_linh_vuc=ban_ghi["ma_linh_vuc"],
            ten_linh_vuc=ban_ghi["ten_linh_vuc"],
            trung_cache=ban_ghi["trung_cache"],
        )
    except Exception as loi:
        logger.warning("Khong ghi duoc LichSuDieuPhoi (kiem tra model/migrate): %s", loi)


def lay_ngu_canh_noi_tiep(prompt: str) -> str:
    """Neu prompt la cau hoi noi tiep ngan gon (vd: 'class gi', 'ham gi'), gan ngu canh truoc."""
    sach = (prompt or "").strip()
    thuong = chuan_hoa_van_ban(sach)
    if not _LICH_SU_HOI_THOAI:
        return sach

    la_cau_noi_tiep = bool(
        re.match(
            r"^(class\s*gì|class\s*gi|hàm\s*gì|ham\s*gi|file\s*gì|file\s*gi|app\s*nào|app\s*nao|ở\s*đâu|o\s*dau|những\s*gì|nhung\s*gi)\b",
            thuong,
        )
    )
    if not la_cau_noi_tiep:
        return sach

    luot_gan_nhat = _LICH_SU_HOI_THOAI[-1]
    if re.search(r"(hệ\s*thống|he\s*thong|app|file|dự\s*án|du\s*an|code|class|hàm|ham)", luot_gan_nhat["prompt"].lower()):
        ket_hop = f"hệ thống {sach}"
        logger.info("Noi ngu canh cau hoi tiep: '%s' -> '%s'", sach, ket_hop)
        return ket_hop

    return sach
