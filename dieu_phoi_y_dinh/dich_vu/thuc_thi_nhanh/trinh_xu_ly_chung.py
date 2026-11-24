# ============================================================================
# File Path: dieu_phoi_y_dinh/dich_vu/thuc_thi_nhanh/trinh_xu_ly_chung.py
# Module: Trinh Xu Ly Dung Chung Theo Che Do
# Linked Files: dieu_phoi_y_dinh/dich_vu/thuc_thi_nhanh/truy_van_db_va_ast.py,
#               dieu_phoi_y_dinh/dich_vu/thuc_thi_nhanh/do_ma_nguon_ast.py,
#               dieu_phoi_y_dinh/dich_vu/thuc_thi_nhanh/ho_tro_llm_he_thong.py,
#               dieu_phoi_y_dinh/dich_vu/thuc_thi_nhanh/tra_cuu_mang.py,
#               dieu_phoi_y_dinh/dich_vu/dieu_phoi_nhanh.py
# Purpose: Thuc thi y dinh theo che_do_xu_ly, chuan hoa loi go ngan, nho ten,
#          chao hoi nhanh va dieu phoi sang DB/AST/do ma nguon/he thong/LLM.
# ============================================================================

from dataclasses import dataclass
import logging
from pathlib import Path
import re
from typing import Any

from .do_ma_nguon_ast import (
    phan_tich_lien_ket_file_va_ham,
    tim_vi_tri_file,
    tim_vi_tri_ham_hoac_bien,
)
from .ho_tro_llm_he_thong import (
    NUM_PREDICT_HUONG_DAN,
    TIMEOUT_LLM_CHAT_GIAY,
    TIMEOUT_LLM_CODE_GIAY,
    goi_llm_huong_dan,
    xu_ly_huong_dan_he_thong,
)
from .tra_cuu_mang import xu_ly_tra_cuu_mang
from .truy_van_db_va_ast import (
    doc_tom_tat_project_map,
    liet_ke_file_he_thong_nhanh,
    quet_ham_va_bien_du_an,
    truy_van_db_django,
)

logger = logging.getLogger(__name__)

MAX_LUOT_NGU_CANH = 8
TU_LOAI_TRU_TEN = {
    "alo", "ok", "okay", "ừ", "uh", "ừm", "vâng", "dạ",
    "không", "chào", "hi", "hello", "ai", "gì", "gi", "nào", "nao",
}
THAY_THE_GO_NHANH: tuple[tuple[str, str], ...] = (
    (r"\balo+\b", "alo"),
    (r"\bnhức\b", "nhắc"),
    (r"\bnhắ\b", "nhắc"),
    (r"\bnhac\b", "nhắc"),
    (r"\blai\b", "lại"),
    (r"\bten\b", "tên"),
    (r"\bko\b", "không"),
)
MAU_HOI_HAM = re.compile(r"\b(?:hàm|ham|chức\s+năng\s+các\s+hàm|mô\s+tả.*hàm|bảng.*hàm)\b", flags=re.IGNORECASE)
MAU_HOI_DANH_SACH_FILE = re.compile(
    r"\b(?:có\s+(?:những\s+)?file\s+gì|những\s+file\s+nào|file\s+nào\s+liên\s+quan|danh\s+sách\s+file|liệt\s+kê\s+file)\b",
    flags=re.IGNORECASE,
)
MAU_DO_LIEN_KET = re.compile(
    r"\b(?:liên\s+kết|lien\s+ket|liên\s+quan|gọi\s+hàm\s+nào|phụ\s+thuộc|phu\s+thuoc)\b",
    flags=re.IGNORECASE,
)
MAU_DO_VI_TRI_HAM = re.compile(
    r"\b(?:hàm|ham|class|biến|bien)\b.*(?:ở\s+đâu|nằm\s+ở\s+đâu|nam\s+o\s+dau|o\s+dau|file\s+nào|file\s+nao|dòng\s+mấy)",
    flags=re.IGNORECASE,
)
MAU_DO_VI_TRI_FILE = re.compile(
    r"\b(?:file|setting|settings|tệp|tep)\b.*(?:ở\s+đâu|nằm\s+ở\s+đâu|nam\s+o\s+dau|o\s+dau|đường\s+dẫn|thư\s+mục|thu\s+muc)",
    flags=re.IGNORECASE,
)
MAU_CHAO_NGAN = re.compile(
    r"^\s*(?:alo+|hello+|hi+|chào(?:\s+(?:bạn|anh|chị|em|ad|bot|ai_sys))?)\s*[.!?]*$",
    flags=re.IGNORECASE,
)


