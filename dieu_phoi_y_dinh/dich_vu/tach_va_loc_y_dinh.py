# ============================================================================
# File Path: dieu_phoi_y_dinh/dich_vu/tach_va_loc_y_dinh.py
# Module: Dieu Phoi Pheu 3 Tang (Phan Mien, Tach Hanh Dong Va Loc Ranh Gioi)
# Linked Files: dieu_phoi_y_dinh/dich_vu/dinh_tuyen/khoi_tao_y_dinh.py,
#               dieu_phoi_y_dinh/dich_vu/hoc_tang_cuong_qa.py,
#               dieu_phoi_y_dinh/dich_vu/dieu_phoi_nhanh.py,
#               dieu_phoi_y_dinh/dich_vu/thuc_thi_nhanh/ho_tro_llm_he_thong.py
# Purpose: Chuan hoa prompt, phan mien nhanh tang 1, tach da y dinh theo
#          hanh dong/ve doc lap tang 2, loc ranh gioi va ke thua ngu canh tang 3.
# ============================================================================

import logging
import re
from typing import Any

from dieu_phoi_y_dinh.dich_vu.dinh_tuyen.khoi_tao_y_dinh import registry
from dieu_phoi_y_dinh.dich_vu.hoc_tang_cuong_qa import la_tin_hieu_dinh_chinh, lay_diem_hoc_y_dinh

logger = logging.getLogger(__name__)

MA_Y_DINH_MAC_DINH = "chat_tu_do"
MAX_Y_DINH_CON = 4

# Bang chuan hoa loi go tat/thieu dau pho bien truoc dinh tuyen.
CHUAN_HOA_THUONG_GAP: tuple[tuple[str, str], ...] = (
    (r"(?:^|[\s,;])dong\s+du\s+lieu(?:$|[\s,;.!?])", " dòng dữ liệu "),
    (r"(?:^|[\s,;])so\s+dong(?:$|[\s,;.!?])", " số dòng "),
    (r"(?:^|[\s,;])tung\s+ham(?:$|[\s,;.!?])", " từng hàm "),
    (r"(?:^|[\s,;])mo\s+ta(?:$|[\s,;.!?])", " mô tả "),
    (r"(?:^|[\s,;])may\s+dang\s+chay(?:$|[\s,;.!?])", " máy đang chạy "),
    (r"(?:^|[\s,;])mua\s+hay\s+nang(?:$|[\s,;.!?])", " mưa hay nắng "),
    (r"(?:^|[\s,;])vang\s+loi(?:$|[\s,;.!?])", " văng lỗi "),
    (r"(?:^|[\s,;])teen(?:$|[\s,;.!?])", " tên "),
    (r"(?:^|[\s,;])nhuc(?:$|[\s,;.!?])", " nhắc "),
    (r"(?:^|[\s,;])nghanh(?:$|[\s,;.!?])", " ngành "),
    (r"\balo+\b", " alo "),
)

