# ============================================================================
# File Path: dieu_phoi_y_dinh/dich_vu/tach_da_y_dinh.py
# Module: Tach Da Y Dinh & Nhan Dien Linh Vuc
# Linked Files: bo_nao_cache_cosine.py, mau_y_dinh.py, dieu_phoi_nhanh.py
# Purpose: Tach nhieu y dinh/nhanh cho prompt ngan va chia cum ngu canh tong quat
#          cho prompt dai phuc vu test luong dieu phoi, khong hardcode nghiep vu le.
# ============================================================================

import json
import logging
import re

from .bo_nao_cache_cosine import goi_ollama_phan_tich, lay_ngu_canh_noi_tiep
from .mau_y_dinh import cham_diem_y_dinh

logger = logging.getLogger(__name__)

NGUONG_PROMPT_DAI = 500
SO_NHANH_TOI_DA_PROMPT_DAI = 4

_MAU_TEN_FILE = re.compile(
    r"\b[\w\-]+\.(?:py|js|ts|html|css|json|md|sql|txt|yaml|yml|xml|sh|bat)\b",
    flags=re.IGNORECASE,
)
_MAU_SO_SANH = re.compile(
    r"\b(phân\s+biệt|phan\s+biet|so\s+sánh|so\s+sanh|khác\s+nhau|khac\s+nhau|"
    r"giống\s+nhau|giong\s+nhau|đối\s+chiếu|doi\s+chieu)\b",
    flags=re.IGNORECASE,
)
_MAU_NGU_CANH_MA_NGUON = re.compile(
    r"\b(file|tệp|tep|hàm|ham|class|lớp|lop|biến|bien|module|mã\s+nguồn|ma\s+nguon|"
    r"dự\s+án|du\s+an|hệ\s+thống|he\s+thong|liên\s+quan|lien\s+quan|import)\b",
    flags=re.IGNORECASE,
)


def _lam_sach_phu_tro_test(van_ban: str) -> str:
    """Loai bo phan chon phuong an noi duoi khi test de giu noi dung goc sach."""
    text = (van_ban or "").strip()
    text = re.sub(
        r"\s*(?:—|-)?\s*Chọn\s+1\s+phương\s+án:[\s\S]*$",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"\s*=>\s*[^\n]+$", "", text, flags=re.IGNORECASE)
    return text.strip()


def _la_truy_van_ma_nguon_hoac_so_sanh(van_ban: str) -> bool:
    """Kiem tra prompt ngan co chua ten file hoac cau so sanh/phan biet ve ma nguon."""
    text = (van_ban or "").strip()
    if not text:
        return False
    if _MAU_TEN_FILE.search(text):
        return True
    if _MAU_SO_SANH.search(text) and _MAU_NGU_CANH_MA_NGUON.search(text):
        return True
    return False


def xac_dinh_linh_vuc(van_ban: str) -> tuple[str, str]:
    """Nhan dien linh vuc tong quat theo ngu canh prompt."""
    thuong = (van_ban or "").lower()
    if re.search(r"\b(tính\s+lương|tinh\s+luong|lương|luong|chấm\s+công|cham\s+cong|thưởng|thuong|kpi)\b", thuong):
        return "luong_nhan_su", "Lương & Nhân sự"
    if re.search(r"\b(class|hàm|ham|file|module|mã\s+nguồn|ma\s+nguon|migration|model|logic)\b", thuong):
        return "cau_truc_du_an", "Cấu trúc & Mã nguồn dự án"
    if re.search(r"(\bdb\b|database|excel|csv|pdf|hóa\s+đơn|hoa\s+don|đối\s+soát|doi\s+soat)", thuong):
        return "du_lieu_nghiep_vu", "Dữ liệu & Nghiệp vụ"
    if re.search(r"\b(cộng|cong|trừ|tru|nhân|nhan|chia|phép\s+toán|phep\s+toan|2\s+số|2\s+so|hai\s+số|hai\s+so)\b", thuong):
        return "toan_hoc_tien_ich", "Tiện ích tính toán"
    if re.search(
        r"\b(luật|luat|quy\s+định|quy\s+dinh|nghị\s+định|nghi\s+dinh|thông\s+tư|thong\s+tu|"
        r"tra\s+thông\s+tin|tra\s+thong\s+tin|tra\s+cứu|tra\s+cuu|tìm\s+kiếm|tim\s+kiem|tin\s+tức|tin\s+tuc|mới\s+nhất|moi\s+nhat)\b",
        thuong,
    ):
        return "tra_cuu_thong_tin", "Tra cứu & Thông tin"
    return "tong_quat", "Đa ngành / Tổng quát"


