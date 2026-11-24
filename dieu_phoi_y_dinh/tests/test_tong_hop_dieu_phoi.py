# ============================================================================
# File Path: dieu_phoi_y_dinh/tests/test_tong_hop_dieu_phoi.py
# Module: Bo Test Tong Hop Dieu Phoi Don, Da Y Dinh Va Hoi Thoai
# Linked Files: dieu_phoi_y_dinh/dich_vu/dieu_phoi_nhanh.py,
#               dieu_phoi_y_dinh/dich_vu/bo_nho_va_cache.py
# Purpose: Kiem thu toan dien cac ca thieu dau, mo ho, nho ten, da y dinh,
#          cache va bien ngoai le cua luong dieu phoi y dinh.
# ============================================================================

import logging
import os
from pathlib import Path
import sys
import time
from typing import Any

GOC_DU_AN = Path(__file__).resolve().parents[2]
if str(GOC_DU_AN) not in sys.path:
    sys.path.insert(0, str(GOC_DU_AN))

import django  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger(__name__)

UNG_VIEN_SETTINGS = (
    "config.settings",
    "AI_sys.settings",
    "ai_sys.settings",
    "vnxbox.settings",
    "settings",
)


def _tim_settings_module() -> str:
    """Tu dong tim module settings.py hop le trong du an."""
    if os.environ.get("DJANGO_SETTINGS_MODULE"):
        return os.environ["DJANGO_SETTINGS_MODULE"]

    for ung_vien in UNG_VIEN_SETTINGS:
        duong_dan = GOC_DU_AN / Path(*ung_vien.split(".")).with_suffix(".py")
        if duong_dan.exists():
            return ung_vien

    for tep in GOC_DU_AN.rglob("settings.py"):
        if ".venv" in tep.parts or "site-packages" in tep.parts:
            continue
        tuong_doi = tep.relative_to(GOC_DU_AN).with_suffix("")
        return ".".join(tuong_doi.parts)

    return "config.settings"


def _khoi_tao_django() -> None:
    """Khoi tao moi truong Django va nap day du app/model."""
    if not (GOC_DU_AN / "manage.py").exists():
        logger.warning("Khong tim thay manage.py tai %s", GOC_DU_AN)
    settings_mod = _tim_settings_module()
    os.environ["DJANGO_SETTINGS_MODULE"] = settings_mod
    logger.info("Khoi tao Django voi DJANGO_SETTINGS_MODULE=%s", settings_mod)
    django.setup()


def _chay_mot_ca(
    ten_ca: str,
    prompt: str,
    y_dinh_hop_le: set[str] | None = None,
    phien: str = "phien_test_tong_hop",
    bo_qua_cache: bool = True,
    yeu_cau_da_y_dinh: bool = False,
    ky_vong_that_bai: bool = False,
) -> dict[str, Any]:
    """Thuc thi mot ca kiem thu va tra ve ket qua chuan hoa."""
    from dieu_phoi_y_dinh.dich_vu.dieu_phoi_nhanh import xu_ly_prompt_da_y_dinh

    bat_dau = time.perf_counter()
    kq = xu_ly_prompt_da_y_dinh(
        prompt=prompt,
        bo_qua_cache=bo_qua_cache,
        session={"ma_phien": phien},
    )
    thoi_gian = time.perf_counter() - bat_dau

    yd = str(kq.get("y_dinh") or "")
    ds_yd = list(kq.get("danh_sach_y_dinh") or [])
    ok_flag = bool(kq.get("ok"))

    if ky_vong_that_bai:
        dat = not ok_flag
        ly_do = "ok (tra ve ok=False dung ky vong)" if dat else "loi: le ra phai tra ve ok=False"
    else:
        dat = ok_flag
        ly_do = "ok"
        if y_dinh_hop_le and yd not in y_dinh_hop_le:
            dat = False
            ly_do = f"y_dinh={yd} (hop le={sorted(y_dinh_hop_le)})"
        elif yeu_cau_da_y_dinh and len(ds_yd) < 2:
            dat = False
            ly_do = f"ky vong da y dinh nhung chi co {ds_yd}"

    tom_tat = " ".join(str(kq.get("tom_tat") or kq.get("error") or "").split())[:100]
    trang_thai = "PASS" if dat else "FAIL"
    print(f"[{trang_thai}] ({thoi_gian:5.2f}s) [{ten_ca}] '{prompt}' -> {ly_do} | {tom_tat}")
    return {"dat": dat, "thoi_gian": thoi_gian, "kq": kq}


