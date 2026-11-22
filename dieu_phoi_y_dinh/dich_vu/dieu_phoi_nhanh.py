# ============================================================================
# File Path: dieu_phoi_y_dinh/dich_vu/dieu_phoi_nhanh.py
# Module: Dieu Phoi Cac Nhanh Y Dinh
# Linked Files: bo_nao_cache_cosine.py, tach_da_y_dinh.py, truy_van_du_lieu.py, xu_ly_chat.py
# Purpose: Dieu phoi tung nhanh sang chat / db_file / tim_kiem_mang / phan_tich_nghiep_vu,
#          ho tro dinh dang bang Markdown dung chung va ghi nhan lich su hoi thoai.
# ============================================================================

import logging
import re

from .bo_nao_cache_cosine import (
    ghi_nhan_luot_hoi_thoai,
    goi_ollama_phan_tich,
    luu_lich_su_cau_hoi,
    tim_cau_hoi_tuong_tu,
)
from .tach_da_y_dinh import tach_cac_nhanh_y_dinh, xac_dinh_linh_vuc
from .truy_van_du_lieu import thuc_hien_truy_van_db_va_file
from .xu_ly_chat import xu_ly_nhanh_chat

logger = logging.getLogger(__name__)

# Cac cau hoi tra cuu trang thai/ma nguon/DB nen lay du lieu moi nhat, khong dung cache cu
_MA_LINH_VUC_KHONG_CACHE = {"cau_truc_du_an", "du_lieu_nghiep_vu"}

_MAU_YEU_CAU_BANG = re.compile(
    r"\b(lập\s+bảng|lap\s+bang|tạo\s+bảng|tao\s+bang|kẻ\s+bảng|ke\s+bang|dạng\s+bảng|dang\s+bang|bảng)\b",
    flags=re.IGNORECASE,
)


def _lam_sach_o_bang(gia_tri: str) -> str:
    """Chuan hoa noi dung 1 o bang Markdown, tranh lech cot do ky tu '|' hoac xuong dong."""
    return re.sub(r"\s+", " ", str(gia_tri or "").replace("|", "/")).strip()


def _muon_lap_bang(van_ban: str) -> bool:
    """Kiem tra prompt hoac nhanh co yeu cau trinh bay dang bang hay khong."""
    return bool(_MAU_YEU_CAU_BANG.search(van_ban or ""))


def _tao_bang_dau_muc_markdown(dau_muc: list[dict], noi_dung: str) -> str:
    """Chuyen danh sach dau muc giai doan thanh bang Markdown."""
    dong = [
        f"📊 Bảng các đầu mục phân tích cho: **{_lam_sach_o_bang(noi_dung)}**",
        "| Mã | Đầu mục phân tích / Triển khai | Trạng thái |",
        "| --- | --- | --- |",
    ]
    for muc in dau_muc:
        ma = _lam_sach_o_bang(muc.get("ma") or "-")
        ten = _lam_sach_o_bang(muc.get("ten") or "")
        trang_thai = _lam_sach_o_bang(muc.get("trang_thai") or "Chờ chạy")
        dong.append(f"| `{ma}` | {ten} | {trang_thai} |")
    return "\n".join(dong)


def _tao_bang_phan_tich_markdown(noi_dung: str, ghi_chu_ollama: str, phuong_an: list[dict]) -> str:
    """Chuyen phan tich & danh sach phuong an thanh bang Markdown khi nguoi dung muon lap bang."""
    dong = [
        f"📊 Bảng phân tích & phương án cho: **{_lam_sach_o_bang(noi_dung)}**",
        "| Hạng mục | Nội dung / Hướng triển khai |",
        "| --- | --- |",
    ]
    if ghi_chu_ollama:
        dong.append(f"| Gợi ý trọng tâm | {_lam_sach_o_bang(ghi_chu_ollama)} |")
    for pa in phuong_an:
        tieu_de = _lam_sach_o_bang(pa.get("tieu_de") or "Phương án")
        mo_ta = _lam_sach_o_bang(pa.get("mo_ta") or "")
        dong.append(f"| {tieu_de} | {mo_ta} |")
    return "\n".join(dong)


