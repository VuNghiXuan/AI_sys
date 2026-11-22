# ==============================================================================
# File Path: quan_ly_du_an/tu_dong_lam_ro.py
# Description: Auto-generate clarification questions, self-answer inferable items, and escalate hard ones.
# Linked Files: [quan_ly_du_an/models.py, quan_ly_du_an/dich_vu_dieu_phoi.py]
# Logs: Infer answers from context/LLM, update CauHoiLamRo, sync cac_truong_du_lieu and da_chot_thong_tin.
# ==============================================================================

from dataclasses import dataclass
import re
from quan_ly_du_an.dich_vu_dieu_phoi import khoi_tao_ho_so_va_lam_ro
from quan_ly_du_an.models import HoSoChucNang


@dataclass
class KetQuaTuLamRo:
    """
    Summary after AI generates questions, self-answers inferable ones, and leaves hard ones for user.
    New terms:
    - self-clarification (tu lam ro): AI tu suy luan va dien dap an cho cac cau hoi du co so.
    - escalation gate (nguong hoi lai): chi giu lai cau hoi can_hoi_lai=True khi thieu co so chac chan.
    """
    ho_so_id: int
    da_tu_tra_loi: list[str]
    con_hoi_nguoi_dung: list[dict]
    da_chot_thong_tin: bool


def _trich_xuat_truong_du_lieu(noi_dung: str) -> list[str]:
    """Extract clean field names from a clarification answer."""
    cac_tu = re.findall(r"[a-zA-Z_][a-zA-Z0-9_]{1,40}", noi_dung or "")
    ket_qua: list[str] = []
    for tu in cac_tu:
        tu_sach = tu.strip("_").lower()
        if len(tu_sach) >= 2 and tu_sach not in ket_qua:
            ket_qua.append(tu_sach)
    return ket_qua[:12]


def _suy_luan_dap_an_theo_ngu_canh(ho_so: HoSoChucNang, ma_cau_hoi: str) -> tuple[str | None, bool]:
    """
    Infer answer from profile context and domain.
    Returns (answer_text, du_tin_cay_de_tu_chot).
    If du_tin_cay_de_tu_chot is False, AI leaves can_hoi_lai=True to ask the user.
    """
    ten = (ho_so.ten_chuc_nang or "").strip()
    linh_vuc = (ho_so.linh_vuc or "chung").strip().lower()
    ten_lower = ten.lower()

    if ma_cau_hoi == "H1":
        if "kho" in ten_lower:
            return "Nhan vien kho va quan ly kho", True
        if "ke toan" in ten_lower:
            return "Nhan vien ke toan va ke toan truong", True
        return "Nguoi dung nghiep vu truc tiep su dung chuc nang", True

    if ma_cau_hoi == "H2":
        if linh_vuc == "vang_bac" or "quet" in ten_lower or "kiem ke" in ten_lower:
            return (
                f"Thuc hien nghiep vu ({ten}), doi soat so lieu thuc te voi he thong "
                f"de phat hien lech, trung ma hoac sai sot som."
            ), True
        if linh_vuc == "ke_toan" or "doi soat" in ten_lower:
            return (
                f"Thuc hien ({ten}), doi soat so lieu giua cac nguon de phat hien "
                f"chenh lech va ghi nhan trang thai ro rang."
            ), True
        return f"Ho tro thuc hien va kiem soat ket qua cho chuc nang: {ten}", True

    if ma_cau_hoi == "H3":
        if linh_vuc == "vang_bac":
            return (
                "ma_phieu_kiem_ke, ma_san_pham, tuoi_vang, "
                "trong_luong_he_thong, trong_luong_quet, trang_thai_lech"
            ), True
        if linh_vuc == "ke_toan":
            return "ma_phieu, so_tien_ke_toan, so_tien_thuc_te, chenh_lech, trang_thai", True
        return None, False

    if ma_cau_hoi == "H4":
        return None, False

    return None, False


def tu_dong_sinh_va_tra_loi_lam_ro(
    ho_so: HoSoChucNang,
    ham_goi_llm: object | None = None,
) -> KetQuaTuLamRo:
    """
    Generate missing clarification questions if needed, self-answer inferable ones,
    and keep can_hoi_lai=True only for items that still need user decision.
    """
    if not ho_so.cac_cau_hoi.exists():
        khoi_tao_ho_so_va_lam_ro(ho_so.ten_chuc_nang, linh_vuc=ho_so.linh_vuc)
        ho_so.refresh_from_db()

    da_tu_tra_loi: list[str] = []
    truong_moi: list[str] = list(ho_so.cac_truong_du_lieu or [])

    for cau_hoi in ho_so.cac_cau_hoi.order_by("ma_cau_hoi"):
        if cau_hoi.da_tra_loi and not cau_hoi.can_hoi_lai:
            continue

        dap_an: str | None = None
        tu_chot = False

        if callable(ham_goi_llm):
            goi_y_llm = (
                f"Chuc nang: {ho_so.ten_chuc_nang} | Linh vuc: {ho_so.linh_vuc}\n"
                f"Cau hoi ({cau_hoi.ma_cau_hoi}): {cau_hoi.noi_dung_hoi}\n"
                f"Neu chua du co so chac chan (nguong lech, quy dinh rieng, ket noi ngoai), "
                f"hay tra loi dung 1 tu: CAN_HOI_LAI"
            )
            phan_hoi = str(ham_goi_llm(goi_y_llm) or "").strip()
            if phan_hoi and "CAN_HOI_LAI" not in phan_hoi.upper():
                dap_an = phan_hoi
                tu_chot = True

        if not dap_an:
            dap_an, tu_chot = _suy_luan_dap_an_theo_ngu_canh(ho_so, cau_hoi.ma_cau_hoi)

        if dap_an and tu_chot:
            cau_hoi.cau_tra_loi = dap_an
            cau_hoi.da_tra_loi = True
            cau_hoi.can_hoi_lai = False
            cau_hoi.save(update_fields=["cau_tra_loi", "da_tra_loi", "can_hoi_lai"])
            da_tu_tra_loi.append(cau_hoi.ma_cau_hoi)

            if cau_hoi.ma_cau_hoi == "H3":
                for tr in _trich_xuat_truong_du_lieu(dap_an):
                    if tr not in truong_moi:
                        truong_moi.append(tr)
        else:
            cau_hoi.can_hoi_lai = True
            cau_hoi.save(update_fields=["can_hoi_lai"])

    if truong_moi != (ho_so.cac_truong_du_lieu or []):
        ho_so.cac_truong_du_lieu = truong_moi
        ho_so.save(update_fields=["cac_truong_du_lieu", "ngay_cap_nhat"])

    con_hoi = [
        {"ma_cau_hoi": ch.ma_cau_hoi, "noi_dung_hoi": ch.noi_dung_hoi}
        for ch in ho_so.cac_cau_hoi.filter(can_hoi_lai=True).order_by("ma_cau_hoi")
    ]
    da_chot = len(con_hoi) == 0
    if ho_so.da_chot_thong_tin != da_chot:
        ho_so.da_chot_thong_tin = da_chot
        ho_so.save(update_fields=["da_chot_thong_tin", "ngay_cap_nhat"])

    return KetQuaTuLamRo(
        ho_so_id=ho_so.id,
        da_tu_tra_loi=da_tu_tra_loi,
        con_hoi_nguoi_dung=con_hoi,
        da_chot_thong_tin=da_chot,
    )