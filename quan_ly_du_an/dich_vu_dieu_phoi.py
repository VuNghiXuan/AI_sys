# ==============================================================================
# File Path: quan_ly_du_an/dich_vu_dieu_phoi.py
# Description: Service layer to detect machine specs, clarify specs, manage tasks, and audit completion in DB.
# Linked Files: [quan_ly_du_an/models.py]
# Logs: Sync machine specs to CauHinhMay, create HoSoChucNang/CauHoiLamRo/DauMucViec, audit progress.
# ==============================================================================

import ctypes
from dataclasses import dataclass, field
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
from quan_ly_du_an.models import (
    CauHinhMay,
    CauHoiLamRo,
    DauMucViec,
    HoSoChucNang,
)


@dataclass
class KetQuaDoiChieu:
    """
    Completion audit result across all work items of a feature.
    New terms:
    - completion check (doi chieu hoan tat): kiem tra tung dau muc trong DB da xong that chua.
    - pending item (muc ton dong): dau muc chua lam xong hoac dang bi loi.
    """
    ten_chuc_nang: str
    tong_dau_muc: int
    so_muc_da_xong: int
    muc_da_xong: list[str] = field(default_factory=list)
    muc_ton_dong: list[dict] = field(default_factory=list)
    hoan_tat_toan_bo: bool = False


def _lay_tong_ram_gb() -> float:
    """Get total physical RAM in GB on Windows or POSIX systems."""
    if os.name == "nt":
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        trang_thai = MEMORYSTATUSEX()
        trang_thai.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(trang_thai)):
            return round(trang_thai.ullTotalPhys / (1024 ** 3), 2)
        return 0.0

    try:
        so_trang = os.sysconf("SC_PHYS_PAGES")
        kich_thuoc_trang = os.sysconf("SC_PAGE_SIZE")
        if so_trang > 0 and kich_thuoc_trang > 0:
            return round((so_trang * kich_thuoc_trang) / (1024 ** 3), 2)
    except (ValueError, AttributeError, OSError):
        pass
    return 0.0


def _kiem_tra_gpu_roi() -> tuple[bool, str]:
    """Check if an NVIDIA discrete GPU is available via nvidia-smi."""
    try:
        ket_qua = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if ket_qua.returncode == 0 and ket_qua.stdout.strip():
            return True, ket_qua.stdout.strip().splitlines()[0].strip()
    except (FileNotFoundError, subprocess.SubprocessError, OSError):
        pass
    return False, "khong_co_gpu_roi_hoac_chay_cpu"


def do_va_luu_cau_hinh_may(thu_muc_goc: Path | None = None) -> CauHinhMay:
    """Detect current host specs and save or update into CauHinhMay table."""
    goc = thu_muc_goc or Path(__file__).resolve().parent.parent
    so_cpu = os.cpu_count() or 1
    tong_ram = _lay_tong_ram_gb()
    trong_gb = round(shutil.disk_usage(goc).free / (1024 ** 3), 2)
    co_gpu, mo_ta_gpu = _kiem_tra_gpu_roi()

    # Keep conservative mode when running on CPU-only or modest RAM
    muc_goi_y = "tiet_kiem_cpu_ram" if (not co_gpu or tong_ram < 24) else "chuan_tien_loi"
    ten_may = platform.node() or "may_local"

    cau_hinh, _ = CauHinhMay.objects.update_or_create(
        ten_may=ten_may,
        defaults={
            "he_dieu_hanh": f"{platform.system()} {platform.release()}",
            "phien_ban_python": sys.version.split()[0],
            "so_luong_cpu": so_cpu,
            "tong_ram_gb": tong_ram,
            "dung_luong_trong_gb": trong_gb,
            "co_gpu_roi": co_gpu,
            "mo_ta_gpu": mo_ta_gpu,
            "muc_chay_goi_y": muc_goi_y,
        },
    )
    return cau_hinh