def _gom_ket_qua_hien_thi(cac_nhanh: list[dict], tom_tat: str = "") -> str:
    """Gom noi dung ket_qua cua cac nhanh thanh 1 chuoi de luu vao LichSuDieuPhoi."""
    ds_kq = [str(n.get("ket_qua", "")).strip() for n in (cac_nhanh or []) if str(n.get("ket_qua", "")).strip()]
    if ds_kq:
        return "\n\n".join(ds_kq)
    return (tom_tat or "").strip()


def _xu_ly_db_va_file(noi_dung: str) -> dict:
    """Dieu phoi truy van DB / tim file du lieu / quet cau truc du an."""
    logger.info("Dieu phoi nhanh DB/File/Cau truc: %s", noi_dung)
    du_lieu_tim = thuc_hien_truy_van_db_va_file(noi_dung) or {}

    if isinstance(du_lieu_tim, dict):
        noi_dung_kq = (
            du_lieu_tim.get("thong_diep")
            or du_lieu_tim.get("ket_qua")
            or du_lieu_tim.get("tom_tat")
            or du_lieu_tim.get("noi_dung")
            or ""
        ).strip()
        if not noi_dung_kq:
            ghi_chu = str(du_lieu_tim.get("ghi_chu") or "").strip()
            if du_lieu_tim.get("co_du_lieu") is False:
                noi_dung_kq = (
                    f"Chưa có dữ liệu trả về cho truy vấn '{noi_dung}'."
                    + (f" ({ghi_chu})" if ghi_chu else "")
                )
            elif ghi_chu:
                noi_dung_kq = ghi_chu
            elif du_lieu_tim:
                noi_dung_kq = str(du_lieu_tim)
    else:
        noi_dung_kq = str(du_lieu_tim or "").strip()

    return {
        "buoc": 0,
        "loai_nhanh": "db_file",
        "nhan_nhanh": "Tra cứu DB / File / Cấu trúc",
        "noi_dung": noi_dung,
        "ket_qua": noi_dung_kq or f"Đã thực hiện tra cứu DB/File cho: {noi_dung}",
        "du_lieu_truy_van": du_lieu_tim,
    }


def _xu_ly_tim_kiem_mang(noi_dung: str) -> dict:
    """Dieu phoi nhanh tra cuu/tim kiem thong tin (khong suy dien du lieu chua co)."""
    logger.info("Dieu phoi nhanh tim kiem mang: %s", noi_dung)
    return {
        "buoc": 0,
        "loai_nhanh": "tim_kiem_mang",
        "nhan_nhanh": "Tra cứu thông tin",
        "noi_dung": noi_dung,
        "ket_qua": (
            f"Đã nhận nhánh tra cứu: \"{noi_dung}\". Hiện chưa nối nguồn tìm kiếm ngoài/dữ liệu thực tế "
            "nên hệ thống không suy diễn thêm thông tin để tránh sai lệch."
        ),
    }


def _de_xuat_phuong_an(ma_linh_vuc: str, noi_dung: str) -> list[dict]:
    """Sinh cac phuong an sat linh vuc khi yeu cau con nhieu cach lam."""
    if ma_linh_vuc == "luong_nhan_su":
        return [
            {
                "id": "pa_luong_sp_tg",
                "tieu_de": "Phương án 1: Lương theo thời gian + Lương sản phẩm",
                "mo_ta": "Tính theo công/ca kết hợp sản lượng × đơn giá và các khoản khấu trừ.",
            },
            {
                "id": "pa_luong_khoan_kpi",
                "tieu_de": "Phương án 2: Lương khoán / bậc thang + Thưởng KPI",
                "mo_ta": "Áp dụng mức lương theo bậc/khoán và điều chỉnh theo chỉ tiêu đạt được.",
            },
        ]
    return [
        {
            "id": "pa_gon_chuan",
            "tieu_de": "Phương án 1: Triển khai bản gọn đúng trọng tâm",
            "mo_ta": f"Giải quyết trực tiếp yêu cầu '{noi_dung}' với cấu trúc rõ ràng, dễ kiểm tra.",
        },
        {
            "id": "pa_mo_rong_da_nhanh",
            "tieu_de": "Phương án 2: Thiết kế có cấu trúc mở rộng đa nhánh",
            "mo_ta": f"Tách lớp dữ liệu, logic xử lý và điểm mở rộng cho '{noi_dung}' để dễ nâng cấp sau này.",
        },
    ]


