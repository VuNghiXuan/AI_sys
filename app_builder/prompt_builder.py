# ============================================================================
# File Path: app_builder/prompt_builder.py
# Module: Tang Dung System Prompt Va Dinh Dang Ngu Canh Theo Che Do
# Linked Files: app_builder/executor.py,
#               app_builder/planner.py,
#               code_map/context_builder.py
# Purpose: Tach biet prompt cho che do chi doc/phan tich va che do tao/sua
#          tep, cung cap preset de mo rong them vai tro/agent ve sau.
# ============================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MauCheDoPrompt:
    """Dinh nghia quy tac prompt cho tung che do thuc thi."""

    ten_che_do: str
    chi_doc: bool
    huong_dan_he_thong: str
    quy_tac_ngu_canh: str


CHE_DO_DOC_PHAN_TICH = MauCheDoPrompt(
    ten_che_do="read_only_analysis",
    chi_doc=True,
    huong_dan_he_thong=(
        "Ban dang o che do CHI DOC / PHAN TICH.\n"
        "1. Chi tra loi dua tren du lieu, danh sach tep va doan ma co trong NGU CANH.\n"
        "2. TUYET DOI KHONG tao file moi, KHONG sua code tren dia, KHONG de xuat tao "
        "cac file mau nhu tep_1.py hay new_features.py khi khong duoc yeu cau.\n"
        "3. Khi liet ke ham (def), class, thuoc tinh/bien: phai phan biet ro rang "
        "dau la class, dau la ham, dau la bien/field; khong suy dien ten symbol ngoai ngu canh.\n"
        "4. Neu ngu canh chua du thong tin de ket luan chac chan, hay neu ro phan con thieu."
    ),
    quy_tac_ngu_canh=(
        "Uu tien doc ky danh sach tep dich, tep lien quan, muc luc symbol va doan trich "
        "code duoc cung cap ben duoi."
    ),
)

CHE_DO_TAO_SUA_TEP = MauCheDoPrompt(
    ten_che_do="write_code",
    chi_doc=False,
    huong_dan_he_thong=(
        "Ban dang o che do TAO / SUA TEP CODE theo ke hoach.\n"
        "1. Chi tao hoac cap nhat dung cac tep nam trong pham vi duoc phep va tuan thu "
        "gioi han so tep moi luot.\n"
        "2. Giua nguyen kien truc, quy chuan header duong dan/file lien ket va module hoa "
        "gon ro (tranh nhung nhieu logic khong lien quan).\n"
        "3. Khong tu y them thu vien hoac symbol khong co trong ngu canh neu khong can thiet."
    ),
    quy_tac_ngu_canh=(
        "Doi chieu ky signature, import va cau truc cac tep lien quan truoc khi sinh ma."
    ),
)

DANH_SACH_CHE_DO: dict[str, MauCheDoPrompt] = {
    "read_only_analysis": CHE_DO_DOC_PHAN_TICH,
    "write_code": CHE_DO_TAO_SUA_TEP,
}


def chon_che_do_prompt(ghi_ra_dia: bool, che_do_tuy_chon: str | None = None) -> MauCheDoPrompt:
    """Chon mau prompt phu hop; uu tien che do chi doc khi khong ghi ra dia."""
    if che_do_tuy_chon and che_do_tuy_chon in DANH_SACH_CHE_DO:
        mau = DANH_SACH_CHE_DO[che_do_tuy_chon]
        if not ghi_ra_dia and not mau.chi_doc:
            return CHE_DO_DOC_PHAN_TICH
        return mau
    return CHE_DO_TAO_SUA_TEP if ghi_ra_dia else CHE_DO_DOC_PHAN_TICH


