# ============================================================================
# File Path: dieu_phoi_y_dinh/dich_vu/mau_y_dinh.py
# Module: Kho Mau Y Dinh & Cham Diem Trong So
# Linked Files: tach_da_y_dinh.py, ngu_canh_hoi_thoai.py
# Purpose: Tap trung kho tu khoa/mau cau theo tung nhom y dinh, tach biet
#          tra cuu noi bo code/DB voi hoi dap kien thuc/quy dinh va xu ly huy y dinh.
# ============================================================================

import logging
import re

logger = logging.getLogger(__name__)

MAU_HUY_Y_DINH = (
    r"\b(bỏ\s+ý\s+định|bo\s+y\s+dinh|hủy\s+ý\s+định|huy\s+y\s+dinh|"
    r"không\s+tạo\s+nữa|khong\s+tao\s+nua|không\s+làm\s+nữa|khong\s+lam\s+nua|"
    r"thôi\s+không|thoi\s+khong|dừng\s+làm|dung\s+lam|hủy\s+làm|huy\s+lam)\b"
)

MAU_HOI_LIET_KE_CAU_TRUC = (
    r"(các|cac|những|nhung|mọi|moi|toàn\s+bộ|toan\s+bo)\s+"
    r"(class|hàm|ham|biến|bien|hằng|hang|file|tệp|tep|folder|thư\s+mục|thu\s+muc|app|module|model|bảng|bang)|"
    r"(liệt\s+kê|liet\s+ke|thống\s+kê|thong\s+ke|kể\s+tên|ke\s+ten)\b[\s\S]{0,60}"
    r"\b(app|folder|thư\s+mục|thu\s+muc|file|tệp|tep|hàm|ham|biến|bien|hằng|hang|class|model)\b|"
    r"(class|hàm|ham|biến|bien|file|tệp|tep|folder|thư\s+mục|thu\s+muc|app|model|bảng|bang)\s+(gì|gi|nào|nao)|"
    r"(có|co)\s+(class|hàm|ham|biến|bien|file|tệp|tep|folder|thư\s+mục|thu\s+muc|app|model|bảng|bang)|"
    r"cấu\s+trúc\s+(hệ\s+thống|dự\s+án\s+code|dự\s+án|code|app)|"
    r"cau\s+truc\s+(he\s+thong|du\s+an\s+code|du\s+an|code|app)|"
    r"trong\s+(code|mã\s+nguồn|ma\s+nguon|source|hệ\s+thống|he\s+thong|dự\s+án|du\s+an)"
)

