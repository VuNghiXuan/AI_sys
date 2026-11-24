# ============================================================================
# File Path: dieu_phoi_y_dinh/tests/test_cau_hoi_he_thong.py
# Module: Bo Test Chuyen Biet Cho Cac Cau Hoi Ve He Thong Du An AI_Sys
# Linked Files: dieu_phoi_y_dinh/dich_vu/dieu_phoi_nhanh.py,
#               dieu_phoi_y_dinh/dich_vu/thuc_thi_nhanh/trinh_xu_ly_chung.py,
#               dieu_phoi_y_dinh/dich_vu/thuc_thi_nhanh/do_ma_nguon_ast.py,
#               dieu_phoi_y_dinh/cau_hinh/cau_hinh_y_dinh.json
# Purpose: Kiem thu dinh tuyen, toc do phan hoi va do chinh xac tra loi khi
#          do DB, telemetry, vi tri file, vi tri ham/bien AST va lien ket code.
# ============================================================================

import inspect
import os
from pathlib import Path
import re
import sys
import time
from typing import Any

GOC_DU_AN = Path(__file__).resolve().parents[2]
if str(GOC_DU_AN) not in sys.path:
    sys.path.insert(0, str(GOC_DU_AN))


def _lay_settings_module_tu_manage(goc: Path) -> str:
    """Doc DJANGO_SETTINGS_MODULE tu manage.py de tranh lech ten package."""
    tep_manage = goc / "manage.py"
    if tep_manage.is_file():
        noi_dung = tep_manage.read_text(encoding="utf-8", errors="replace")
        khop = re.search(r"""DJANGO_SETTINGS_MODULE['"]\s*,\s*['"]([^'"]+)['"]""", noi_dung)
        if khop:
            return khop.group(1).strip()
    return "settings"


os.environ.setdefault("DJANGO_SETTINGS_MODULE", _lay_settings_module_tu_manage(GOC_DU_AN))

import django  # noqa: E402

django.setup()

from dieu_phoi_y_dinh.dich_vu.dieu_phoi_nhanh import xu_ly_prompt_da_y_dinh  # noqa: E402

KHOA_NOI_DUNG_UU_TIEN = (
    "noi_dung",
    "ket_qua_hien_thi",
    "tra_loi",
    "ket_qua",
    "phan_hoi",
    "hien_thi",
    "text",
    "message",
    "content",
)

# (nhom, cau_hoi, tap_y_dinh_chap_nhan, tu_khoa_bat_buoc_trong_ket_qua)
TEST_HE_THONG: list[tuple[str, str, set[str], list[str]]] = [
    # --- 1. DB / Model / Thong ke ---
    ("DB", "kể tên các app và model trong database hiện tại", {"liet_ke_app_va_model"}, ["Model", "App"]),
    ("DB", "thống kê số lượng bản ghi trong database", {"thong_ke_du_lieu_db"}, ["LichSuDieuPhoi", "CauHinhMay"]),
    ("DB", "so sánh các app trong hệ thống", {"liet_ke_app_va_model", "thong_ke_du_lieu_db", "hoi_dap_he_thong_chi_tiet"}, ["app"]),
    ("DB", "bảng nào trong db đang có dữ liệu", {"thong_ke_du_lieu_db"}, ["db"]),
    ("DB", "cấu trúc bảng db và các trường model hiện có", {"liet_ke_app_va_model"}, ["id"]),

    # --- 2. Telemetry / Phan cung / Model Ollama ---
    ("TELEMETRY", "máy đang chạy model nào và cấu hình phần cứng ra sao", {"tra_cuu_telemetry_va_model"}, ["CPU", "RAM", "Ollama"]),
    ("TELEMETRY", "kiểm tra thông số cpu ram gpu và model ollama", {"tra_cuu_telemetry_va_model"}, ["RAM"]),
    ("TELEMETRY", "cau hinh may va model ollama dang chay", {"tra_cuu_telemetry_va_model"}, ["Ollama"]),

    # --- 3. Vi tri file & cau hinh ---
    ("FILE_LOC", "file setting nằm ở đâu", {"hoi_dap_he_thong_chi_tiet"}, ["settings.py"]),
    ("FILE_LOC", "file setting nam o dau trong du an", {"hoi_dap_he_thong_chi_tiet"}, ["settings.py"]),
    ("FILE_LOC", "file trinh_xu_ly_chung.py nằm ở đâu", {"hoi_dap_he_thong_chi_tiet"}, ["trinh_xu_ly_chung.py"]),
    ("FILE_LOC", "file cau_hinh_y_dinh.json ở thư mục nào", {"hoi_dap_he_thong_chi_tiet"}, ["cau_hinh_y_dinh.json"]),
    ("FILE_LOC", "file do_ma_nguon_ast.py ở đâu", {"hoi_dap_he_thong_chi_tiet"}, ["do_ma_nguon_ast.py"]),
    ("FILE_LIST", "hệ thống có file gì", {"hoi_dap_he_thong_chi_tiet"}, ["dieu_phoi_y_dinh"]),

    # --- 4. Vi tri ham / class / bien (AST) ---
    ("SYM_LOC", "hàm xu_ly_prompt_da_y_dinh nằm ở file nào", {"hoi_dap_he_thong_chi_tiet", "viet_code_va_phan_tich"}, ["xu_ly_prompt_da_y_dinh"]),
    ("SYM_LOC", "hàm thuc_thi_theo_che_do ở file nào", {"hoi_dap_he_thong_chi_tiet", "viet_code_va_phan_tich"}, ["thuc_thi_theo_che_do"]),
    ("SYM_LOC", "class ThongTinYDinhThucThi định nghĩa ở đâu", {"hoi_dap_he_thong_chi_tiet", "viet_code_va_phan_tich"}, ["ThongTinYDinhThucThi"]),
    ("SYM_LOC", "hàm truy_van_db_django nằm ở đâu", {"hoi_dap_he_thong_chi_tiet", "viet_code_va_phan_tich"}, ["truy_van_db_django"]),
    ("SYM_LIST", "liệt kê các hàm và biến trong dự án này", {"viet_code_va_phan_tich", "hoi_dap_he_thong_chi_tiet"}, ["xu_ly_prompt_da_y_dinh"]),

    # --- 5. Lien ket file & ham + mo rong + huong dan ---
    ("LINK", "file trinh_xu_ly_chung.py liên kết với file nào", {"hoi_dap_he_thong_chi_tiet"}, ["truy_van_db_va_ast.py"]),
    ("LINK", "hàm xu_ly_prompt_da_y_dinh liên kết với hàm nào", {"hoi_dap_he_thong_chi_tiet", "viet_code_va_phan_tich"}, ["xu_ly_prompt_da_y_dinh"]),
    ("LINK", "file do_ma_nguon_ast.py phụ thuộc file nào", {"hoi_dap_he_thong_chi_tiet"}, ["truy_van_db_va_ast.py"]),
    ("EXTEND", "tao muốn thêm ý định thì thêm vào đâu", {"hoi_dap_he_thong_chi_tiet"}, ["cau_hinh_y_dinh.json"]),
    ("GUIDE", "hướng dẫn tao cách sử dụng hệ thống", {"huong_dan_su_dung_nhanh"}, ["Cách dùng nhanh"]),
]