# Tang 1: Phan mien va khop tuyen nhanh (< 0.05s, khong goi LLM).
MAU_TAO_APP = re.compile(
    r"^\s*(?:tạo|tao|lập|lap|xây\s+dựng|xay\s+dung)\s+(?:app|ứng\s+dụng|ung\s+dung)\b",
    flags=re.IGNORECASE,
)
MAU_XA_GIAO_NGAN = re.compile(
    r"^\s*(?:alo|hello|hi|hey|xin\s+chào|chào(?:\s+buổi\s+(?:sáng|trưa|chiều|tối))?|"
    r"(?:ok|okay|ừ|dạ)?\s*(?:cảm\s+ơn|cam\s+on|cám\s+ơn|thanks|thank\s+you)|tạm\s+biệt)"
    r"(?:\s+(?:nhé|nha|ạ|bạn|em|anh|nhiều|rất\s+nhiều|ad|bot))*[.!?]*\s*$",
    flags=re.IGNORECASE,
)
MAU_GIOI_THIEU_TEN = re.compile(
    r"^\s*(?:(?:tên|ten)\s+(?:tôi|tao|mình|minh|anh|em)\s+(?:là|la)\s+\S+|"
    r"(?:tôi|tao|mình|minh|anh|em)\s+(?:tên|ten)\s+(?:là|la\s+)?\S+)",
    flags=re.IGNORECASE,
)
MAU_HOI_NHAC_TEN = re.compile(
    r"\b(?:nhắc|nhac|nhớ|nho|nhức|nhuc)\s+(?:lại\s+)?(?:tên|teen|ten)\b|\b(?:tên|teen|ten)\s+(?:tôi|tao|mình|minh|anh|em)\s+(?:là\s+|la\s+)?(?:gì|gi)\b",
    flags=re.IGNORECASE,
)
MAU_HOI_DANH_SACH_FILE = re.compile(
    r"\b(?:có\s+(?:những\s+)?file\s+gì|những\s+file\s+nào|file\s+nào\s+liên\s+quan|danh\s+sách\s+file|liệt\s+kê\s+file)\b",
    flags=re.IGNORECASE,
)
MAU_HOI_CHUC_NANG_FILE = re.compile(
    r"\b(?:chức\s+năng|chuc\s+nang|vai\s+trò|nhiệm\s+vụ)\b.*\b(?:từng\s+file|mỗi\s+file|các\s+file)\b",
    flags=re.IGNORECASE,
)
MAU_THONG_KE_DB = re.compile(
    r"(?:mấy\s+dòng|bao\s+nhiêu\s+dòng|số\s+dòng|dòng\s+dữ\s+liệu|số\s+bản\s+ghi|đếm|thong\s+ke\s+so\s+ban\s+ghi)",
    flags=re.IGNORECASE,
)
MAU_TELEMETRY = re.compile(
    r"(?:(?:^|[\s,;])(?:ram|cpu|gpu|ollama|telemetry)(?:$|[\s,;.!?])|"
    r"\b(?:cấu\s+hình\s+phần\s+cứng|cau\s+hinh\s+may|cấu\s+hình\s+máy|model\s+ollama|máy\s+đang\s+chạy)\b|"
    r"\bmáy\b.*\b(?:model|cấu\s+hình|phần\s+cứng)\b)",
    flags=re.IGNORECASE,
)
MAU_THOI_TIET_MANG = re.compile(
    r"(?:mưa\s+hay\s+nắng|nắng\s+hay\s+mưa|ngoài\s+trời|có\s+mưa|thời\s+tiết|giá\s+vàng|tỷ\s+giá|tin\s+tức)",
    flags=re.IGNORECASE,
)

# Tang 2: Tach theo dau ngat manh / tu noi chuyen buoc, giu cum danh tu ghep.
MAU_TACH_MANH = re.compile(r"(?:\s*;\s*|\s*\n+\s*|\s+(?:rồi|roi|xong thì|sau đó|đồng thời)\s+)", flags=re.IGNORECASE)
MAU_DONG_TU_HANH_DONG = re.compile(
    r"\b(?:viết|viet|sửa|sua|kiểm\s+tra|kiem\s+tra|đếm|dem|thống\s+kê|thong\s+ke|"
    r"tạo|tao|lập|lap|phân\s+tích|phan\s+tich|hướng\s+dẫn|huong\s+dan|tìm|tim)\b",
    flags=re.IGNORECASE,
)
MAU_CUM_DANH_TU_GHEP = re.compile(
    r"(?:app\s+và\s+model|model\s+và\s+app|hàm\s+và\s+biến|biến\s+và\s+hàm|"
    r"hàm\s+và\s+file|file\s+và\s+hàm|ram\s+với\s+ollama|ram\s+và\s+ollama|"
    r"đơn\s+hàng\s+và\s+công\s+nợ|app\s+và\s+trường)",
    flags=re.IGNORECASE,
)