def _xu_ly_phan_tich(
    noi_dung: str,
    ma_linh_vuc: str,
    chon_phuong_an: str = "",
    lap_bang: bool = False,
) -> tuple[dict, bool, list[dict], list[dict]]:
    """Phan tich nghiep vu/mo rong; tra (ket_qua_nhanh, can_chon, danh_sach_phuong_an, dau_muc_giai_doan)."""
    if chon_phuong_an:
        dau_muc = [
            {"ma": "DM-01", "ten": f"Chuẩn hóa dữ liệu & quy tắc cho '{noi_dung}' ({chon_phuong_an})", "trang_thai": "Chờ chạy"},
            {"ma": "DM-02", "ten": f"Thực thi logic xử lý & kiểm thử cho '{noi_dung}'", "trang_thai": "Chờ chạy"},
        ]
        ket_qua_text = (
            _tao_bang_dau_muc_markdown(dau_muc, noi_dung)
            if lap_bang
            else f"Đã chốt '{chon_phuong_an}' và lập đầu mục giai đoạn cho: \"{noi_dung}\"."
        )
        return (
            {
                "buoc": 0,
                "loai_nhanh": "phan_tich_nghiep_vu",
                "nhan_nhanh": "Phân tích & Lập đầu mục",
                "noi_dung": noi_dung,
                "ket_qua": ket_qua_text,
            },
            False,
            [],
            dau_muc,
        )

    if ma_linh_vuc == "toan_hoc_tien_ich" and len(noi_dung.split()) >= 3:
        dau_muc = [
            {"ma": "DM-01", "ten": f"Tạo giao diện & hàm tính cho '{noi_dung}'", "trang_thai": "Chờ chạy"},
            {"ma": "DM-02", "ten": "Kiểm tra đầu vào hợp lệ & hiển thị kết quả", "trang_thai": "Chờ chạy"},
        ]
        ket_qua_text = (
            _tao_bang_dau_muc_markdown(dau_muc, noi_dung)
            if lap_bang
            else f"Yêu cầu '{noi_dung}' đã đủ rõ phạm vi cơ bản để lập đầu mục thực hiện."
        )
        return (
            {
                "buoc": 0,
                "loai_nhanh": "phan_tich_nghiep_vu",
                "nhan_nhanh": "Phân tích & Lập đầu mục",
                "noi_dung": noi_dung,
                "ket_qua": ket_qua_text,
            },
            False,
            [],
            dau_muc,
        )

    ghi_chu_ollama = (
        goi_ollama_phan_tich(
            f"Gợi ý ngắn gọn 1-2 ý về cách xây dựng/chức năng chính (không lặp lại nguyên câu hỏi) cho yêu cầu: '{noi_dung}'."
        )
        or ""
    ).strip()
    phuong_an = _de_xuat_phuong_an(ma_linh_vuc, noi_dung)

    if lap_bang:
        ket_qua_chu = _tao_bang_phan_tich_markdown(noi_dung, ghi_chu_ollama, phuong_an)
    else:
        goi_y_pa = " | ".join(pa["tieu_de"] for pa in phuong_an)
        ket_qua_chu = (
            f"{ghi_chu_ollama} — Hướng đề xuất: {goi_y_pa}"
            if ghi_chu_ollama
            else f"Yêu cầu '{noi_dung}' có nhiều cách triển khai — {goi_y_pa}."
        )

    return (
        {
            "buoc": 0,
            "loai_nhanh": "phan_tich_nghiep_vu",
            "nhan_nhanh": "Phân tích phương án nghiệp vụ",
            "noi_dung": noi_dung,
            "ket_qua": ket_qua_chu,
        },
        True,
        phuong_an,
        [],
    )