@dataclass
class ThongTinYDinhThucThi:
    """Thong tin y dinh truyen cho trinh xu ly dung chung."""

    ma_y_dinh: str
    che_do_xu_ly: str
    db_muc_tieu: str = "models_theo_app"
    mau_tra_loi: str = ""
    chi_dan_llm: str = ""
    mo_ta_ngu_nghia: str = ""
    link_tham_khao: list[dict[str, str]] | None = None


def _chuan_hoa_cau_hoi(cau_hoi: str) -> str:
    """Chuan hoa loi go ngan/thieu dau pho bien truoc khi xu ly."""
    ket_qua = (cau_hoi or "").strip()
    for mau, thay_bang in THAY_THE_GO_NHANH:
        ket_qua = re.sub(mau, thay_bang, ket_qua, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", ket_qua).strip()


def _hop_le_nhu_ten(ten_ung_vien: str) -> bool:
    """Kiem tra chuoi ung vien co hop le nhu mot ten nguoi ngan gon hay khong."""
    sach = (ten_ung_vien or "").strip(" .,!?:;\"'")
    if not sach or sach.lower() in TU_LOAI_TRU_TEN or "trợ lý" in sach.lower() or "tro ly" in sach.lower():
        return False
    return bool(re.fullmatch(r"[A-Za-zÀ-ỹ]+(?:\s+[A-Za-zÀ-ỹ]+){0,2}", sach))


def _trich_xuat_ten_tu_luot_user(cac_luot: list[dict[str, str]]) -> str:
    """Chi trich xuat ten tu cac luot co role='user' trong lich su gan nhat."""
    mau_gioi_thieu = (
        r"^(?:(?:ờ|ừ|ủa|à|ơi|hi|chào)\s+)?(?:tên\s+)?(?:tôi|tao|mình|minh|em|anh)\s+"
        r"(?:là|la)\s+([A-Za-zÀ-ỹ]+(?:\s+[A-Za-zÀ-ỹ]+)?)\s*[.!?]*$",
        r"^(?:(?:ờ|ừ|ủa|à|ơi|hi|chào)\s+)?(?:tên\s+)?(?:tôi|tao|mình|minh|em|anh)\s+"
        r"([A-Za-zÀ-ỹ]+(?:\s+[A-Za-zÀ-ỹ]+)?)\s*[.!?]*$",
    )
    for chi_so, luot in enumerate(cac_luot):
        if luot.get("role") != "user":
            continue
        noi_dung = _chuan_hoa_cau_hoi(str(luot.get("content") or ""))
        if not noi_dung:
            continue
        for mau in mau_gioi_thieu:
            khop = re.match(mau, noi_dung, flags=re.IGNORECASE)
            if khop and _hop_le_nhu_ten(khop.group(1)):
                return khop.group(1).strip(" .,!?:;")
        luot_truoc = cac_luot[chi_so - 1] if chi_so > 0 else {}
        loi_ai_truoc = str(luot_truoc.get("content") or "").lower()
        co_hoi_ten = luot_truoc.get("role") == "assistant" and any(
            cum in loi_ai_truoc for cum in ("cho mình biết tên", "tên bạn là gì", "nhắc tên", "tên gì")
        )
        if co_hoi_ten and _hop_le_nhu_ten(noi_dung):
            return noi_dung.strip(" .,!?:;")
    return ""


def _xu_ly_nho_ten_hoac_xac_nhan(
    cau_hoi: str,
    lich_su: list[dict[str, str]] | None,
    ten_da_luu: str = "",
) -> str:
    """Xu ly cau hoi nho ten hoac xac nhan ngan ('ừ', 'vâng', 'ok') noi tiep luot truoc."""
    cau_thuong = _chuan_hoa_cau_hoi(cau_hoi).lower().strip()
    cac_luot = (lich_su or [])[-MAX_LUOT_NGU_CANH:]
    ten_chot = ten_da_luu.strip() if _hop_le_nhu_ten(ten_da_luu) else _trich_xuat_ten_tu_luot_user(cac_luot)

    hoi_ten = bool(re.search(r"\b(?:tên|nhớ\s+tên)\b", cau_thuong)) and bool(
        re.search(r"\b(?:gì|nhắc|nào|ko|không)\b", cau_thuong)
    )
    if hoi_ten:
        return f"Tên anh là **{ten_chot}**." if ten_chot else "Trong đoạn chat này anh chưa nhắc tên. Anh cho em biết tên để em nhớ nhé."

    luot_ai_cuoi = next((str(l.get("content") or "").lower() for l in reversed(cac_luot) if l.get("role") == "assistant"), "")
    if cau_thuong in {"ừ", "uh", "ừm", "vâng", "dạ", "ok", "okay", "đúng rồi"}:
        if ("nhắc" in luot_ai_cuoi or "tên" in luot_ai_cuoi) and ten_chot:
            return f"Tên anh là **{ten_chot}**."
        if ten_chot:
            return f"Vâng, em nhớ tên anh là **{ten_chot}**. Anh cần em hỗ trợ phần nào tiếp theo?"
    return ""


def _xay_dung_chi_dan_kem_map(chi_dan_goc: str, goc_du_an: Path) -> str:
    """Ghep noi dung PROJECT_MAP_COMPACT.md vao chi dan LLM khi can tra loi cau truc/file."""
    tom_tat_map = doc_tom_tat_project_map(goc_du_an)
    if not tom_tat_map:
        return chi_dan_goc
    phan_dau = (chi_dan_goc or "Trả lời chính xác dựa trên bản đồ cấu trúc hệ thống dưới đây.").strip()
    return f"{phan_dau}\n\nNgữ cảnh cấu trúc từ bản đồ dự án:\n{tom_tat_map}"


def thuc_thi_theo_che_do(
    tt: ThongTinYDinhThucThi,
    goc_du_an: Path,
    cau_hoi: str,
    chi_muc: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Thuc thi y dinh theo che_do_xu_ly khai bao trong JSON."""
    cau_hoi_chuan = _chuan_hoa_cau_hoi(cau_hoi)
    che_do = (tt.che_do_xu_ly or "chat_tu_do").strip()
    chi_muc_dict = chi_muc or {}
    lich_su = chi_muc_dict.get("lich_su_hoi_thoai") if isinstance(chi_muc_dict.get("lich_su_hoi_thoai"), list) else None
    ten_da_luu = str(chi_muc_dict.get("ten_nguoi_dung") or "")
    logger.info("Thuc thi y dinh ma=%s theo che_do=%s", tt.ma_y_dinh, che_do)

    if MAU_DO_LIEN_KET.search(cau_hoi_chuan):
        return {"noi_dung": phan_tich_lien_ket_file_va_ham(goc_du_an, cau_hoi_chuan), "chuyen_huong_tao_app": False}
    if MAU_DO_VI_TRI_HAM.search(cau_hoi_chuan):
        return {"noi_dung": tim_vi_tri_ham_hoac_bien(goc_du_an, cau_hoi_chuan), "chuyen_huong_tao_app": False}
    if MAU_DO_VI_TRI_FILE.search(cau_hoi_chuan):
        return {"noi_dung": tim_vi_tri_file(goc_du_an, cau_hoi_chuan), "chuyen_huong_tao_app": False}

    if che_do == "db_truy_van":
        return {"noi_dung": truy_van_db_django(tt.db_muc_tieu, cau_hoi=cau_hoi_chuan), "chuyen_huong_tao_app": False}
    if che_do == "mau_co_dinh":
        return {"noi_dung": tt.mau_tra_loi or tt.mo_ta_ngu_nghia, "chuyen_huong_tao_app": False}
    if che_do == "huong_dan_he_thong_co_nguon":
        if MAU_HOI_DANH_SACH_FILE.search(cau_hoi_chuan):
            return {"noi_dung": liet_ke_file_he_thong_nhanh(goc_du_an), "chuyen_huong_tao_app": False}
        ds_link = chi_muc_dict.get("link_tham_khao") or tt.link_tham_khao
        return {
            "noi_dung": xu_ly_huong_dan_he_thong(cau_hoi_chuan, _xay_dung_chi_dan_kem_map(tt.chi_dan_llm, goc_du_an), ds_link, lich_su),
            "chuyen_huong_tao_app": False,
        }
    if che_do == "tra_mang":
        return {"noi_dung": xu_ly_tra_cuu_mang(cau_hoi_chuan, chi_muc_dict.get("link_tham_khao") or tt.link_tham_khao), "chuyen_huong_tao_app": False}
    if che_do == "tao_app":
        return {
            "noi_dung": f"🚀 Đã nhận ý định tạo ứng dụng mới cho yêu cầu: *\"{cau_hoi_chuan}\"*. Chuyển sang **Xưởng Tạo App** để cấu hình chi tiết.",
            "chuyen_huong_tao_app": True,
        }
    if che_do == "llm_huong_dan":
        if MAU_HOI_HAM.search(cau_hoi_chuan) and "bảng" not in cau_hoi_chuan.lower() and "mô tả" not in cau_hoi_chuan.lower():
            return {"noi_dung": quet_ham_va_bien_du_an(goc_du_an), "chuyen_huong_tao_app": False}
        chi_dan_goi = tt.chi_dan_llm
        if MAU_HOI_HAM.search(cau_hoi_chuan):
            chi_dan_goi = f"{chi_dan_goi}\n\nDanh sách hàm/biến quét thực tế từ AST:\n{quet_ham_va_bien_du_an(goc_du_an)}"
        return {
            "noi_dung": goi_llm_huong_dan(cau_hoi_chuan, chi_dan_goi, TIMEOUT_LLM_CODE_GIAY, NUM_PREDICT_HUONG_DAN, lich_su, uu_tien_nhanh=True),
            "chuyen_huong_tao_app": False,
        }

    tra_loi_nhanh = _xu_ly_nho_ten_hoac_xac_nhan(cau_hoi_chuan, lich_su, ten_da_luu=ten_da_luu)
    if tra_loi_nhanh:
        return {"noi_dung": tra_loi_nhanh, "chuyen_huong_tao_app": False}
    if MAU_CHAO_NGAN.match(cau_hoi_chuan):
        return {"noi_dung": "Chào anh, em đang sẵn sàng hỗ trợ. Anh cần xử lý hay trao đổi việc gì?", "chuyen_huong_tao_app": False}

    return {
        "noi_dung": goi_llm_huong_dan(
            cau_hoi_chuan,
            "Bạn là trợ lý AI của hệ thống AI_Sys. Trả lời hoàn toàn bằng tiếng Việt tự nhiên, ngắn gọn, chính xác; không dùng chữ Trung Quốc.",
            TIMEOUT_LLM_CHAT_GIAY,
            256,
            lich_su,
            uu_tien_nhanh=True,
        ),
        "chuyen_huong_tao_app": False,
    }