# Tang 3: Loc ranh gioi, ngu canh noi bo va luot hoi thoai tiep noi.
MAU_NGU_CANH_NOI_BO = re.compile(
    r"\b(?:trong\s+dự\s+án|trong\s+hệ\s+thống|hệ\s+thống|dự\s+án|codebase|mã\s+nguồn|"
    r"database|db|model|app|file|hàm|biến)\b",
    flags=re.IGNORECASE,
)
MAU_HOI_HAM = re.compile(
    r"(?:hàm|ham|biến|bien|function|def\s+|chức\s+năng\s+(?:từng|các)\s+hàm|từng\s+hàm|hàm\s+mà|ham\s+ma)",
    flags=re.IGNORECASE,
)
MAU_DEBUG_CODE = re.compile(r"(?:chia\s+cho\s+0|văng\s+lỗi|lỗi\s+vậy|traceback|exception|bug)", flags=re.IGNORECASE)
MAU_LO_MO_KHONG_CHOT = re.compile(
    r"^(?:chắc\s+làm|để\s+xem|tính\s+làm|nay\s+đầu\s+óc|hôm\s+nay\s+(?:hơi\s+)?(?:mệt|căng))",
    flags=re.IGNORECASE,
)
MAU_DOI_DANG_BANG_NOI_TIEP = re.compile(r"^(?:là\s+)?(?:lập|đổi|chuyển|kẻ)\s+(?:thành\s+)?bảng", flags=re.IGNORECASE)
MAU_XAC_NHAN_NGAN = re.compile(r"^(?:ừ|uh|ừm|vâng|dạ|ok|okay|đúng\s+rồi)[.!?]*$", flags=re.IGNORECASE)
MAU_CAU_HOI_NOI_TIEP = re.compile(
    r"^(?:vậy\s+|thế\s+|còn\s+|thế\s+còn\s+|vậy\s+thì\s+)?"
    r"(?:(?:ngành|nghành|cái|mục|phần|loại|trường|mã|nhóm|môn|khối)\s+nào|"
    r"chi\s+tiết\s+hơn|cụ\s+thể\s+hơn|giải\s+thích\s+thêm|nói\s+rõ\s+hơn|"
    r"tại\s+sao|vì\s+sao|thế\s+nào|ra\s+sao|bao\s+nhiêu)\b",
    flags=re.IGNORECASE,
)
MAU_YEU_CAU_BANG = re.compile(
    r"\b(?:lập|đổi|chuyển|kẻ|tạo|xuất|hiển\s+thị)\b.*\b(?:thành\s+)?bảng\b|\bdạng\s+bảng\b",
    flags=re.IGNORECASE,
)