# Cau truc moi nhom:
# - loai_nhanh: chat | db_file | tim_kiem_mang | phan_tich_nghiep_vu
# - mau_cao: diem +3 (cum tu ro nghia)
# - mau_thuong: diem +1 (tu khoa ho tro)
KHO_MAU_Y_DINH: list[dict] = [
    {
        "ma_nhom": "cau_truc_du_an",
        "loai_nhanh": "db_file",
        "mau_cao": [
            r"(các|cac)\s+class",
            r"class\s+(gì|gi)",
            r"(các|cac)\s+(hàm|ham|biến|bien|hằng|hang|folder|thư\s+mục|thu\s+muc|tệp|tep)",
            r"(hàm|ham|biến|bien|hằng|hang|folder|thư\s+mục|thu\s+muc|tệp|tep)\s+(gì|gi|nào|nao)",
            r"(liệt\s+kê|liet\s+ke|thống\s+kê|thong\s+ke)\b[\s\S]{0,60}"
            r"\b(app|folder|thư\s+mục|thu\s+muc|file|tệp|tep|hàm|ham|biến|bien|hằng|hang|class|model)\b",
            r"(có|co)\s+(file|tệp|tep|folder|thư\s+mục|thu\s+muc|app|class|hàm|ham|biến|bien|model)",
            r"(file|tệp|tep|folder|thư\s+mục|thu\s+muc|app|model)\s+(gì|gi|nào|nao)",
            r"cấu\s+trúc\s+(hệ\s+thống|dự\s+án|mã\s+nguồn|code)|cau\s+truc\s+(he\s+thong|du\s+an|ma\s+nguon|code)",
            r"mã\s+nguồn|ma\s+nguon|migration|model",
        ],
        "mau_thuong": [
            r"\b(class|hàm|ham|biến|bien|hằng|hang|folder|thư\s+mục|thu\s+muc|file|tệp|tep|module|code|source)\b",
        ],
    },
    {
        "ma_nhom": "tim_kiem_thong_tin",
        "loai_nhanh": "tim_kiem_mang",
        "mau_cao": [
            r"tra\s+(thông\s+tin|thong\s+tin|cứu|cuu|mạng|mang)",
            r"tìm\s+(kiếm|kiem|thông\s+tin|thong\s+tin)",
            r"\bvụ\s+.+\s+là\s+vụ\s+gì\b|\bvu\s+.+\s+la\s+vu\s+gi\b",
            r"thông\s+tin\s+vụ|thong\s+tin\s+vu",
            r"\b(luật|luat|quy\s+định|quy\s+dinh|nghị\s+định|nghi\s+dinh|thông\s+tư|thong\s+tu)\b",
            r"có\s+nội\s+dung\s+gì|co\s+noi\s+dung\s+gi|quy\s+định\s+(gì|gi|sao|thế\s+nào)",
            r"mới\s+nhất|moi\s+nhat|tin\s+tức|tin\s+tuc",
        ],
        "mau_thuong": [
            r"\b(scandal|phốt|phot|sự\s+kiện|su\s+kien|google|tìm|tim|pháp\s+luật|phap\s+luat|xây\s+dựng|xay\s+dung)\b",
        ],
    },
    {
        "ma_nhom": "du_lieu_db_file",
        "loai_nhanh": "db_file",
        "mau_cao": [
            r"truy\s+vấn|truy\s+van|lấy\s+dữ\s+liệu|lay\s+du\s+lieu",
            r"bảng\s+dữ\s+liệu|bang\s+du\s+lieu|đối\s+soát|doi\s+soat|hóa\s+đơn|hoa\s+don",
        ],
        "mau_thuong": [
            r"\b(db|database|excel|csv|pdf|dữ\s+liệu|du\s+lieu)\b",
        ],
    },
    {
        "ma_nhom": "chat_trao_doi",
        "loai_nhanh": "chat",
        "mau_cao": [
            r"^(chào|chao|hi+|hello+|helo+|hey+|yo|alo)\b",
            r"\b(tao|mình|minh|tôi|toi|em|anh)\s+(là|la|tên|ten)\b",
            r"\btên\s+(tao|mình|minh|tôi|toi|em|anh)\s+(là|la|gì|gi)?\b",
            r"\b(nhắc\s+lại\s+tên|nhac\s+lai\s+ten|nhớ\s+tên|nho\s+ten)\b",
            r"\b(mày|may|bạn|ban)\s+(tên\s+gì|ten\s+gi|là\s+ai|la\s+ai)\b",
            r"\b(nội\s+dung\s+trao\s+đổi|noi\s+dung\s+trao\s+doi|lịch\s+sử\s+trao\s+đổi|lich\s+su\s+trao\s+doi)\b",
            r"\b(thông\s+tin\s+máy|thong\s+tin\s+may|cấu\s+hình\s+máy|cau\s+hinh\s+may|máy\s+(tao|mình|minh|tôi|toi))\b",
            r"(sao\s+rồi|sao\s+roi|ổn\s+không|on\s+khong|đang\s+làm\s+gì|dang\s+lam\s+gi)",
        ],
        "mau_thuong": [
            r"\b(cảm\s+ơn|cam\s+on|ok|oke|ê|e|nhắc\s+lại|nhac\s+lai|lúc\s+nãy|luc\s+nay|vừa\s+hỏi|vua\s+hoi)\b",
        ],
    },
    {
        "ma_nhom": "phan_tich_xay_dung",
        "loai_nhanh": "phan_tich_nghiep_vu",
        "mau_cao": [
            r"(tạo|tao|viết|viet|làm|lam)\s+(tao\s+)?(app|ap|hệ\s+thống|he\s+thong|chức\s+năng|chuc\s+nang)",
            r"(sửa|sua|đổi\s+tên|doi\s+ten|đặt\s+lại\s+tên|dat\s+lai\s+ten)\b.*\b(app|ap|tên|ten|code)\b",
            r"phân\s+tích\s+(phương\s+án|phuong\s+an|nghiệp\s+vụ|nghiep\s+vu)",
            r"nâng\s+cấp|nang\s+cap|sửa\s+code|sua\s+code|lập\s+đầu\s+mục|lap\s+dau\s+muc",
        ],
        "mau_thuong": [
            r"\b(tạo|tao|viết|viet|nâng\s+cấp|nang\s+cap|phương\s+án|phuong\s+an|tính|tinh)\b",
        ],
    },
]


def cham_diem_y_dinh(van_ban: str) -> tuple[str, str, int]:
    """Cham diem cac nhom mau; tra (ma_nhom, loai_nhanh, diem_cao_nhat)."""
    thuong = (van_ban or "").strip().lower()
    if not thuong:
        return "chat_trao_doi", "chat", 1

    # 1. Cau huy/bo y dinh lam app hoac doi y dinh -> di chat, khong ep lap dau muc lam moi
    if re.search(MAU_HUY_Y_DINH, thuong):
        logger.debug("Phat hien sac thai huy y dinh trong '%s' -> chat_trao_doi", thuong)
        return "chat_trao_doi", "chat", 2

    diem_tung_nhom: list[tuple[int, str, str]] = []
    for nhom in KHO_MAU_Y_DINH:
        ma_nhom = nhom["ma_nhom"]
        # Neu nhac 'app' nhung khong hoi liet ke/cau truc thi bo qua cau_truc_du_an
        if ma_nhom == "cau_truc_du_an" and "app" in thuong and not re.search(MAU_HOI_LIET_KE_CAU_TRUC, thuong):
            continue

        diem = 0
        for mau in nhom.get("mau_cao", []):
            if re.search(mau, thuong):
                diem += 3
        for mau in nhom.get("mau_thuong", []):
            if re.search(mau, thuong):
                diem += 1
        if diem > 0:
            diem_tung_nhom.append((diem, ma_nhom, nhom["loai_nhanh"]))

    if diem_tung_nhom:
        diem_tung_nhom.sort(key=lambda x: x[0], reverse=True)
        diem_nhat, ma_nhat, loai_nhat = diem_tung_nhom[0]
        logger.debug("Cham diem y dinh '%s' -> %s (%s, diem=%d)", thuong, ma_nhat, loai_nhat, diem_nhat)
        return ma_nhat, loai_nhat, diem_nhat

    # Khong khop mau nao: neu khong yeu cau tao moi/lam app thi coi la chat trao doi
    if not re.search(r"\b(tạo|tao|viết|viet|làm|lam|sửa|sua|xây|xay|nâng\s+cấp|nang\s+cap)\b", thuong):
        return "chat_trao_doi", "chat", 0

    return "phan_tich_xay_dung", "phan_tich_nghiep_vu", 0