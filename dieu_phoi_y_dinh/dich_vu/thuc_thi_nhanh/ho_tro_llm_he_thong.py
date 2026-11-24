# ============================================================================
# File Path: dieu_phoi_y_dinh/dich_vu/thuc_thi_nhanh/ho_tro_llm_he_thong.py
# Module: Ho Tro LLM Ollama, Dinh Dang Bang Linh Dong Va Huong Dan He Thong
# Linked Files: dieu_phoi_y_dinh/dich_vu/thuc_thi_nhanh/trinh_xu_ly_chung.py,
#               quan_ly_du_an/services_telemetry.py,
#               dieu_phoi_y_dinh/cau_hinh/cau_hinh_y_dinh.json,
#               PROJECT_MAP_COMPACT.md,
#               PROJECT_MAP.md
# Purpose: Xu ly goi Ollama (tach model nhanh/code), loc ky tu CJK, quet AST
#          ham va sinh bang Markdown linh dong cho liet ke / so sanh theo prompt.
# ============================================================================

import ast
import json
import logging
import os
from pathlib import Path
import re
from urllib import request as url_request

from quan_ly_du_an.services_telemetry import lay_danh_sach_model_ollama

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
MODEL_CHAT_DU_PHONG = os.environ.get("OLLAMA_CHAT_MODEL", "qwen2.5:3b")
MODEL_NHANH_MAC_DINH = os.environ.get("OLLAMA_FAST_CHAT_MODEL", "qwen2.5:3b")
TIMEOUT_LLM_CODE_GIAY = float(os.environ.get("OLLAMA_TIMEOUT_CODE_GIAY", "45.0"))
TIMEOUT_LLM_CHAT_GIAY = float(os.environ.get("OLLAMA_TIMEOUT_CHAT_GIAY", "20.0"))
NUM_PREDICT_MAC_DINH = int(os.environ.get("OLLAMA_NUM_PREDICT_DEFAULT", "320"))
NUM_PREDICT_HUONG_DAN = int(os.environ.get("OLLAMA_NUM_PREDICT_HUONG_DAN", "384"))
MAX_LUOT_NGU_CANH = 8
MAX_DONG_FILE_MAP = 80
MAX_HAM_MOI_FILE = 8

_MAU_KY_TU_CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]+")
_MAU_YEU_CAU_BANG = re.compile(
    r"\b(?:thành\s+bảng|lập\s+bảng|dạng\s+bảng|kẻ\s+bảng|vẽ\s+bảng|tạo\s+bảng|bảng\s+so\s+sánh|bảng\s+liệt\s+kê)\b",
    flags=re.IGNORECASE,
)
_MAU_SO_SANH = re.compile(
    r"\b(?:so\s+sánh|đối\s+chiếu|khác\s+nhau|giống\s+nhau|hơn\s+kém|ưu\s+nhược)\b",
    flags=re.IGNORECASE,
)

DANH_MUC_CHUC_NANG_HE_THONG: tuple[tuple[str, str], ...] = (
    ("Hỏi cấu trúc & thống kê DB", "Liệt kê app/model/trường hoặc đếm số bản ghi trực tiếp từ Django ORM."),
    ("Xem cấu hình máy & model Ollama", "Lấy thông số CPU/RAM/GPU thực tế và danh sách model đang chạy/đã cài."),
    ("Tra cứu file, hàm & biến dự án", "Đọc `PROJECT_MAP_COMPACT.md` / `PROJECT_MAP.md` và quét AST hàm/biến thực tế."),
    ("Điều phối đơn/đa ý định & nhớ tên", "Tách đa hành động, lọc ranh giới, giữ ngữ cảnh phiên và nhớ tên người dùng."),
    ("Hỏi đáp, sinh code & tạo app", "Gọi LLM cục bộ qua Ollama hoặc chuyển sang luồng Xưởng Tạo App."),
)