def phan_loai_loai_nhanh(ve_cau: str) -> str:
    """Phan loai tung ve qua bo cham diem mau_y_dinh."""
    try:
        _, loai_nhanh, _ = cham_diem_y_dinh(ve_cau)
        return loai_nhanh
    except Exception as loi:
        logger.error("Loi phan_loai_loai_nhanh cho '%s': %s", ve_cau, loi, exc_info=True)
        return "chat"


def _tach_cum_lon_prompt_dai(goc: str, so_nhanh_toi_da: int = SO_NHANH_TOI_DA_PROMPT_DAI) -> list[str]:
    """Fallback tach prompt dai theo ranh gioi cau/chuyen y lon va gop doan ngan."""
    doan_lon = re.split(
        r"(?:\r?\n\s*\r?\n)+|[.!?]+(?:\s+|$)|\b(?:đồng\s+thời|dong\s+thoi|kèm\s+theo|kem\s+theo|ngoài\s+ra|ngoai\s+ra|tiếp\s+theo|tiep\s+theo)\b",
        goc,
        flags=re.IGNORECASE,
    )
    sach_lon = [d.strip(" ,:-") for d in doan_lon if len(d.strip(" ,:-")) >= 4]
    if not sach_lon:
        return [goc[:900]]

    cum_hop_nhat: list[str] = []
    for doan in sach_lon:
        if cum_hop_nhat and len(doan) < 60 and len(cum_hop_nhat[-1]) < 450:
            cum_hop_nhat[-1] = f"{cum_hop_nhat[-1]} — {doan}"
        else:
            cum_hop_nhat.append(doan)

    if len(cum_hop_nhat) <= so_nhanh_toi_da:
        return [c[:900] for c in cum_hop_nhat]

    ket_qua: list[str] = []
    kich_thuoc = max(1, (len(cum_hop_nhat) + so_nhanh_toi_da - 1) // so_nhanh_toi_da)
    for i in range(0, len(cum_hop_nhat), kich_thuoc):
        ket_qua.append(" | ".join(cum_hop_nhat[i : i + kich_thuoc])[:900])
    return ket_qua[:so_nhanh_toi_da]


def _la_cau_hoi_lai_hoac_tu_choi(cum: str) -> bool:
    """Loc bo cac cum do model hoi lai hoac tu choi tom tat."""
    thuong = (cum or "").strip().lower()
    return bool(
        re.search(
            r"(có\s+vẻ\s+như|tôi\s+sẽ\s+cần\s+biết|bạn\s+muốn\s+tôi\s+tóm\s+tắt|vui\s+lòng\s+cung\s+cấp|không\s+phải\s+là\s+một\s+câu)",
            thuong,
        )
    )


def _tach_nhanh_bang_model_tom_tat(goc: str, so_nhanh_toi_da: int = SO_NHANH_TOI_DA_PROMPT_DAI) -> list[str] | None:
    """Goi model tom tat & chia ngu canh cho prompt dai; tra None neu loi de fallback rule."""
    doan_rut_gon = goc[:2400]
    prompt_tom_tat = (
        f"Hãy chia nội dung dưới đây thành tối đa {so_nhanh_toi_da} cụm ý theo ngữ cảnh chính "
        "(ví dụ: tra cứu quy định/thông tin, chỉnh sửa/áp dụng logic hệ thống, phân tích nghiệp vụ/yêu cầu). "
        "Giữ sát nội dung của từng cụm, không đặt câu hỏi ngược lại. "
        "Chỉ trả về một mảng JSON gồm các chuỗi ngắn gọn, không thêm lời dẫn.\n"
        f"Nội dung:\n{doan_rut_gon}"
    )
    try:
        phan_hoi = goi_ollama_phan_tich(prompt_tom_tat, timeout_giay=25)
        if not phan_hoi:
            return None
        khop_json = re.search(r"\[[\s\S]*\]", phan_hoi)
        if not khop_json:
            return None
        ds_cum = json.loads(khop_json.group(0))
        if not isinstance(ds_cum, list):
            return None
        cum_sach = [
            str(x).strip()
            for x in ds_cum
            if str(x).strip() and not _la_cau_hoi_lai_hoac_tu_choi(str(x))
        ]
        if len(cum_sach) < 2:
            return None
        logger.info("Model tom tat chia duoc %d cum ngu canh cho prompt dai", len(cum_sach[:so_nhanh_toi_da]))
        return cum_sach[:so_nhanh_toi_da]
    except Exception as loi:
        logger.warning("Buoc tom tat chia ngu canh loi, fallback ve rule: %s", loi, exc_info=True)
        return None


def _chuan_hoa_loai_nhanh_prompt_dai(ve: str, loai_nhanh: str, ma_nhom: str) -> tuple[str, str]:
    """Chi giu db_file cho prompt dai khi thuc su co yeu cau truy van/kiem tra DB/ma nguon/file."""
    thuong = (ve or "").lower()
    co_tin_hieu_he_thong_thuc = bool(
        re.search(
            r"\b(truy\s+vấn\s+db|truy\s+van\s+db|bảng\s+db|bang\s+db|mã\s+nguồn|ma\s+nguon|"
            r"trong\s+code|file\s+dự\s+án|file\s+du\s+an|class\s+nào|hàm\s+nào|ham\s+nao)\b",
            thuong,
        )
    )
    if loai_nhanh == "db_file" and not co_tin_hieu_he_thong_thuc:
        return "phan_tich_nghiep_vu", "phan_tich_xay_dung"
    return loai_nhanh, ma_nhom


def tach_cac_nhanh_y_dinh(prompt: str) -> list[dict]:
    """Tach 1 prompt thanh danh sach cac nhanh y dinh co thu tu."""
    goc_tho = _lam_sach_phu_tro_test((prompt or "").strip())
    if not goc_tho:
        return []

    la_prompt_dai = len(goc_tho) > NGUONG_PROMPT_DAI
    giu_nguyen_nhanh_ma_nguon = (not la_prompt_dai) and _la_truy_van_ma_nguon_hoac_so_sanh(goc_tho)

    try:
        if giu_nguyen_nhanh_ma_nguon:
            prompt_day_du = goc_tho
        else:
            prompt_day_du = goc_tho if la_prompt_dai else lay_ngu_canh_noi_tiep(goc_tho)
    except Exception as loi:
        logger.warning("Khong noi duoc ngu canh tiep, dung prompt goc: %s", loi, exc_info=True)
        prompt_day_du = goc_tho

    goc = _lam_sach_phu_tro_test((prompt_day_du or "").strip())
    if not goc:
        return []

    if giu_nguyen_nhanh_ma_nguon:
        ve_hop_le = [goc]
    elif la_prompt_dai:
        ve_hop_le = _tach_nhanh_bang_model_tom_tat(goc)
        if not ve_hop_le:
            ve_hop_le = _tach_cum_lon_prompt_dai(goc)
    else:
        cac_phan = re.split(
            r"(?:\r?\n)+|[.;!?]+|\b(?:rồi|roi|sau\s+đó|sau\s+do|đồng\s+thời|dong\s+thoi|kèm\s+theo|kem\s+theo)\b",
            goc,
            flags=re.IGNORECASE,
        )
        ve_hop_le = [p.strip(" ,:-") for p in cac_phan if len(p.strip(" ,:-")) >= 2]
        if not ve_hop_le:
            ve_hop_le = [goc]

    danh_sach_nhanh: list[dict] = []
    for stt, ve in enumerate(ve_hop_le, start=1):
        ma_nhom, loai_nhanh, diem = cham_diem_y_dinh(ve)
        if giu_nguyen_nhanh_ma_nguon:
            loai_nhanh = "db_file"
            ma_nhom = "cau_truc_ma_nguon"
            diem = max(diem, 1.0)
        elif la_prompt_dai:
            loai_nhanh, ma_nhom = _chuan_hoa_loai_nhanh_prompt_dai(ve, loai_nhanh, ma_nhom)
        ma_lv, ten_lv = xac_dinh_linh_vuc(ve)
        danh_sach_nhanh.append({
            "buoc": stt,
            "noi_dung": ve,
            "ma_nhom": ma_nhom,
            "loai_nhanh": loai_nhanh,
            "diem_mau": diem,
            "ma_linh_vuc": ma_lv,
            "ten_linh_vuc": ten_lv,
            "la_prompt_dai": la_prompt_dai,
        })

    logger.info(
        "Da tach %d nhanh y dinh (prompt_dai=%s): %s",
        len(danh_sach_nhanh),
        la_prompt_dai,
        [(n["ma_nhom"], n["loai_nhanh"], n["diem_mau"]) for n in danh_sach_nhanh],
    )
    return danh_sach_nhanh