def chay_bo_test_tong_hop() -> bool:
    """Chay tat ca cac nhom ca kiem thu va in bang tong ket."""
    _khoi_tao_django()
    logger.info("Bat dau chay bo test tong hop dieu phoi.")

    cac_nhom: list[tuple[str, list[dict[str, Any]]]] = [
        (
            "1. THIEU DAU & GO NHANH",
            [
                {"ten_ca": "dem_bang", "prompt": "co may bang trong db vay", "y_dinh_hop_le": {"thong_ke_du_lieu_db"}},
                {"ten_ca": "dem_dong_thieu_dau", "prompt": "xem bao nhieu dong du lieu moi bang", "y_dinh_hop_le": {"thong_ke_du_lieu_db"}},
                {"ten_ca": "telemetry_model", "prompt": "may dang chay con model nao", "y_dinh_hop_le": {"tra_cuu_telemetry_va_model"}},
                {"ten_ca": "telemetry_ram_cpu", "prompt": "ram cpu con trong bao nhieu", "y_dinh_hop_le": {"tra_cuu_telemetry_va_model"}},
                {"ten_ca": "thoi_tiet_khong_dau", "prompt": "ngoai troi dang mua hay nang nhi", "y_dinh_hop_le": {"tra_cuu_mang_va_thoi_su"}},
                {"ten_ca": "gia_vang_khong_dau", "prompt": "gia vang hom nay sao roi", "y_dinh_hop_le": {"tra_cuu_mang_va_thoi_su"}},
            ],
        ),
        (
            "2. MO HO, RANH GIOI & DEBUG",
            [
                {"ten_ca": "file_he_thong", "prompt": "ủa mà hệ thống này đang có những file nào", "y_dinh_hop_le": {"hoi_dap_he_thong_chi_tiet"}},
                {"ten_ca": "nhiem_vu_app", "prompt": "mỗi app bên trong làm nhiệm vụ gì", "y_dinh_hop_le": {"liet_ke_app_va_model"}},
                {"ten_ca": "y_tuong_lo_mo", "prompt": "chắc làm cái form nhập liệu cho nhân viên", "y_dinh_hop_le": {"chat_tu_do", "tao_app_chuyen_trang"}},
                {"ten_ca": "tam_su", "prompt": "nay đầu óc hơi căng thẳng quá", "y_dinh_hop_le": {"chat_tu_do"}},
                {"ten_ca": "debug_chia_0", "prompt": "sao chia cho 0 lại văng lỗi vậy", "y_dinh_hop_le": {"viet_code_va_phan_tich"}},
            ],
        ),
        (
            "3. DOI THOAI & NHO TEN CO TU DEM",
            [
                {"ten_ca": "gioi_thieu_ten", "prompt": "ờ tao là vũ", "y_dinh_hop_le": {"chat_tu_do"}, "phien": "phien_nho_ten"},
                {"ten_ca": "hoi_ram_ollama", "prompt": "xem giùm ram với ollama đang thế nào", "y_dinh_hop_le": {"tra_cuu_telemetry_va_model"}, "phien": "phien_nho_ten"},
                {"ten_ca": "nhac_lai_ten", "prompt": "quên mất lúc nãy tao tên gì nhỉ", "y_dinh_hop_le": {"chat_tu_do"}, "phien": "phien_nho_ten"},
                {"ten_ca": "phan_hoi_ngan", "prompt": "ờ", "y_dinh_hop_le": {"chat_tu_do"}, "phien": "phien_nho_ten"},
                {"ten_ca": "dem_dong_tiep_noi", "prompt": "thế đếm giúp xem mỗi bảng có mấy dòng", "y_dinh_hop_le": {"thong_ke_du_lieu_db"}, "phien": "phien_nho_ten"},
            ],
        ),
        (
            "4. PHAN TICH DA Y DINH",
            [
                {
                    "ten_ca": "telemetry_va_dem_dong",
                    "prompt": "xem ram với ollama đang thế nào rồi đếm giúp xem mỗi bảng có mấy dòng",
                    "y_dinh_hop_le": {"tra_cuu_telemetry_va_model"},
                    "phien": "phien_da_y_dinh",
                    "yeu_cau_da_y_dinh": True,
                },
                {
                    "ten_ca": "app_model_va_he_thong",
                    "prompt": "kể tên các app và model; hệ thống này có file nào",
                    "y_dinh_hop_le": {"liet_ke_app_va_model"},
                    "phien": "phien_da_y_dinh",
                    "yeu_cau_da_y_dinh": True,
                },
            ],
        ),
        (
            "5. EDGE CASE & CACHE",
            [
                {
                    "ten_ca": "prompt_rong",
                    "prompt": "   ",
                    "y_dinh_hop_le": None,
                    "phien": "phien_edge",
                    "ky_vong_that_bai": True,
                },
            ],
        ),
    ]

    tong_dat = 0
    tong_ca = 0
    tong_tg = 0.0

    for ten_nhom, ds_ca in cac_nhom:
        print(f"\n=== {ten_nhom} ({len(ds_ca)} ca) ===")
        nhom_dat = 0
        nhom_tg = 0.0
        for ca in ds_ca:
            kq = _chay_mot_ca(**ca)
            tong_ca += 1
            tong_tg += kq["thoi_gian"]
            nhom_tg += kq["thoi_gian"]
            if kq["dat"]:
                nhom_dat += 1
                tong_dat += 1
        print(f"-- Nhom '{ten_nhom}': {nhom_dat}/{len(ds_ca)} ({nhom_tg:.2f}s)")

    tb_tg = tong_tg / tong_ca if tong_ca else 0.0
    print("\n--- TONG KET TONG HOP ---")
    print(f"Tong ket : {tong_dat}/{tong_ca} | Tong tg: {tong_tg:.2f}s | TB: {tb_tg:.2f}s/cau")
    return tong_dat == tong_ca


if __name__ == "__main__":
    sys.exit(0 if chay_bo_test_tong_hop() else 1)