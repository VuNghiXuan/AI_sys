# ==============================================================================
# File Path: quan_ly_du_an/goi_y_dau_muc.py
# Description: Generate categorized suggested items, refine them via user prompt, and build approved work summary.
# Linked Files: [quan_ly_du_an/models.py, quan_ly_du_an/dich_vu_dieu_phoi.py]
# Logs: Create draft suggested items by category, adjust list from prompt, and save approved summary into profile.
# ==============================================================================

from dataclasses import dataclass
from quan_ly_du_an.models import HoSoChucNang


@dataclass
class DauMucGoiY:
    """Single suggested work item before user approval."""
    ma: str
    nhom: str
    noi_dung: str
    da_chon: bool = True


def _sinh_goi_y_theo_nhom(ho_so: HoSoChucNang, nhom: str) -> list[DauMucGoiY]:
    """Generate focused draft items for one category to avoid context bloat."""
    linh_vuc = (ho_so.linh_vuc or "chung").strip().lower()
    ten = (ho_so.ten_chuc_nang or "").strip()
    nhom_chuan = (nhom or "nghiep_vu").strip().lower()

    if nhom_chuan == "du_lieu":
        if linh_vuc == "vang_bac":
            return [
                DauMucGoiY("DL1", "du_lieu", "Chuan hoa ma phieu, ma san pham, tuoi vang va trong luong (he thong vs quet)."),
                DauMucGoiY("DL2", "du_lieu", "Kiem tra dinh dang so duong va truong bat buoc truoc khi doi soat."),
            ]
        if linh_vuc == "ke_toan":
            return [
                DauMucGoiY("DL1", "du_lieu", "Chuan hoa ma chung tu, so tien ke toan, so tien thuc te va khoang chenh lech."),
                DauMucGoiY("DL2", "du_lieu", "Kiem tra trung ma chung tu va gia tri khac thuong."),
            ]
        return [
            DauMucGoiY("DL1", "du_lieu", f"Xac dinh cac truong du lieu dau vao/dau ra cho: {ten}."),
            DauMucGoiY("DL2", "du_lieu", "Kiem tra du lieu thieu, sai kieu hoac trung lap."),
        ]

    if nhom_chuan == "rang_buoc":
        return [
            DauMucGoiY("RB1", "rang_buoc", "Dinh nghia nguong lech/sai so chap nhan duoc va canh bao khi vuot nguong."),
            DauMucGoiY("RB2", "rang_buoc", "Xu ly ro trang thai loi/ngoai le de khong ghi de du lieu goc."),
        ]

    # Default: nhom == "nghiep_vu"
    if linh_vuc == "vang_bac":
        return [
            DauMucGoiY("NV1", "nghiep_vu", f"Thuc hien luong {ten} va doi soat ket qua thuc te voi so lieu he thong."),
            DauMucGoiY("NV2", "nghiep_vu", "Phan loai ro cac muc khop, lech trong luong/tuoi vang hoac trung ma."),
        ]
    if linh_vuc == "ke_toan":
        return [
            DauMucGoiY("NV1", "nghiep_vu", f"Thuc hien luong {ten} va tinh chenh lech giua cac nguon so lieu."),
            DauMucGoiY("NV2", "nghiep_vu", "Tong hop trang thai doi soat de de dang kiem tra va duyet."),
        ]
    return [
        DauMucGoiY("NV1", "nghiep_vu", f"Thuc hien luong xu ly cot loi cho: {ten}."),
        DauMucGoiY("NV2", "nghiep_vu", "Tra ve ket qua kiem tra va danh dau cac diem can luu y."),
    ]


def lap_danh_sach_goi_y(
    ho_so: HoSoChucNang,
    nhom: str = "nghiep_vu",
    prompt_dieu_chinh: str = "",
    goi_y_hien_tai: list[dict] | None = None,
    ham_goi_llm: object | None = None,
) -> list[dict]:
    """
    Create or refine suggested items for a selected category using an optional adjustment prompt.
    Returns list of dicts with keys: ma, nhom, noi_dung, da_chon.
    """
    if goi_y_hien_tai:
        danh_sach = [
            DauMucGoiY(
                ma=str(item.get("ma") or f"M{idx + 1}"),
                nhom=str(item.get("nhom") or nhom),
                noi_dung=str(item.get("noi_dung") or "").strip(),
                da_chon=bool(item.get("da_chon", True)),
            )
            for idx, item in enumerate(goi_y_hien_tai)
            if str(item.get("noi_dung") or "").strip()
        ]
    else:
        danh_sach = _sinh_goi_y_theo_nhom(ho_so, nhom)

    prompt_sach = (prompt_dieu_chinh or "").strip()
    if prompt_sach:
        # Optional local LLM hook if caller provides callable(prompt) -> str
        if callable(ham_goi_llm):
            goi_y_llm = (
                f"Chuc nang: {ho_so.ten_chuc_nang} | Linh vuc: {ho_so.linh_vuc} | Nhom: {nhom}\n"
                f"Danh sach hien tai: {[x.noi_dung for x in danh_sach]}\n"
                f"Yeu cau dieu chinh/bo sung: {prompt_sach}\n"
                f"Hay tra ve moi dong 1 dau muc ngan gon, ro rang."
            )
            phan_hoi = str(ham_goi_llm(goi_y_llm) or "").strip()
            cac_dong = [
                dong.lstrip("-*0123456789. ").strip()
                for dong in phan_hoi.splitlines()
                if dong.lstrip("-*0123456789. ").strip()
            ]
            if cac_dong:
                nhom_chuan = (nhom or "nghiep_vu").strip().lower()
                tien_to = {"du_lieu": "DL", "rang_buoc": "RB"}.get(nhom_chuan, "NV")
                danh_sach = [
                    DauMucGoiY(ma=f"{tien_to}{i + 1}", nhom=nhom_chuan, noi_dung=nd, da_chon=True)
                    for i, nd in enumerate(cac_dong[:8])
                ]
                return [x.__dict__ for x in danh_sach]

        # Deterministic rule-based adjustment when no external LLM hook is passed
        nhom_chuan = (nhom or "nghiep_vu").strip().lower()
        tien_to = {"du_lieu": "DL", "rang_buoc": "RB"}.get(nhom_chuan, "NV")
        for cau in [c.strip() for c in prompt_sach.replace(";", "\n").splitlines() if c.strip()]:
            ma_moi = f"{tien_to}{len(danh_sach) + 1}"
            danh_sach.append(DauMucGoiY(ma=ma_moi, nhom=nhom_chuan, noi_dung=cau, da_chon=True))

    return [x.__dict__ for x in danh_sach]


def chot_dau_muc_thanh_tom_tat(danh_sach_goi_y: list[dict]) -> tuple[list[dict], list[str]]:
    """
    Filter approved items (da_chon=True) and build a clean work summary list.
    Returns (danh_sach_cap_nhat, ban_tom_tat_cong_viec).
    """
    cap_nhat: list[dict] = []
    tom_tat: list[str] = []

    for item in danh_sach_goi_y or []:
        noi_dung = str(item.get("noi_dung") or "").strip()
        if not noi_dung:
            continue
        da_chon = bool(item.get("da_chon", False))
        muc_sach = {
            "ma": str(item.get("ma") or ""),
            "nhom": str(item.get("nhom") or "nghiep_vu"),
            "noi_dung": noi_dung,
            "da_chon": da_chon,
        }
        cap_nhat.append(muc_sach)
        if da_chon:
            tom_tat.append(f"[{muc_sach['ma']}] {noi_dung}")

    return cap_nhat, tom_tat