# ============================================================================
# File Path: dieu_phoi_y_dinh/tests/test_hoi_lo_mo_nguoi_that.py
# Module: Bo Test Hoi Lo Mo, Thieu Dau Va Noi Ngu Canh Nhu Nguoi That
# Linked Files: dieu_phoi_y_dinh/dich_vu/dieu_phoi_nhanh.py,
#               dieu_phoi_y_dinh/dich_vu/bo_nho_va_cache.py,
#               dieu_phoi_y_dinh/cau_hinh_y_dinh.json
# Purpose: Kiem thu kha nang dieu phoi, nho ngu canh va toc do khi nguoi dung
#          nhap cau hoi thieu dau, mo ho hoac noi tiep kieu doi thoai that.
# ============================================================================

from dataclasses import dataclass
import logging
import os
from pathlib import Path
import sys
import time
from typing import Any

GOC_DU_AN = Path(__file__).resolve().parents[2]
if str(GOC_DU_AN) not in sys.path:
    sys.path.insert(0, str(GOC_DU_AN))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "he_thong.settings")

import django

django.setup()

from dieu_phoi_y_dinh.dich_vu.dieu_phoi_nhanh import xu_ly_prompt_da_y_dinh

logging.basicConfig(level=logging.WARNING, format="%(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CaLoMo:
    """Mot ca hoi lo mo hoac thieu dau kieu nguoi dung thuc te."""

    cau_hoi: str
    y_dinh_hop_le: tuple[str, ...]
    cam_chua: tuple[str, ...] = ()
    bat_buoc_chua: tuple[str, ...] = ()
    ghi_chu: str = ""


NHOM_THIEU_DAU_GO_NHANH: tuple[CaLoMo, ...] = (
    CaLoMo("co may bang trong db vay", ("liet_ke_app_va_model", "thong_ke_du_lieu_db"), ghi_chu="thieu dau hoi db"),
    CaLoMo("xem bao nhieu dong du lieu moi bang", ("thong_ke_du_lieu_db",), ghi_chu="hoi so dong thieu dau"),
    CaLoMo("may dang chay con model nao", ("tra_cuu_telemetry_va_model",), ghi_chu="hoi model dang chay lo mo"),
    CaLoMo("ram cpu con trong bao nhieu", ("tra_cuu_telemetry_va_model",), ghi_chu="hoi tai nguyen lo mo"),
    CaLoMo("ngoai troi dang mua hay nang nhi", ("tra_cuu_mang_va_thoi_su",), ghi_chu="hoi thoi tiet kieu tam chuyen"),
    CaLoMo("gia vang hom nay sao roi", ("tra_cuu_mang_va_thoi_su",), ghi_chu="hoi gia vang ngan gon"),
)

NHOM_MO_HO_RANH_GIOI: tuple[CaLoMo, ...] = (
    CaLoMo(
        "ủa mà hệ thống này đang có những file nào",
        ("hoi_dap_he_thong_chi_tiet", "chat_tu_do"),
        cam_chua=("Cách dùng nhanh",),
        ghi_chu="hoi file khong roi vao menu dung nhanh",
    ),
    CaLoMo(
        "mỗi app bên trong làm nhiệm vụ gì",
        ("liet_ke_app_va_model", "hoi_dap_he_thong_chi_tiet", "chat_tu_do"),
        cam_chua=("Xưởng Tạo App",),
        ghi_chu="co chu app nhung la hoi chuc nang, khong phai tao app",
    ),
    CaLoMo(
        "chắc làm cái form nhập liệu cho nhân viên",
        ("chat_tu_do", "tao_app_chuyen_trang"),
        ghi_chu="noi lo mo kieu suy nghi chua chot",
    ),
    CaLoMo(
        "nay đầu óc hơi căng thẳng quá",
        ("chat_tu_do",),
        ghi_chu="tam su doi thuong",
    ),
    CaLoMo(
        "sao chia cho 0 lại văng lỗi vậy",
        ("viet_code_va_phan_tich", "chat_tu_do"),
        ghi_chu="hoi bug code khong dung tu viet code",
    ),
)

CHUOI_DOI_THOAI_LO_MO: tuple[CaLoMo, ...] = (
    CaLoMo("ờ tao là vũ", ("chat_tu_do",), ghi_chu="gioi thieu ten kem tu dem"),
    CaLoMo("xem giùm ram với ollama đang thế nào", ("tra_cuu_telemetry_va_model",), ghi_chu="xen ke hoi telemetry"),
    CaLoMo("quên mất lúc nãy tao tên gì nhỉ", ("chat_tu_do",), ("trợ lý AI của",), ("vũ",), "hoi nho ten kieu lo mo"),
    CaLoMo("ờ", ("chat_tu_do",), ("Cách dùng nhanh",), ghi_chu="dap ngan 1 tu khong dinh nham menu"),
    CaLoMo("thế đếm giúp xem mỗi bảng có mấy dòng", ("thong_ke_du_lieu_db",), ghi_chu="noi tiep chot dem du lieu"),
)


def _danh_gia_ca(ca: CaLoMo, kq: dict[str, Any]) -> tuple[bool, str, str]:
    """Danh gia ket qua mot ca lo mo theo y dinh hop le va rang buoc noi dung."""
    yd = str(kq.get("y_dinh") or "")
    tom_tat = str(kq.get("tom_tat") or "").strip()
    if not bool(kq.get("ok")) or not tom_tat:
        return False, yd, "loi hoac tom_tat rong"
    if yd not in ca.y_dinh_hop_le:
        return False, yd, f"lech y dinh (hop le={ca.y_dinh_hop_le})"

    thap = tom_tat.lower()
    for cum in ca.bat_buoc_chua:
        if cum.lower() not in thap:
            return False, yd, f"thieu '{cum}'"
    for cam in ca.cam_chua:
        if cam.lower() in thap:
            return False, yd, f"dinh '{cam}'"
    return True, yd, "ok"


def _chay_nhom(tieu_de: str, cac_ca: tuple[CaLoMo, ...], dung_phien: bool = False) -> tuple[int, int, float]:
    """Chay mot nhom test lo mo va in chi tiet tung luot."""
    print(f"\n=== {tieu_de} ({len(cac_ca)} cau) ===")
    phien = {"ma_phien": "phien_lo_mo_nguoi_that"} if dung_phien else None
    dat = 0
    tong_tg = 0.0

    for ca in cac_ca:
        t0 = time.perf_counter()
        kq = xu_ly_prompt_da_y_dinh(ca.cau_hoi, session=phien)
        tg = time.perf_counter() - t0
        tong_tg += tg

        ok, yd, ly_do = _danh_gia_ca(ca, kq)
        if ok:
            dat += 1
        mo_ta = " ".join(str(kq.get("tom_tat") or "").split())[:85]
        print(f"[{'PASS' if ok else 'FAIL'}] ({tg:5.2f}s) '{ca.cau_hoi}' -> yd={yd} ({ly_do}) | {mo_ta}")

    return dat, len(cac_ca), tong_tg


def chay_test_lo_mo() -> None:
    """Chay toan bo bo test hoi lo mo va tong hop toc do."""
    logger.info("Bat dau bo test hoi lo mo kieu nguoi dung thuc te.")
    d1, t1, g1 = _chay_nhom("THIEU DAU & GO NHANH", NHOM_THIEU_DAU_GO_NHANH, dung_phien=False)
    d2, t2, g2 = _chay_nhom("MO HO & RANH GIOI", NHOM_MO_HO_RANH_GIOI, dung_phien=False)
    d3, t3, g3 = _chay_nhom("DOI THOAI LO MO LIEN TUC", CHUOI_DOI_THOAI_LO_MO, dung_phien=True)

    tong_dat = d1 + d2 + d3
    tong_cau = t1 + t2 + t3
    tong_tg = g1 + g2 + g3
    print("\n--- TONG KET LO MO ---")
    print(f"Thieu dau go nhanh : {d1}/{t1} ({g1:.2f}s)")
    print(f"Mo ho ranh gioi    : {d2}/{t2} ({g2:.2f}s)")
    print(f"Doi thoai lien tuc : {d3}/{t3} ({g3:.2f}s)")
    print(f"Tong ket           : {tong_dat}/{tong_cau} | Tong tg: {tong_tg:.2f}s | TB: {tong_tg / max(1, tong_cau):.2f}s/cau")


if __name__ == "__main__":
    chay_test_lo_mo()