def xu_ly_prompt_da_y_dinh(prompt: str, chon_phuong_an: str = "", bo_qua_cache: bool = False) -> dict:
    """Ham dieu phoi chinh: kiem tra cache cosine -> tach da y dinh -> dieu phoi tung nhanh."""
    prompt_sach = (prompt or "").strip()
    if not prompt_sach:
        return {"ok": False, "error": "Prompt trống"}

    try:
        ma_lv_chinh, ten_lv_chinh = xac_dinh_linh_vuc(prompt_sach)
        lap_bang_prompt = _muon_lap_bang(prompt_sach)
        cho_phep_cache = (
            (not chon_phuong_an)
            and (not bo_qua_cache)
            and (not lap_bang_prompt)
            and (ma_lv_chinh not in _MA_LINH_VUC_KHONG_CACHE)
        )

        if cho_phep_cache:
            da_co = tim_cau_hoi_tuong_tu(prompt_sach)
            if da_co:
                kq_cache = _gom_ket_qua_hien_thi(da_co.get("cac_nhanh", []), da_co.get("tom_tat", ""))
                ghi_nhan_luot_hoi_thoai(
                    prompt_sach,
                    da_co.get("ma_linh_vuc", ma_lv_chinh),
                    da_co.get("y_dinh", "da_y_dinh"),
                    ket_qua_hien_thi=kq_cache,
                    ten_linh_vuc=da_co.get("ten_linh_vuc", ten_lv_chinh),
                    trung_cache=True,
                )
                return {"ok": True, **da_co}

        cac_nhanh = tach_cac_nhanh_y_dinh(prompt_sach)

        ket_qua_cac_nhanh = []
        can_chon = False
        ds_phuong_an = []
        ds_dau_muc = []

        for nhanh in cac_nhanh:
            loai = nhanh["loai_nhanh"]
            lap_bang_nhanh = lap_bang_prompt or _muon_lap_bang(nhanh["noi_dung"])
            if loai == "chat":
                kq = xu_ly_nhanh_chat(nhanh["noi_dung"])
            elif loai == "db_file":
                kq = _xu_ly_db_va_file(nhanh["noi_dung"])
            elif loai == "tim_kiem_mang":
                kq = _xu_ly_tim_kiem_mang(nhanh["noi_dung"])
            else:
                kq, n_chon, p_an, d_muc = _xu_ly_phan_tich(
                    nhanh["noi_dung"],
                    nhanh["ma_linh_vuc"],
                    chon_phuong_an=chon_phuong_an,
                    lap_bang=lap_bang_nhanh,
                )
                if n_chon and not can_chon:
                    can_chon = True
                    ds_phuong_an = p_an
                if d_muc:
                    ds_dau_muc.extend(d_muc)

            kq["buoc"] = nhanh["buoc"]
            kq["ten_linh_vuc"] = nhanh["ten_linh_vuc"]
            ket_qua_cac_nhanh.append(kq)

        tom_tat_nhanh = " + ".join(dict.fromkeys(n["nhan_nhanh"] for n in ket_qua_cac_nhanh))
        tom_tat_chuoi = f"Đã tách {len(ket_qua_cac_nhanh)} nhánh ({tom_tat_nhanh}) trên ngữ cảnh {ten_lv_chinh}."
        du_lieu_tra = {
            "y_dinh": "da_y_dinh" if len(ket_qua_cac_nhanh) > 1 else ket_qua_cac_nhanh[0]["loai_nhanh"],
            "nhan_y_dinh": tom_tat_nhanh or "Điều phối đa tầng",
            "ma_linh_vuc": ma_lv_chinh,
            "ten_linh_vuc": ten_lv_chinh,
            "cac_nhanh": ket_qua_cac_nhanh,
            "can_chon": can_chon,
            "danh_sach_phuong_an": ds_phuong_an,
            "dau_muc_giai_doan": ds_dau_muc,
            "tom_tat": tom_tat_chuoi,
            "trung_cache": False,
        }

        kq_hien_thi = _gom_ket_qua_hien_thi(ket_qua_cac_nhanh, tom_tat_chuoi)
        ghi_nhan_luot_hoi_thoai(
            prompt_sach,
            ma_lv_chinh,
            du_lieu_tra["y_dinh"],
            ket_qua_hien_thi=kq_hien_thi,
            ten_linh_vuc=ten_lv_chinh,
            trung_cache=False,
        )
        if not can_chon and not lap_bang_prompt and ma_lv_chinh not in _MA_LINH_VUC_KHONG_CACHE:
            luu_lich_su_cau_hoi(prompt_sach, du_lieu_tra)

        return {"ok": True, **du_lieu_tra}
    except Exception as loi:
        logger.error("Loi xu_ly_prompt_da_y_dinh: %s", loi, exc_info=True)
        return {"ok": False, "error": f"Lỗi điều phối ý định: {loi}"}