def chuan_hoa_truoc_dinh_tuyen(prompt_sach: str) -> str:
    """Chuan hoa cac cum thieu dau/viet tat de tang do khop y dinh."""
    ket_qua = (prompt_sach or "").strip()
    for mau, thay_bang in CHUAN_HOA_THUONG_GAP:
        ket_qua = re.sub(mau, thay_bang, ket_qua, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", ket_qua).strip()


def _phan_mien_tang_1(doan_chuan: str) -> str | None:
    """Tang 1: Bat nhanh mien/y dinh ro rang khong qua suy luan nang."""
    if MAU_TAO_APP.search(doan_chuan):
        return "tao_app_chuyen_trang"
    if (
        MAU_XA_GIAO_NGAN.match(doan_chuan)
        or MAU_GIOI_THIEU_TEN.search(doan_chuan)
        or MAU_HOI_NHAC_TEN.search(doan_chuan)
    ):
        return MA_Y_DINH_MAC_DINH
    if MAU_HOI_DANH_SACH_FILE.search(doan_chuan) or MAU_HOI_CHUC_NANG_FILE.search(doan_chuan):
        return "hoi_dap_he_thong_chi_tiet"
    if MAU_THONG_KE_DB.search(doan_chuan) and not MAU_HOI_HAM.search(doan_chuan):
        return "thong_ke_du_lieu_db"
    if MAU_TELEMETRY.search(doan_chuan) and not MAU_THONG_KE_DB.search(doan_chuan):
        return "tra_cuu_telemetry_va_model"
    if MAU_THOI_TIET_MANG.search(doan_chuan):
        return "tra_cuu_mang_va_thoi_su"
    return None


def _lay_luot_user_gan_nhat(lich_su: list[dict[str, Any]] | None) -> tuple[str, str]:
    """Lay (noi_dung_truoc, ma_y_dinh_truoc) cua luot user gan nhat."""
    for luot in reversed(lich_su or []):
        if luot.get("role") == "assistant":
            continue
        yd = str(luot.get("y_dinh") or "").strip()
        nd = str(luot.get("content") or "").strip()
        if yd:
            return nd, yd
    return "", ""


def _co_the_tach_ve_va(ve_trai: str, ve_phai: str) -> bool:
    """Chi tach theo 'và' khi vế phải có động từ hành động/câu hỏi độc lập và không phải cụm ghép."""
    ve_phai_sach = ve_phai.strip(" ,;.")
    if len(ve_phai_sach) < 4:
        return False
    if MAU_CUM_DANH_TU_GHEP.search(f"{ve_trai} và {ve_phai_sach}"):
        return False
    return bool(MAU_DONG_TU_HANH_DONG.search(ve_phai_sach) or "?" in ve_phai_sach)


def _tach_doan_prompt(prompt_sach: str) -> list[str]:
    """Tang 2: Tach prompt theo dau ngat/tu noi buoc va 'và' khi vế sau mang hành động riêng."""
    doan_manh = [p.strip(" ,;.") for p in MAU_TACH_MANH.split(prompt_sach) if len(p.strip(" ,;.")) >= 2]
    ket_qua: list[str] = []

    for doan in (doan_manh or [prompt_sach]):
        cac_phan_va = re.split(r"\s+và\s+", doan, flags=re.IGNORECASE)
        if len(cac_phan_va) <= 1:
            ket_qua.append(doan)
            continue

        ve_hien_tai = cac_phan_va[0].strip(" ,;.")
        for phan_ke in cac_phan_va[1:]:
            if _co_the_tach_ve_va(ve_hien_tai, phan_ke):
                ket_qua.append(ve_hien_tai)
                ve_hien_tai = phan_ke.strip(" ,;.")
            else:
                ve_hien_tai = f"{ve_hien_tai} và {phan_ke.strip(' ,;.')}"
        if ve_hien_tai:
            ket_qua.append(ve_hien_tai)

    return ket_qua or [prompt_sach]


def loc_y_dinh_ranh_gioi(
    prompt_chuan: str,
    ma_yd_goi_y: str,
    lich_su: list[dict[str, Any]] | None = None,
) -> str:
    """Tang 3: Dieu chinh y dinh theo ranh gioi cau hoi, ngu canh luot truoc va hoc Q&A."""
    yd_tang_1 = _phan_mien_tang_1(prompt_chuan)
    if yd_tang_1 is not None:
        logger.info("Tang 1 chot y dinh nhanh -> %s", yd_tang_1)
        return yd_tang_1

    if MAU_LO_MO_KHONG_CHOT.search(prompt_chuan):
        return MA_Y_DINH_MAC_DINH

    _, yd_truoc = _lay_luot_user_gan_nhat(lich_su)
    if MAU_XAC_NHAN_NGAN.match(prompt_chuan.strip()):
        yd_xac_nhan = yd_truoc if yd_truoc and yd_truoc != "tra_cuu_telemetry_va_model" else MA_Y_DINH_MAC_DINH
        logger.info("Xac nhan ngan -> %s", yd_xac_nhan)
        return yd_xac_nhan

    if MAU_HOI_HAM.search(prompt_chuan):
        logger.info("Loc ranh gioi bat cau hoi ham/bien -> viet_code_va_phan_tich")
        return "viet_code_va_phan_tich"

    if (
        yd_truoc
        and not MAU_NGU_CANH_NOI_BO.search(prompt_chuan)
        and MAU_CAU_HOI_NOI_TIEP.search(prompt_chuan)
        and ma_yd_goi_y in {"huong_dan_su_dung_nhanh", MA_Y_DINH_MAC_DINH}
    ):
        logger.info("Ke thua y dinh luot truoc cho cau hoi noi tiep -> %s", yd_truoc)
        return yd_truoc

    if MAU_DOI_DANG_BANG_NOI_TIEP.search(prompt_chuan) and yd_truoc:
        logger.info("Noi tiep yeu cau lap bang theo luot truoc -> %s", yd_truoc)
        return yd_truoc

    if la_tin_hieu_dinh_chinh(prompt_chuan) and yd_truoc:
        logger.info("Dinh chinh y dinh theo luot truoc -> %s", yd_truoc)
        return yd_truoc

    if MAU_DEBUG_CODE.search(prompt_chuan):
        return "viet_code_va_phan_tich"
    if ma_yd_goi_y == "tra_cuu_mang_va_thoi_su" and MAU_NGU_CANH_NOI_BO.search(prompt_chuan):
        logger.info("Chan tra_cuu_mang_va_thoi_su nham tren ngu canh noi bo -> %s", MA_Y_DINH_MAC_DINH)
        return MA_Y_DINH_MAC_DINH

    diem_hoc = lay_diem_hoc_y_dinh(prompt_chuan, ma_yd_goi_y)
    if diem_hoc <= -1.0 and ma_yd_goi_y != MA_Y_DINH_MAC_DINH:
        logger.info("Y dinh '%s' co diem hoc am (%.2f), chuyen ve %s", ma_yd_goi_y, diem_hoc, MA_Y_DINH_MAC_DINH)
        return MA_Y_DINH_MAC_DINH
    return ma_yd_goi_y


def phan_tich_cac_y_dinh(
    prompt_sach: str,
    lich_su: list[dict[str, Any]] | None = None,
) -> list[tuple[str, str]]:
    """Tach va xac dinh danh sach (doan_cau, ma_y_dinh) dung thu tu, khong trung lap."""
    doan_ds = _tach_doan_prompt(prompt_sach)
    ket_qua: list[tuple[str, str]] = []
    da_co_ma: set[str] = set()

    for doan in doan_ds[:MAX_Y_DINH_CON]:
        doan_chuan = chuan_hoa_truoc_dinh_tuyen(doan)
        yd_nhanh = _phan_mien_tang_1(doan_chuan)
        if yd_nhanh is not None:
            ma_yd = yd_nhanh
        else:
            yd = registry.khop_nhanh(doan_chuan, dung_ngu_nghia=True)
            ma_goi_y = yd.ma_y_dinh if yd else MA_Y_DINH_MAC_DINH
            ma_yd = loc_y_dinh_ranh_gioi(doan_chuan, ma_goi_y, lich_su=lich_su)

        doan_thuc_thi = doan
        if ma_yd == "tra_cuu_mang_va_thoi_su" and MAU_CAU_HOI_NOI_TIEP.search(doan_chuan):
            prompt_truoc, yd_truoc = _lay_luot_user_gan_nhat(lich_su)
            if prompt_truoc and yd_truoc == "tra_cuu_mang_va_thoi_su":
                doan_thuc_thi = f"{prompt_truoc} - {doan}"
                logger.info("Ghep ngu canh luot truoc cho tra_cuu_mang: %s", doan_thuc_thi)

        if ma_yd not in da_co_ma:
            da_co_ma.add(ma_yd)
            ket_qua.append((doan_thuc_thi, ma_yd))

    logger.info("Ket qua phan tich da y dinh: %s", ket_qua)
    return ket_qua or [(prompt_sach, MA_Y_DINH_MAC_DINH)]