DANH_MUC_CAU_TRUC_HE_THONG: tuple[tuple[str, str, str], ...] = (
    ("Cấu hình ý định", "`dieu_phoi_y_dinh/cau_hinh/cau_hinh_y_dinh.json`", "Khai báo mã ý định, nhóm lớn, chế độ xử lý và từ khóa"),
    ("Khởi tạo & Registry", "`dieu_phoi_y_dinh/dich_vu/dinh_tuyen/khoi_tao_y_dinh.py`", "Nạp cấu hình ý định, khớp nhanh và thực thi ý định"),
    ("Điều phối đơn/đa ý định", "`dieu_phoi_y_dinh/dich_vu/dieu_phoi_nhanh.py`", "Chuẩn hóa prompt, lọc ranh giới, tách đa ý định, phiên & cache"),
    ("Thực thi theo chế độ", "`dieu_phoi_y_dinh/dich_vu/thuc_thi_nhanh/trinh_xu_ly_chung.py`", "Truy vấn DB/telemetry, nhớ tên, gọi LLM hoặc chuyển Xưởng Tạo App"),
    ("Hỗ trợ LLM & hệ thống", "`dieu_phoi_y_dinh/dich_vu/thuc_thi_nhanh/ho_tro_llm_he_thong.py`", "Gọi Ollama cục bộ, trả cấu trúc hệ thống và quy trình thêm ý định"),
    ("Bộ nhớ phiên & cache", "`dieu_phoi_y_dinh/dich_vu/bo_nho_va_cache.py`", "Lưu lịch sử hội thoại theo phiên, tên người dùng và cache TTL"),
    ("Hiển thị & render bảng", "`quan_ly_du_an/static/quan_ly_du_an/js/dieu_khien/`", "`dieu_khoi_render_bang.js` và `hien_thi_hoi_thoai.js`"),
    ("Bản đồ dự án & test", "`PROJECT_MAP.md` & `dieu_phoi_y_dinh/tests/`", "Sơ đồ liên kết module và bộ test hồi quy/tổng hợp"),
)

QUY_TRINH_THEM_Y_DINH: tuple[str, ...] = (
    "1. **Khai báo ý định** trong `dieu_phoi_y_dinh/cau_hinh/cau_hinh_y_dinh.json` (mã ý định, nhóm lớn, mô tả ngữ nghĩa, chế độ xử lý, từ khóa/mẫu câu).",
    "2. **Kiểm tra nạp & khớp ý định** tại `dieu_phoi_y_dinh/dich_vu/dinh_tuyen/khoi_tao_y_dinh.py` để `khop_nhanh` nhận diện đúng.",
    "3. **Bổ sung xử lý hoặc ranh giới** trong `dieu_phoi_y_dinh/dich_vu/thuc_thi_nhanh/trinh_xu_ly_chung.py` và `dieu_phoi_y_dinh/dich_vu/dieu_phoi_nhanh.py` (giữ mỗi file dưới 300 dòng, có header + liên kết file + log).",
    "4. **Cập nhật sơ đồ liên kết** tại `PROJECT_MAP.md` theo quy chuẩn hệ thống.",
    "5. **Thêm test case** vào `dieu_phoi_y_dinh/tests/test_bo_cau_hoi_y_dinh.py` và `dieu_phoi_y_dinh/tests/test_tong_hop_dieu_phoi.py` rồi chạy kiểm thử.",
)


def _tim_goc_du_an() -> Path:
    """Tim thu muc goc chua manage.py."""
    hien_tai = Path(__file__).resolve()
    for cha in [hien_tai.parent, *hien_tai.parents]:
        if (cha / "manage.py").exists():
            return cha
    return hien_tai.parents[4] if len(hien_tai.parents) > 4 else hien_tai.parent


def lay_ten_model_chat_mac_dinh(uu_tien_nhanh: bool = False) -> str:
    """Lay model chat phu hop: uu tien model nhe (3b) cho chat/tom tat nhanh."""
    if uu_tien_nhanh and MODEL_NHANH_MAC_DINH:
        return MODEL_NHANH_MAC_DINH
    try:
        info = lay_danh_sach_model_ollama() or {}
    except Exception as loi:
        logger.warning("Khong lay duoc danh sach model Ollama: %s", loi)
        return MODEL_CHAT_DU_PHONG

    for ds_key in ("running_models", "installed_models"):
        for muc in info.get(ds_key) or []:
            ten = str(muc.get("name") or "").strip()
            if ten and "embed" not in ten.lower():
                return ten
    return MODEL_CHAT_DU_PHONG


