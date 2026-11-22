# ==============================================================================
# File Path: quan_ly_du_an/phan_luong_y_dinh.py
# Description: Multi-layer intent router across mode, work area, and DB records.
# Linked Files: [quan_ly_du_an/models.py, quan_ly_du_an/dich_vu_dieu_phoi.py]
# Logs: Detect execution mode, match work area, query matching feature/questions/tasks in DB.
# ==============================================================================

from dataclasses import dataclass, field
from quan_ly_du_an.models import HoSoChucNang


@dataclass
class KetQuaPhanLuong:
    """
    Routing decision across mode, work area, and matching DB records.
    New terms:
    - multi-layer intent (y dinh da tang): chia viec nhan dien y dinh thanh tung tang tu rong toi cu the.
    - work area (linh vuc): nhom viec hoac nghiep vu de loc du lieu dung pham vi trong DB.
    """
    cau_goc: str
    che_do: str
    linh_vuc: str
    ho_so_khop: list[str] = field(default_factory=list)
    cau_hoi_chua_ro: list[dict] = field(default_factory=list)
    dau_muc_ton_dong: list[dict] = field(default_factory=list)
    buoc_goi_y: str = ""


TU_KHOA_LINH_VUC = {
    "ke_toan": ["doi soat", "phieu", "so tien", "chenh lech", "hoa don", "cong no", "ke toan"],
    "vang_bac": ["tuoi vang", "quy doi", "trong luong", "don gia", "doi tra", "trang suc", "vang"],
    "kiem_thu": ["test case", "kiem thu", "loi", "bug", "retest", "ca kiem thu"],
}

TU_KHOA_TAO_MOI = ["tao ", "lam ", "them ", "viet ", "xay dung", "sinh "]
TU_KHOA_TRO_CHUYEN = ["chao", "hello", "hi", "khoe khong", "cam on", "oke", "ok"]


def _xac_dinh_che_do(cau_thuong: str) -> str:
    """Classify request into mode: tao_chuc_nang, hoi_dap_nghiep_vu, or tro_chuyen_nhe."""
    if any(tu in cau_thuong for tu in TU_KHOA_TAO_MOI):
        return "tao_chuc_nang"
    if cau_thuong.strip() in TU_KHOA_TRO_CHUYEN or len(cau_thuong.split()) <= 2:
        if any(tu in cau_thuong for tu in TU_KHOA_TRO_CHUYEN):
            return "tro_chuyen_nhe"
    return "hoi_dap_nghiep_vu"


def _xac_dinh_linh_vuc(cau_thuong: str) -> str:
    """Match work area from keywords; fall back to 'chung' if no specific match."""
    for ma_linh_vuc, ds_tu in TU_KHOA_LINH_VUC.items():
        if any(tu in cau_thuong for tu in ds_tu):
            return ma_linh_vuc
    return "chung"


def phan_luong_da_tang(noi_dung_yeu_cau: str) -> KetQuaPhanLuong:
    """
    Route a user prompt through 3 layers: mode -> work area -> matching DB records.
    """
    cau_sach = noi_dung_yeu_cau.strip()
    cau_thuong = cau_sach.lower()

    che_do = _xac_dinh_che_do(cau_thuong)
    linh_vuc = _xac_dinh_linh_vuc(cau_thuong)

    # Layer 3: Query matching feature profiles in DB by work area or keyword overlap
    ds_ho_so = list(HoSoChucNang.objects.filter(linh_vuc=linh_vuc).order_by("-ngay_cap_nhat"))
    if not ds_ho_so and linh_vuc != "chung":
        ds_ho_so = list(HoSoChucNang.objects.filter(linh_vuc="chung").order_by("-ngay_cap_nhat"))

    ho_so_khop_ten: list[str] = []
    cau_hoi_chua_ro: list[dict] = []
    dau_muc_ton_dong: list[dict] = []

    for hs in ds_ho_so:
        # Match if feature name shares words with prompt or is the latest active profile in area
        tu_khoa_hs = [w for w in hs.ten_chuc_nang.lower().split() if len(w) >= 4]
        if any(w in cau_thuong for w in tu_khoa_hs) or len(ho_so_khop_ten) == 0:
            ho_so_khop_ten.append(hs.ten_chuc_nang)

            for ch in hs.cac_cau_hoi.filter(can_hoi_lai=True).order_by("ma_cau_hoi"):
                cau_hoi_chua_ro.append({
                    "ho_so": hs.ten_chuc_nang,
                    "ma_cau_hoi": ch.ma_cau_hoi,
                    "noi_dung_hoi": ch.noi_dung_hoi,
                })

            for muc in hs.cac_dau_muc.exclude(trang_thai="da_xong").order_by("ma_muc"):
                dau_muc_ton_dong.append({
                    "ho_so": hs.ten_chuc_nang,
                    "ma_muc": muc.ma_muc,
                    "ten_viec": muc.ten_viec,
                    "trang_thai": muc.trang_thai,
                })
            break

    if cau_hoi_chua_ro:
        buoc_goi_y = "Hoi lam ro cac cau hoi con thieu truoc khi chot lam."
    elif dau_muc_ton_dong:
        muc_ke_tiep = dau_muc_ton_dong[0]
        buoc_goi_y = f"Lam tiep dau muc {muc_ke_tiep['ma_muc']}: {muc_ke_tiep['ten_viec']}."
    else:
        buoc_goi_y = "Khoi tao ho so chuc nang moi hoac kiem tra lai ket qua."

    return KetQuaPhanLuong(
        cau_goc=cau_sach,
        che_do=che_do,
        linh_vuc=linh_vuc,
        ho_so_khop=ho_so_khop_ten,
        cau_hoi_chua_ro=cau_hoi_chua_ro,
        dau_muc_ton_dong=dau_muc_ton_dong,
        buoc_goi_y=buoc_goi_y,
    )