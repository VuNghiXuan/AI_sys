# ============================================================================
# File Path: dieu_phoi_y_dinh/dich_vu/xu_ly_chat.py
# Module: Xu Ly Nhanh Chat & Chit-Chat
# Linked Files: bo_nao_cache_cosine.py, dieu_phoi_nhanh.py, ngu_canh_hoi_thoai.py
# Purpose: Xu ly cac cau chao hoi, tu gioi thieu, nhac lai thong tin/ten tu
#          lich su trao doi va chat nhanh ma khong ep chon phuong an.
# ============================================================================

import logging
import re

from .bo_nao_cache_cosine import goi_ollama_phan_tich
from .ngu_canh_hoi_thoai import xu_ly_cau_hoi_nhac_lai

logger = logging.getLogger(__name__)


def _phan_hoi_nhanh_theo_mau(noi_dung: str) -> str | None:
    """Tra loi tuc thi cac mau chao hoi/tu gioi thieu/hoi tham ngan."""
    thuong = (noi_dung or "").strip().lower()

    khop_ten = re.search(
        r"\b(?:tao|mình|minh|tôi|toi)\s+(?:là|la)\s+([a-zA-Z0-9_à-ỹ\s]{1,30})",
        thuong,
    )
    if khop_ten:
        ten_goi = khop_ten.group(1).strip().title()
        return f"Chào {ten_goi}! Mình đã ghi nhận trong phiên này. Bạn cần mình hỗ trợ gì tiếp theo?"

    if re.search(r"^(chào|chao|hi+|hello+|helo+|hey+|yo|alo|ê|e)\b", thuong):
        return (
            "Chào bạn! Mình đang sẵn sàng. Bạn cần chat trao đổi nhanh, "
            "tra cứu app/file/class/DB, tìm thông tin, hay phân tích/lập đầu mục nghiệp vụ?"
        )

    if re.search(
        r"\b(sao\s+rồi|sao\s+roi|ổn\s+không|on\s+khong|đang\s+làm\s+gì|dang\s+lam\s+gi|khỏe\s+không|khoe\s+khong)\b",
        thuong,
    ):
        return (
            "Hệ thống đang hoạt động bình thường trên máy local. "
            "Bạn cứ nhập yêu cầu hoặc hỏi tiếp, mình điều phối theo từng nhánh cho bạn."
        )

    if re.search(r"\b(cảm\s+ơn|cam\s+on|ok|oke|được\s+đấy|duoc\s+day|hay\s+đấy|hay\s+day)\b", thuong):
        return "Ok bạn! Cần test thêm nhánh nào hoặc nâng cấp tiếp phần nào cứ bảo mình."

    return None


def xu_ly_nhanh_chat(noi_dung: str) -> dict:
    """Dieu phoi xu ly cho nhanh chat/chit-chat."""
    sach = (noi_dung or "").strip()
    logger.info("Bat dau xu ly nhanh chat: %s", sach)

    tra_loi_nhac_lai = xu_ly_cau_hoi_nhac_lai(sach)
    if tra_loi_nhac_lai:
        return {
            "buoc": 0,
            "loai_nhanh": "chat",
            "nhan_nhanh": "Chat & Ngữ cảnh",
            "noi_dung": sach,
            "ket_qua": tra_loi_nhac_lai,
        }

    tra_loi_nhanh = _phan_hoi_nhanh_theo_mau(sach)
    if tra_loi_nhanh:
        return {
            "buoc": 0,
            "loai_nhanh": "chat",
            "nhan_nhanh": "Chat & Trao đổi",
            "noi_dung": sach,
            "ket_qua": tra_loi_nhanh,
        }

    phan_hoi_ollama = goi_ollama_phan_tich(
        f"Trả lời ngắn gọn, thân thiện, đúng trọng tâm bằng tiếng Việt cho câu trao đổi: '{sach}'."
    )
    ket_qua = phan_hoi_ollama or (
        f"Đã tiếp nhận trao đổi: \"{sach}\". Bạn muốn mình giải đáp thêm hay chuyển sang truy vấn/phân tích nghiệp vụ?"
    )

    return {
        "buoc": 0,
        "loai_nhanh": "chat",
        "nhan_nhanh": "Chat & Trao đổi",
        "noi_dung": sach,
        "ket_qua": ket_qua,
    }