# ============================================================================
# File Path: dieu_phoi_y_dinh/dich_vu/thuc_thi_nhanh/tra_cuu_mang.py
# Module: Dich Vu Tra Cuu Mang Truc Tiep Va Fallback Khi Loi
# Linked Files: dieu_phoi_y_dinh/dich_vu/thuc_thi_nhanh/trinh_xu_ly_chung.py,
#               dieu_phoi_y_dinh/dich_vu/thuc_thi_nhanh/ho_tro_llm_he_thong.py
# Purpose: Tra cuu web truc tiep cho moi may cai dat, uu tien AI_SYS_SEARCH_URL
#          neu co, boc tach HTML linh hoat, cache TTL va fallback khi loi.
# ============================================================================

from html import unescape
import json
import logging
import os
import re
import threading
import time
from typing import Any
from urllib import parse as url_parse
from urllib import request as url_request

from .ho_tro_llm_he_thong import (
    TIMEOUT_LLM_CHAT_GIAY,
    dinh_dang_link_tham_khao,
    goi_llm_huong_dan,
)

logger = logging.getLogger(__name__)

MAC_DINH_BAT_TRA_CUU_MANG = "1"
GIA_TRI_BAT = {"1", "true", "yes", "on"}
URL_TIM_KIEM_MAC_DINH = "https://html.duckduckgo.com/html/"
MAX_KET_QUA_MANG = 5
USER_AGENT_TRINH_DUYET = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

_LOCK_CACHE_MANG = threading.Lock()
_CACHE_MANG: dict[str, tuple[float, list[dict[str, str]]]] = {}

_MAU_THE_A_DDG = re.compile(r"<a\b([^>]*)>(.*?)</a>", flags=re.IGNORECASE | re.DOTALL)
_MAU_CLASS_ATTR = re.compile(r"""class\s*=\s*["']([^"']*)["']""", flags=re.IGNORECASE)
_MAU_HREF_ATTR = re.compile(r"""href\s*=\s*["']([^"']*)["']""", flags=re.IGNORECASE)
_MAU_SNIPPET_DDG = re.compile(
    r"""<(?:a|div|span)\b[^>]*class\s*=\s*["'][^"']*result__snippet[^"']*["'][^>]*>(.*?)</(?:a|div|span)>""",
    flags=re.IGNORECASE | re.DOTALL,
)
_MAU_XOA_TAG = re.compile(r"<[^>]+>")


def _doc_cau_hinh_mang() -> dict[str, Any]:
    """Doc cau hinh tra cuu mang dong theo moi truong hien tai."""
    co_bat = os.environ.get("AI_SYS_ENABLE_WEB_SEARCH", MAC_DINH_BAT_TRA_CUU_MANG).strip().lower()
    endpoint = os.environ.get("AI_SYS_SEARCH_URL", "").strip()
    timeout_giay = float(os.environ.get("AI_SYS_SEARCH_TIMEOUT_GIAY", "6.0"))
    ttl_giay = int(os.environ.get("AI_SYS_SEARCH_CACHE_TTL", "300"))
    num_predict = int(os.environ.get("OLLAMA_NUM_PREDICT_WEB", "224"))
    return {
        "bat": co_bat in GIA_TRI_BAT,
        "endpoint": endpoint,
        "timeout": max(1.5, timeout_giay),
        "ttl": max(10, ttl_giay),
        "num_predict": max(64, num_predict),
    }


def _lam_sach_van_ban_html(chuoi_html: str) -> str:
    """Xoa tag HTML va chuan hoa khoang trang."""
    sach = _MAU_XOA_TAG.sub(" ", unescape(chuoi_html or ""))
    return re.sub(r"\s+", " ", sach).strip()


def _giai_ma_url_tim_kiem(url_tho: str) -> str:
    """Chuan hoa link chuyen huong (neu co) ve URL dich http/https."""
    sach = unescape((url_tho or "").strip())
    if sach.startswith("//"):
        sach = f"https:{sach}"
    parsed = url_parse.urlparse(sach)
    if "duckduckgo.com" in parsed.netloc and parsed.path.startswith("/l/"):
        qs = url_parse.parse_qs(parsed.query)
        dich = (qs.get("uddg") or [""])[0].strip()
        if dich:
            return url_parse.unquote(dich)
    return sach