def khoi_tao_ho_so_va_lam_ro(noi_dung_yeu_cau: str, linh_vuc: str = "chung") -> HoSoChucNang:
    """
    Create or update a feature profile, auto-answer clear questions,
    save unresolved questions to CauHoiLamRo, and create initial DauMucViec rows.
    """
    noi_dung_sach = noi_dung_yeu_cau.strip()
    chu_thuong = noi_dung_sach.lower()
    ten_chuc_nang = noi_dung_sach[:120] if noi_dung_sach else "chuc_nang_moi"

    lam_cho_ai = ""
    muc_dich = ""
    if any(tu in chu_thuong for tu in ["cho ", "nguoi dung", "khach hang", "nhan vien"]):
        lam_cho_ai = f"Tu suy ra tu yeu cau: {noi_dung_sach}"
    if any(tu in chu_thuong for tu in ["de ", "nham ", "muc dich", "giup "]):
        muc_dich = f"Tu suy ra tu yeu cau: {noi_dung_sach}"

    ho_so, _ = HoSoChucNang.objects.update_or_create(
        ten_chuc_nang=ten_chuc_nang,
        defaults={
            "linh_vuc": linh_vuc,
            "lam_cho_ai": lam_cho_ai,
            "muc_dich": muc_dich,
            "cac_truong_du_lieu": ["ma_so", "trang_thai", "ket_qua", "ghi_chu"],
        },
    )

    bo_cau_hoi = [
        ("H1", "lam_cho_ai", "Chuc nang/ung dung nay lam cho ai va ai la nguoi truc tiep dung?", bool(lam_cho_ai), lam_cho_ai),
        ("H2", "muc_dich", "Muc dich chinh la gi va giai quyet thao tac/van de nao?", bool(muc_dich), muc_dich),
        ("H3", "du_lieu", "Can nhap, luu hay xuat nhung truong du lieu nao?", False, ""),
        ("H4", "rang_buoc", "Co dieu kien rang buoc, loi bien hay ket noi phan nao da co khong?", False, ""),
    ]

    con_cau_hoi_chua_ro = False
    for ma_ch, nhom, noi_dung, da_tl, tra_loi in bo_cau_hoi:
        can_hoi = not da_tl
        if can_hoi:
            con_cau_hoi_chua_ro = True
        CauHoiLamRo.objects.update_or_create(
            ho_so=ho_so,
            ma_cau_hoi=ma_ch,
            defaults={
                "nhom_hoi": nhom,
                "noi_dung_hoi": noi_dung,
                "da_tra_loi": da_tl,
                "cau_tra_loi": tra_loi,
                "can_hoi_lai": can_hoi,
            },
        )

    ho_so.da_chot_thong_tin = not con_cau_hoi_chua_ro
    ho_so.save(update_fields=["da_chot_thong_tin", "ngay_cap_nhat"])

    cac_dau_muc_mac_dinh = [
        ("M1", "Chot truong du lieu va cau truc vao/ra", "hop_dong_du_lieu.py", "tao_du_lieu_chuan"),
        ("M2", "Viet xu ly chinh theo tung buoc nho", "xu_ly_chinh.py", "chay_xu_ly"),
        ("M3", "Kiem tra ket qua va doi chieu hoan tat", "kiem_tra_ket_qua.py", "doi_chieu_hoan_tat"),
    ]
    for ma_muc, ten_viec, ten_file, ten_ham in cac_dau_muc_mac_dinh:
        DauMucViec.objects.get_or_create(
            ho_so=ho_so,
            ma_muc=ma_muc,
            defaults={
                "ten_viec": ten_viec,
                "ten_file": ten_file,
                "ten_ham": ten_ham,
                "trang_thai": "chua_lam",
            },
        )

    return ho_so


def doi_chieu_hoan_tat_theo_ho_so(ho_so: HoSoChucNang) -> KetQuaDoiChieu:
    """Audit all DauMucViec records of a feature in DB and report exact progress."""
    danh_sach_muc = list(ho_so.cac_dau_muc.order_by("ma_muc"))
    muc_da_xong: list[str] = []
    muc_ton_dong: list[dict] = []

    for muc in danh_sach_muc:
        if muc.trang_thai == "da_xong":
            muc_da_xong.append(f"{muc.ma_muc}: {muc.ten_viec}")
        else:
            muc_ton_dong.append({
                "ma_muc": muc.ma_muc,
                "ten_viec": muc.ten_viec,
                "trang_thai": muc.trang_thai,
                "ghi_chu": muc.ghi_chu or "Chua hoan tat",
            })

    tong = len(danh_sach_muc)
    da_xong = len(muc_da_xong)
    hoan_tat = (tong > 0) and (da_xong == tong) and (len(muc_ton_dong) == 0)

    return KetQuaDoiChieu(
        ten_chuc_nang=ho_so.ten_chuc_nang,
        tong_dau_muc=tong,
        so_muc_da_xong=da_xong,
        muc_da_xong=muc_da_xong,
        muc_ton_dong=muc_ton_dong,
        hoan_tat_toan_bo=hoan_tat,
    )

def luu_cau_tra_loi_lam_ro(
    ho_so: HoSoChucNang,
    cac_cau_tra_loi: dict[str, str],
) -> HoSoChucNang:
    """
    Save user answers for clarifying questions and lock feature spec when none remain.
    """
    for ma_ch, noi_dung_tl in cac_cau_tra_loi.items():
        tra_loi_sach = noi_dung_tl.strip()
        if not tra_loi_sach:
            continue
        cau_hoi = CauHoiLamRo.objects.filter(ho_so=ho_so, ma_cau_hoi=ma_ch).first()
        if not cau_hoi:
            continue

        cau_hoi.da_tra_loi = True
        cau_hoi.cau_tra_loi = tra_loi_sach
        cau_hoi.can_hoi_lai = False
        cau_hoi.save()

        # Sync key answers back onto feature fields when applicable
        if cau_hoi.nhom_hoi == "lam_cho_ai" and not ho_so.lam_cho_ai:
            ho_so.lam_cho_ai = tra_loi_sach
        elif cau_hoi.nhom_hoi == "muc_dich" and not ho_so.muc_dich:
            ho_so.muc_dich = tra_loi_sach
        elif cau_hoi.nhom_hoi == "du_lieu":
            cac_cot = [cot.strip() for cot in tra_loi_sach.split(",") if cot.strip()]
            if cac_cot:
                ho_so.cac_truong_du_lieu = cac_cot

    con_cau_hoi_can_hoi = ho_so.cac_cau_hoi.filter(can_hoi_lai=True).exists()
    ho_so.da_chot_thong_tin = not con_cau_hoi_can_hoi
    ho_so.save()
    return ho_so


def cap_nhat_trang_thai_dau_muc(
    ho_so: HoSoChucNang,
    ma_muc: str,
    trang_thai: str,
    ghi_chu: str = "",
) -> DauMucViec | None:
    """
    Update status (chua_lam, dang_lam, da_xong, loi) and optional note for one task item.
    """
    muc = ho_so.cac_dau_muc.filter(ma_muc=ma_muc).first()
    if not muc:
        return None
    muc.trang_thai = trang_thai
    if ghi_chu:
        muc.ghi_chu = ghi_chu
    muc.save()
    return muc