def _trich_tom_tat_ngu_canh(ngu_canh: Any) -> str:
    """Chuyen doi doi tuong ngu canh thanh chuoi sach, de doc cho LLM."""
    if ngu_canh is None:
        return "(Khong co du lieu ngu canh)"

    if isinstance(ngu_canh, str):
        return ngu_canh.strip() or "(Ngu canh rong)"

    if isinstance(ngu_canh, dict):
        phan: list[str] = []
        tep_dich = ngu_canh.get("tep_dich") or []
        tep_lien_quan = ngu_canh.get("tep_lien_quan") or []
        if tep_dich:
            phan.append("Tep dich:\n" + "\n".join(f"- {t}" for t in tep_dich))
        if tep_lien_quan:
            phan.append("Tep lien quan:\n" + "\n".join(f"- {t}" for t in tep_lien_quan))
        for khoa in ("ban_do_symbol", "tom_tat_cau_truc", "trich_doan_code", "noi_dung"):
            gia_tri = ngu_canh.get(khoa)
            if gia_tri:
                phan.append(f"[{khoa}]\n{gia_tri}")
        return "\n\n".join(phan) if phan else str(ngu_canh)

    phan_obj: list[str] = []
    tep_dich = getattr(ngu_canh, "tep_dich", None) or []
    tep_lien_quan = getattr(ngu_canh, "tep_lien_quan", None) or []
    if tep_dich:
        phan_obj.append("Tep dich:\n" + "\n".join(f"- {t}" for t in tep_dich))
    if tep_lien_quan:
        phan_obj.append("Tep lien quan:\n" + "\n".join(f"- {t}" for t in tep_lien_quan))

    for thuoc_tinh in ("ban_do_symbol", "ban_do_rut_gon", "trich_doan_code", "noi_dung_ngu_canh"):
        gia_tri = getattr(ngu_canh, thuoc_tinh, None)
        if gia_tri:
            phan_obj.append(f"[{thuoc_tinh}]\n{gia_tri}")

    return "\n\n".join(phan_obj) if phan_obj else str(ngu_canh)


def xay_dung_system_prompt(
    ghi_ra_dia: bool,
    che_do_tuy_chon: str | None = None,
    bo_sung_quy_tac: str = "",
) -> str:
    """Tao system prompt hoan chinh theo che do hien hanh."""
    mau = chon_che_do_prompt(ghi_ra_dia=ghi_ra_dia, che_do_tuy_chon=che_do_tuy_chon)
    dong = [
        f"Che do hien tai: {mau.ten_che_do}",
        mau.huong_dan_he_thong,
        f"Luu y ngu canh: {mau.quy_tac_ngu_canh}",
    ]
    if bo_sung_quy_tac.strip():
        dong.append(f"Quy tac bo sung:\n{bo_sung_quy_tac.strip()}")
    return "\n\n".join(dong)


def xay_dung_user_prompt(
    yeu_cau: str,
    ngu_canh: Any = None,
    ke_hoach: Any = None,
    ghi_ra_dia: bool = False,
) -> str:
    """Gop yeu cau nguoi dung, ke hoach (neu co) va ngu canh du an thanh prompt ro rang."""
    mau = chon_che_do_prompt(ghi_ra_dia=ghi_ra_dia)
    khoi: list[str] = [f"Yeu cau:\n{yeu_cau.strip()}"]

    if ke_hoach is not None:
        mo_ta_kh = getattr(ke_hoach, "tom_tat", None) or str(ke_hoach)
        khoi.append(f"Ke hoach:\n{mo_ta_kh}")

    ngu_canh_text = _trich_tom_tat_ngu_canh(ngu_canh)
    khoi.append(f"Ngu canh he thong:\n{ngu_canh_text}")

    if mau.chi_doc:
        khoi.append(
            "Ranh gioi thuc thi: Chi tra loi phan tich/liet ke dua tren ngu canh tren, "
            "khong tao/sua tep."
        )
    return "\n\n".join(khoi)


def dang_ky_che_do_prompt(mau: MauCheDoPrompt) -> None:
    """Cho phep mo rong them che do prompt moi (vd: audit, review, test) ve sau."""
    DANH_SACH_CHE_DO[mau.ten_che_do] = mau