def dinh_dang_link_tham_khao(link_tham_khao: list[dict[str, str]] | None) -> str:
    """Chi dinh dang khi co link web hop le; khong tra ve dong bao thieu link."""
    hop_le = [
        f"- [{str(m.get('tieu_de') or m.get('url')).strip()}]({str(m.get('url')).strip()})"
        for m in (link_tham_khao or [])
        if str(m.get("url") or "").strip().startswith(("http://", "https://"))
    ]
    if not hop_le:
        return ""
    return "### Link tham khảo\n" + "\n".join(hop_le)


def _lam_sach_phan_hoi_tieng_viet(van_ban: str) -> str:
    """Loai bo ky tu CJK neu model bi lech ngon ngu o cuoi cau."""
    if not _MAU_KY_TU_CJK.search(van_ban or ""):
        return (van_ban or "").strip()
    sach = _MAU_KY_TU_CJK.sub("", van_ban or "")
    sach = re.sub(r"[，。！？；：、（）【】《》]+", " ", sach)
    return re.sub(r"\s+", " ", sach).strip() or "Em đã ghi nhận thông tin của anh."


def _xay_dung_chi_dan_bang_linh_dong(cau_hoi: str, chi_dan_goc: str) -> str:
    """Tao chi dan ep LLM sinh bang Markdown linh dong theo dung yeu cau liet ke/so sanh."""
    if _MAU_SO_SANH.search(cau_hoi or ""):
        quy_tac_bang = (
            "Trình bày dưới dạng bảng Markdown so sánh linh hoạt theo các tiêu chí phù hợp nhất với câu hỏi "
            "(ví dụ: Tiêu chí, Đối tượng/Phương án, Điểm mạnh/Khác biệt, Ghi chú). "
            "Tự chọn cột theo đúng ngữ cảnh câu hỏi, giữ nội dung từng ô ngắn gọn."
        )
    else:
        quy_tac_bang = (
            "Trình bày danh sách/thông tin dưới dạng bảng Markdown linh hoạt với tên cột tự chọn phù hợp "
            "với nội dung và yêu cầu cụ thể trong câu hỏi (không gò ép vào khuôn cột cố định). "
            "Có thể thêm 1-2 dòng tóm tắt ngắn gọn bên dưới bảng."
        )
    nen = (chi_dan_goc or "Trả lời ngắn gọn, chính xác, tự nhiên bằng tiếng Việt.").strip()
    return f"{nen}\n{quy_tac_bang}"