def _trich_noi_dung_tu_kq(kq: dict[str, Any]) -> str:
    """Lay chuoi noi dung tra ve tu dictionary ket qua (ho tro ca danh_sach_y_dinh)."""
    for khoa in KHOA_NOI_DUNG_UU_TIEN:
        val = kq.get(khoa)
        if isinstance(val, str) and val.strip():
            return val

    ds_yd = kq.get("danh_sach_y_dinh")
    if isinstance(ds_yd, list):
        phan_noi_dung: list[str] = []
        for muc in ds_yd:
            if not isinstance(muc, dict):
                continue
            for k in ("noi_dung", "ket_qua", "tra_loi", "ket_qua_hien_thi", "tom_tat"):
                v = muc.get(k)
                if isinstance(v, str) and v.strip():
                    phan_noi_dung.append(v.strip())
                    break
        if phan_noi_dung:
            return "\n".join(phan_noi_dung)

    tom_tat = kq.get("tom_tat")
    return tom_tat.strip() if isinstance(tom_tat, str) else ""

def _goi_dieu_phoi(cau_hoi: str, ma_phien: str) -> dict[str, Any]:
    """Goi xu_ly_prompt_da_y_dinh tuong thich chu ky ham hien tai."""
    sig = inspect.signature(xu_ly_prompt_da_y_dinh)
    kwargs: dict[str, Any] = {}
    for ten_tham_so in ("ma_phien", "session_id", "phien_id", "ma_hoi_thoai"):
        if ten_tham_so in sig.parameters:
            kwargs[ten_tham_so] = ma_phien
            break
    ket_qua = xu_ly_prompt_da_y_dinh(cau_hoi, **kwargs)
    return ket_qua if isinstance(ket_qua, dict) else {"noi_dung": str(ket_qua or "")}


def chay_test_he_thong() -> None:
    """Chay bo test cac cau hoi ve he thong va in bao cao dat/rot theo nhom."""
    tong_dat = 0
    tong_thoi_gian = 0.0
    ma_phien = f"test_he_thong_{int(time.time())}"
    rot_theo_nhom: dict[str, list[str]] = {}

    print("=== TEST CAU HOI VE HE THONG DU AN ===")
    for idx, (nhom, cau_hoi, yd_hop_le, tu_khoa_can) in enumerate(TEST_HE_THONG, start=1):
        t0 = time.perf_counter()
        kq = _goi_dieu_phoi(cau_hoi, ma_phien=ma_phien)
        dt = time.perf_counter() - t0
        tong_thoi_gian += dt

        yd_nhan = str(kq.get("y_dinh") or kq.get("ma_y_dinh") or "")
        noi_dung = _trich_noi_dung_tu_kq(kq)
        khop_yd = yd_nhan in yd_hop_le
        khop_nd = all(tk.lower() in noi_dung.lower() for tk in tu_khoa_can)
        dat = khop_yd and khop_nd
        if dat:
            tong_dat += 1
        else:
            rot_theo_nhom.setdefault(nhom, []).append(cau_hoi)

        trang_thai = "PASS" if dat else "FAIL"
        print(
            f"[{trang_thai}] #{idx:02d} [{nhom}] ({dt:5.2f}s) '{cau_hoi}' "
            f"-> yd={yd_nhan} (mong={sorted(yd_hop_le)}) | khop_nd={khop_nd}"
        )
        if not dat:
            trich = noi_dung[:180].replace("\n", " ").replace("\r", " ")
            print(f"       Keys={list(kq.keys())} | Trich noi dung: {trich}")

    tb = tong_thoi_gian / max(1, len(TEST_HE_THONG))
    print(
        f"\nTong ket: {tong_dat}/{len(TEST_HE_THONG)} dat | "
        f"Tong thoi gian: {tong_thoi_gian:.2f}s | TB: {tb:.2f}s/cau"
    )
    if rot_theo_nhom:
        print("Cac nhom co cau rot:")
        for nhom, ds_cau in rot_theo_nhom.items():
            print(f"  - {nhom} ({len(ds_cau)} cau): {ds_cau}")


if __name__ == "__main__":
    chay_test_he_thong()