def _la_url_hop_le(url: str) -> bool:
    """Kiem tra URL bat dau bang http:// hoac https:// va co host."""
    sach = (url or "").strip()
    if not sach.startswith(("http://", "https://")):
        return False
    parsed = url_parse.urlparse(sach)
    return bool(parsed.netloc)


def _chuan_hoa_ket_qua_json(ds_raw: list[Any]) -> list[dict[str, str]]:
    """Chuan hoa ket qua JSON tu endpoint tuy chinh ve tieu_de, url, tom_tat."""
    ket_qua: list[dict[str, str]] = []
    for muc in ds_raw or []:
        if not isinstance(muc, dict):
            continue
        url = _giai_ma_url_tim_kiem(str(muc.get("url") or muc.get("link") or ""))
        if not _la_url_hop_le(url):
            continue
        tieu_de = _lam_sach_van_ban_html(str(muc.get("title") or muc.get("tieu_de") or url)) or url
        tom_tat = _lam_sach_van_ban_html(
            str(muc.get("content") or muc.get("snippet") or muc.get("tom_tat") or "")
        )
        ket_qua.append({"tieu_de": tieu_de, "url": url, "tom_tat": tom_tat})
        if len(ket_qua) >= MAX_KET_QUA_MANG:
            break
    return ket_qua


def _goi_endpoint_json(cau_hoi: str, endpoint: str, timeout_giay: float) -> list[dict[str, str]]:
    """Truy van endpoint JSON (vd SearXNG / proxy tim kiem)."""
    sep = "&" if "?" in endpoint else "?"
    url_goi = f"{endpoint}{sep}q={url_parse.quote(cau_hoi)}&format=json"
    req = url_request.Request(
        url_goi,
        headers={"Accept": "application/json", "User-Agent": "AI_Sys/1.0"},
        method="GET",
    )
    with url_request.urlopen(req, timeout=timeout_giay) as resp:
        raw = json.loads(resp.read().decode("utf-8"))
    ds_goc = raw.get("results") if isinstance(raw, dict) else raw
    return _chuan_hoa_ket_qua_json(ds_goc if isinstance(ds_goc, list) else [])


def _goi_tim_kiem_mac_dinh(cau_hoi: str, timeout_giay: float) -> list[dict[str, str]]:
    """Tra cuu web truc tiep khi chua khai bao AI_SYS_SEARCH_URL."""
    url_goi = f"{URL_TIM_KIEM_MAC_DINH}?q={url_parse.quote(cau_hoi)}"
    req = url_request.Request(
        url_goi,
        headers={
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
            "User-Agent": USER_AGENT_TRINH_DUYET,
        },
        method="GET",
    )
    with url_request.urlopen(req, timeout=timeout_giay) as resp:
        html_text = resp.read().decode("utf-8", errors="replace")

    cac_link: list[tuple[str, str]] = []
    for thuoc_tinh, noi_dung_the in _MAU_THE_A_DDG.findall(html_text):
        m_cls = _MAU_CLASS_ATTR.search(thuoc_tinh)
        m_href = _MAU_HREF_ATTR.search(thuoc_tinh)
        if not m_cls or not m_href:
            continue
        if "result__a" not in m_cls.group(1).split():
            continue
        cac_link.append((m_href.group(1), noi_dung_the))

    cac_tom_tat = _MAU_SNIPPET_DDG.findall(html_text)
    logger.info("Boc tach HTML: %d link result__a, %d snippet", len(cac_link), len(cac_tom_tat))

    ket_qua: list[dict[str, str]] = []
    for idx, (href_tho, tieu_de_tho) in enumerate(cac_link):
        url = _giai_ma_url_tim_kiem(href_tho)
        if not _la_url_hop_le(url):
            continue
        tieu_de = _lam_sach_van_ban_html(tieu_de_tho) or url
        tom_tat = _lam_sach_van_ban_html(cac_tom_tat[idx]) if idx < len(cac_tom_tat) else ""
        ket_qua.append({"tieu_de": tieu_de, "url": url, "tom_tat": tom_tat})
        if len(ket_qua) >= MAX_KET_QUA_MANG:
            break
    return ket_qua