def goi_llm_huong_dan(
    cau_hoi: str,
    chi_dan: str,
    timeout_giay: float = TIMEOUT_LLM_CODE_GIAY,
    num_predict: int = NUM_PREDICT_MAC_DINH,
    lich_su: list[dict[str, str]] | None = None,
    uu_tien_nhanh: bool = False,
) -> str:
    """Goi model local qua Ollama kem ngu canh cac luot gan nhat va loc CJK."""
    phan_lich_su = ""
    if lich_su:
        dong_ls = [
            f"- {m.get('role', 'user')}: {m.get('content', '')}"
            for m in lich_su[-MAX_LUOT_NGU_CANH:]
            if str(m.get("content") or "").strip()
        ]
        if dong_ls:
            phan_lich_su = "Ngữ cảnh các lượt gần nhất:\n" + "\n".join(dong_ls) + "\n\n"

    model = lay_ten_model_chat_mac_dinh(uu_tien_nhanh=uu_tien_nhanh)
    gioi_han_token = max(64, int(num_predict))
    system_prompt = (
        (chi_dan or "Trả lời ngắn gọn, chính xác, tự nhiên bằng tiếng Việt.")
        + "\nBắt buộc chỉ dùng tiếng Việt (hoặc thuật ngữ kỹ thuật tiếng Anh nếu cần), tuyệt đối không dùng chữ Trung Quốc."
    )
    payload = json.dumps({
        "model": model,
        "system": system_prompt,
        "prompt": f"{phan_lich_su}Câu hỏi hiện tại: {cau_hoi}" if phan_lich_su else cau_hoi,
        "stream": False,
        "options": {"temperature": 0.2, "num_predict": gioi_han_token},
    }).encode("utf-8")
    req = url_request.Request(
        f"{OLLAMA_BASE_URL}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        logger.info("Goi Ollama model=%s (timeout=%.1fs, num_predict=%d)", model, timeout_giay, gioi_han_token)
        with url_request.urlopen(req, timeout=timeout_giay) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
        ket_qua = _lam_sach_phan_hoi_tieng_viet(str(raw.get("response") or ""))
        return ket_qua or "Chưa có phản hồi từ model."
    except Exception as loi:
        logger.warning("Loi goi Ollama (%s): %s", model, loi)
        return f"⚠️ Chưa gọi được model local ({model}): {loi}"


def _liet_ke_danh_sach_y_dinh_tu_json(dang_bang: bool) -> str:
    """Doc danh sach y dinh da khai bao tu cau_hinh_y_dinh.json."""
    goc = _tim_goc_du_an()
    tep_json = goc / "dieu_phoi_y_dinh" / "cau_hinh" / "cau_hinh_y_dinh.json"
    if not tep_json.is_file():
        return ""
    try:
        du_lieu = json.loads(tep_json.read_text(encoding="utf-8"))
    except Exception as loi:
        logger.warning("Khong doc duoc %s: %s", tep_json, loi)
        return ""

    ds_yd = [m for m in (du_lieu.get("y_dinh") or []) if isinstance(m, dict) and m.get("ma_y_dinh")]
    if not ds_yd:
        return ""

    logger.info("Lay danh sach %d y dinh tu %s", len(ds_yd), tep_json)
    if dang_bang:
        dong = [
            f"🎯 **Danh sách ý định trong hệ thống ({len(ds_yd)} mã):**",
            "",
            "| Mã ý định | Nhóm lớn | Chế độ xử lý | Mô tả |",
            "| --- | --- | --- | --- |",
        ]
        for muc in ds_yd:
            ma = str(muc.get("ma_y_dinh") or "").strip()
            nhom = str(muc.get("nhom_lon") or "").strip()
            che_do = str(muc.get("che_do_xu_ly") or "").strip()
            mo_ta = str(muc.get("mo_ta_ngu_nghia") or "").strip()
            dong.append(f"| `{ma}` | {nhom} | `{che_do}` | {mo_ta} |")
        return "\n".join(dong)

    dong = [f"🎯 **Danh sách ý định trong hệ thống ({len(ds_yd)} mã):**"]
    for muc in ds_yd:
        ma = str(muc.get("ma_y_dinh") or "").strip()
        che_do = str(muc.get("che_do_xu_ly") or "").strip()
        mo_ta = str(muc.get("mo_ta_ngu_nghia") or "").strip()
        dong.append(f"- `{ma}` (`{che_do}`): {mo_ta}")
    return "\n".join(dong)


def _dinh_dang_chuc_nang_he_thong() -> str:
    """Tra ve danh sach cac chuc nang chinh cua he thong."""
    dong = ["⚙️ **Các chức năng chính của hệ thống:**"]
    for ten, mo_ta in DANH_MUC_CHUC_NANG_HE_THONG:
        dong.append(f"- **{ten}:** {mo_ta}")
    return "\n".join(dong)


def _trich_danh_sach_file_tu_map() -> str:
    """Doc truc tiep PROJECT_MAP_COMPACT.md (hoac PROJECT_MAP.md) de lay danh sach file."""
    goc = _tim_goc_du_an()
    for ten_tep in ("PROJECT_MAP_COMPACT.md", "PROJECT_MAP.md"):
        tep = goc / ten_tep
        if not tep.is_file():
            continue
        try:
            noi_dung = tep.read_text(encoding="utf-8", errors="replace")
        except Exception as loi:
            logger.warning("Khong doc duoc %s: %s", tep, loi)
            continue

        cac_dong_file = [dong.strip() for dong in noi_dung.splitlines() if dong.strip().startswith("- `")]
        if cac_dong_file:
            logger.info("Lay danh sach %d file truc tiep tu %s", len(cac_dong_file), ten_tep)
            hien_thi = cac_dong_file[:MAX_DONG_FILE_MAP]
            them = (
                f"\n- ... *(còn {len(cac_dong_file) - MAX_DONG_FILE_MAP} file khác trong {ten_tep})*"
                if len(cac_dong_file) > MAX_DONG_FILE_MAP
                else ""
            )
            return f"📂 **Danh sách file từ `{ten_tep}`:**\n" + "\n".join(hien_thi) + them
    return ""


def _liet_ke_tung_ham_he_thong() -> str:
    """Quet AST cac file cot loi de liet ke tung ham va docstring ngan gon."""
    goc = _tim_goc_du_an()
    cac_tep = [
        goc / "dieu_phoi_y_dinh" / "dich_vu" / "tach_va_loc_y_dinh.py",
        goc / "dieu_phoi_y_dinh" / "dich_vu" / "dieu_phoi_nhanh.py",
        goc / "dieu_phoi_y_dinh" / "dich_vu" / "thuc_thi_nhanh" / "trinh_xu_ly_chung.py",
        goc / "dieu_phoi_y_dinh" / "dich_vu" / "thuc_thi_nhanh" / "ho_tro_llm_he_thong.py",
        goc / "dieu_phoi_y_dinh" / "dich_vu" / "thuc_thi_nhanh" / "tra_cuu_mang.py",
    ]
    dong_kq = ["🧩 **Danh sách hàm chính theo từng file (quét AST):**"]
    so_file_co_ham = 0

    for tep in cac_tep:
        if not tep.is_file():
            continue
        try:
            cay = ast.parse(tep.read_text(encoding="utf-8", errors="replace"))
        except Exception as loi:
            logger.warning("Khong parse AST duoc %s: %s", tep, loi)
            continue

        cac_ham = [node for node in cay.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
        if not cac_ham:
            continue

        so_file_co_ham += 1
        rel_path = tep.relative_to(goc).as_posix()
        ds_ten_ham: list[str] = []
        for ham in cac_ham[:MAX_HAM_MOI_FILE]:
            doc = (ast.get_docstring(ham) or "").splitlines()[0].strip() if ast.get_docstring(ham) else ""
            ds_ten_ham.append(f"`{ham.name}()` ({doc})" if doc else f"`{ham.name}()`")
        if len(cac_ham) > MAX_HAM_MOI_FILE:
            ds_ten_ham.append(f"+{len(cac_ham) - MAX_HAM_MOI_FILE} hàm khác")
        dong_kq.append(f"- **`{rel_path}`:** " + ", ".join(ds_ten_ham))

    if not so_file_co_ham:
        return ""
    logger.info("Da quet AST tung ham cho %d file cot loi.", so_file_co_ham)
    return "\n".join(dong_kq)


def _dinh_dang_cau_truc_he_thong(dang_bang: bool) -> str:
    """Tra ve cau truc he thong hien tai dang danh sach hoac bang Markdown."""
    if dang_bang:
        dong = [
            "📐 **Các cấu trúc hệ thống hiện tại:**",
            "",
            "| Cấu trúc | File / Module liên quan | Vai trò chính |",
            "| --- | --- | --- |",
        ]
        for ten, tep, vai_tro in DANH_MUC_CAU_TRUC_HE_THONG:
            dong.append(f"| {ten} | {tep} | {vai_tro} |")
        return "\n".join(dong)

    dong = ["📐 **Các cấu trúc hệ thống hiện tại:**"]
    for ten, tep, vai_tro in DANH_MUC_CAU_TRUC_HE_THONG:
        dong.append(f"- **{ten}:** {tep} — {vai_tro}.")
    return "\n".join(dong)


def xu_ly_huong_dan_he_thong(
    cau_hoi: str,
    chi_dan: str,
    link_tham_khao: list[dict[str, str]] | None = None,
    lich_su: list[dict[str, str]] | None = None,
) -> str:
    """Tra loi nhanh cau hoi noi bo; sinh bang linh dong khi so sanh/liet ke tuy bien."""
    cau_thuong = (cau_hoi or "").lower()
    dang_bang = bool(_MAU_YEU_CAU_BANG.search(cau_thuong))
    dang_so_sanh = bool(_MAU_SO_SANH.search(cau_thuong))
    hoi_them_yd = bool(re.search(r"\b(?:thêm\s+ý\s+định|tạo\s+ý\s+định)\b", cau_thuong))
    hoi_tung_ham = bool(re.search(r"\b(?:từng\s+hàm|mỗi\s+hàm|các\s+hàm|chức\s+năng\s+hàm|hàm\s+trong)\b", cau_thuong))
    hoi_tung_file = bool(
        re.search(r"\b(?:từng\s+file|mỗi\s+file|chức\s+năng\s+file|vai\s+trò\s+file|chức\s+năng\s+từng\s+file)\b", cau_thuong)
    )
    hoi_danh_sach_yd = bool(re.search(r"\b(?:ý\s+định|y\s+dinh)\b", cau_thuong)) and not hoi_them_yd
    hoi_danh_sach_file = bool(
        re.search(r"\b(?:có\s+file\s+nào|danh\s+sách\s+file|các\s+file|file\s+liên\s+quan)\b", cau_thuong)
    )
    hoi_chuc_nang = bool(re.search(r"\b(?:chức\s+năng|tính\s+năng|làm\s+được\s+gì)\b", cau_thuong))
    hoi_cau_truc = bool(
        re.search(r"\b(?:cấu\s+trúc|kiến\s+trúc|file\s+nào|liên\s+quan|app|module|model)\b", cau_thuong)
    )

    phan_chinh: list[str] = []
    if dang_so_sanh or (
        dang_bang
        and not any((hoi_them_yd, hoi_tung_ham, hoi_tung_file, hoi_danh_sach_yd, hoi_danh_sach_file, hoi_chuc_nang, hoi_cau_truc))
    ):
        logger.info("Sinh bang Markdown linh dong (so_sanh=%s, bang=%s).", dang_so_sanh, dang_bang)
        chi_dan_bang = _xay_dung_chi_dan_bang_linh_dong(cau_hoi, chi_dan)
        phan_chinh.append(
            goi_llm_huong_dan(
                cau_hoi,
                chi_dan_bang,
                TIMEOUT_LLM_CODE_GIAY,
                NUM_PREDICT_HUONG_DAN,
                lich_su,
                uu_tien_nhanh=True,
            )
        )
    elif hoi_them_yd:
        logger.info("Tra loi quy trinh them y dinh chuan.")
        phan_chinh.append(
            "🛠️ **Cách thêm ý định mới vào `dieu_phoi_y_dinh`:**\n"
            + "\n".join(QUY_TRINH_THEM_Y_DINH)
            + "\n\n"
            + _dinh_dang_cau_truc_he_thong(dang_bang=False)
        )
    elif hoi_tung_ham:
        logger.info("Tra loi danh sach tung ham theo file.")
        phan_chinh.append(_liet_ke_tung_ham_he_thong() or _dinh_dang_cau_truc_he_thong(dang_bang=dang_bang))
    elif hoi_tung_file:
        logger.info("Tra loi chuc nang tung file/module (dang_bang=%s).", dang_bang)
        cau_truc = _dinh_dang_cau_truc_he_thong(dang_bang=dang_bang)
        ds_tu_map = _trich_danh_sach_file_tu_map()
        phan_chinh.append(f"{cau_truc}\n\n{ds_tu_map}".strip() if ds_tu_map else cau_truc)
    elif hoi_danh_sach_yd:
        ds_yd_md = _liet_ke_danh_sach_y_dinh_tu_json(dang_bang=dang_bang)
        phan_chinh.append(ds_yd_md or _dinh_dang_chuc_nang_he_thong())
    elif hoi_danh_sach_file:
        ds_tu_map = _trich_danh_sach_file_tu_map()
        phan_chinh.append(ds_tu_map or _dinh_dang_cau_truc_he_thong(dang_bang=dang_bang))
    elif hoi_chuc_nang:
        logger.info("Tra loi danh sach chuc nang he thong.")
        phan_chinh.append(_dinh_dang_chuc_nang_he_thong())
    elif hoi_cau_truc:
        logger.info("Tra loi cau truc he thong chuan (dang_bang=%s).", dang_bang)
        phan_chinh.append(_dinh_dang_cau_truc_he_thong(dang_bang=dang_bang))
    else:
        noi_dung_llm = goi_llm_huong_dan(
            cau_hoi,
            chi_dan,
            TIMEOUT_LLM_CODE_GIAY,
            NUM_PREDICT_HUONG_DAN,
            lich_su,
            uu_tien_nhanh=True,
        )
        phan_chinh.append(noi_dung_llm)

    link_md = dinh_dang_link_tham_khao(link_tham_khao)
    if link_md:
        phan_chinh.append(link_md)
    return "\n\n".join(phan_chinh)