def _lay_ket_qua_tim_kiem(cau_hoi: str, cau_hinh: dict[str, Any]) -> list[dict[str, str]]:
    """Lay ket qua tim kiem co cache TTL, uu tien endpoint cau hinh roi toi web mac dinh."""
    endpoint = str(cau_hinh.get("endpoint") or "").strip()
    ttl_giay = int(cau_hinh.get("ttl") or 300)
    timeout_giay = float(cau_hinh.get("timeout") or 6.0)
    khoa = f"{endpoint or 'default_web'}::{cau_hoi.strip().lower()}"
    hien_tai = time.monotonic()

    with _LOCK_CACHE_MANG:
        muc_cache = _CACHE_MANG.get(khoa)
        if muc_cache and (hien_tai - muc_cache[0]) <= ttl_giay:
            logger.info("Trung cache tra cuu mang cho '%s'", cau_hoi)
            return list(muc_cache[1])

    ket_qua: list[dict[str, str]] = []
    try:
        if endpoint:
            logger.info("Tra cuu mang qua endpoint cau hinh: %s", endpoint)
            ket_qua = _goi_endpoint_json(cau_hoi, endpoint, timeout_giay)
        if not ket_qua:
            logger.info("Tra cuu web truc tiep qua nguon mac dinh cho '%s'", cau_hoi)
            ket_qua = _goi_tim_kiem_mac_dinh(cau_hoi, timeout_giay)
    except Exception as loi:
        logger.warning("Loi tra cuu mang cho '%s': %s", cau_hoi, loi)
        return []

    if ket_qua:
        with _LOCK_CACHE_MANG:
            _CACHE_MANG[khoa] = (hien_tai, list(ket_qua))
    return ket_qua


def _phan_hoi_fallback(ds_link_hop_le: list[dict[str, str]], ly_do: str) -> str:
    """Chi dung khi loi ket noi hoac khong lay duoc ket qua that; khong bia link/so lieu."""
    link_md = dinh_dang_link_tham_khao(ds_link_hop_le)
    return "\n\n".join([
        f"🌐 {ly_do} nên mình không suy đoán thông tin thời gian thực hay tự bịa link.",
        link_md or "**Link tham khảo:** Hiện chưa lấy được nguồn tham khảo trực tuyến cho câu hỏi này.",
    ])


def xu_ly_tra_cuu_mang(
    cau_hoi: str,
    link_cau_hinh: list[dict[str, str]] | None = None,
) -> str:
    """Thuc thi tra cuu mang truc tiep, tong hop ngan gon qua LLM va chi fallback khi loi."""
    cau_hinh = _doc_cau_hinh_mang()
    ds_link_hop_le = [
        m for m in (link_cau_hinh or []) if isinstance(m, dict) and _la_url_hop_le(str(m.get("url") or ""))
    ]

    if not cau_hinh["bat"]:
        logger.info("Luot tra_mang dang duoc tam tat qua AI_SYS_ENABLE_WEB_SEARCH.")
        return _phan_hoi_fallback(ds_link_hop_le, "Luồng tra cứu mạng đang được tắt trên máy này")

    ket_qua_tim = _lay_ket_qua_tim_kiem(cau_hoi, cau_hinh)
    if not ket_qua_tim:
        logger.info("Khong lay duoc ket qua mang hoac gap loi ket noi, su dung fallback.")
        return _phan_hoi_fallback(
            ds_link_hop_le,
            "Hiện chưa lấy được kết quả từ mạng hoặc kết nối mạng tạm gián đoạn",
        )

    goi_y_nguon = "\n".join(
        f"- {m.get('tieu_de')}: {m.get('tom_tat')} ({m.get('url')})"
        for m in ket_qua_tim
        if m.get("tom_tat")
    )
    if goi_y_nguon:
        chi_dan = (
            "Tóm tắt ngắn gọn, chính xác bằng tiếng Việt dựa trên dữ liệu tìm kiếm sau; "
            "không suy diễn ngoài dữ liệu và không tự bịa thêm link:\n" + goi_y_nguon
        )
        tom_tat = goi_llm_huong_dan(
            cau_hoi,
            chi_dan,
            timeout_giay=TIMEOUT_LLM_CHAT_GIAY,
            num_predict=int(cau_hinh["num_predict"]),
        )
    else:
        tom_tat = "🌐 Đã tìm thấy các nguồn tham khảo liên quan trên web:"

    link_md = dinh_dang_link_tham_khao(ket_qua_tim)
    return "\n\n".join([tom_tat, link_md]).strip()