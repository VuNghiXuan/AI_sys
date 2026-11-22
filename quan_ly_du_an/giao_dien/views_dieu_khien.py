# ==============================================================================
# File Path: quan_ly_du_an/giao_dien/views_dieu_khien.py
# Description: Render UI workbench and handle profile, clarification, suggested items, and M1-M3 runs.
# Linked Files: [quan_ly_du_an/models.py, quan_ly_du_an/dich_vu_dieu_phoi.py, quan_ly_du_an/tu_dong_lam_ro.py, quan_ly_du_an/goi_y_dau_muc.py, quan_ly_du_an/thuc_thi_dau_muc.py]
# Logs: Support categorized AI item suggestions, adjustment prompt, checkbox selection, and work summary approval.
# ==============================================================================

from django.shortcuts import get_object_or_404, redirect, render
from quan_ly_du_an.dich_vu_dieu_phoi import (
    doi_chieu_hoan_tat_theo_ho_so,
    khoi_tao_ho_so_va_lam_ro,
    luu_cau_tra_loi_lam_ro,
)
from quan_ly_du_an.goi_y_dau_muc import chot_dau_muc_thanh_tom_tat, lap_danh_sach_goi_y
from quan_ly_du_an.models import HoSoChucNang
from quan_ly_du_an.thuc_thi_dau_muc import hoan_thien_va_chay_lai_test, thuc_thi_mot_dau_muc
from quan_ly_du_an.tu_dong_lam_ro import tu_dong_sinh_va_tra_loi_lam_ro


def trang_dieu_khien(request, ho_so_id: int | None = None):
    """Render main UI workbench and process form actions for testing."""
    danh_sach_ho_so = list(HoSoChucNang.objects.order_by("-id"))
    ho_so_hien_tai = None

    if ho_so_id is not None:
        ho_so_hien_tai = get_object_or_404(HoSoChucNang, id=ho_so_id)
    elif danh_sach_ho_so:
        ho_so_hien_tai = danh_sach_ho_so[0]

    thong_bao_log = ""
    nhom_hien_tai = "nghiep_vu"
    danh_sach_goi_y: list[dict] = []
    ban_tom_tat: list[str] = []

    if ho_so_hien_tai:
        session_goi_y = request.session.get("goi_y_theo_ho_so", {})
        session_tom_tat = request.session.get("tom_tat_theo_ho_so", {})
        key_hs = str(ho_so_hien_tai.id)

        danh_sach_goi_y = session_goi_y.get(key_hs) or lap_danh_sach_goi_y(ho_so_hien_tai, nhom="nghiep_vu")
        ban_tom_tat = session_tom_tat.get(key_hs) or []
        if danh_sach_goi_y and danh_sach_goi_y[0].get("nhom"):
            nhom_hien_tai = str(danh_sach_goi_y[0].get("nhom"))

    if request.method == "POST":
        hanh_dong = (request.POST.get("hanh_dong") or "").strip()

        if hanh_dong == "tao_ho_so":
            ten_cn = (request.POST.get("ten_chuc_nang") or "").strip()
            linh_vuc = (request.POST.get("linh_vuc") or "chung").strip()
            if ten_cn:
                ho_so_moi = khoi_tao_ho_so_va_lam_ro(ten_cn, linh_vuc=linh_vuc)
                return redirect("giao_dien_ho_so", ho_so_id=ho_so_moi.id)
            thong_bao_log = "Chua nhap ten chuc nang de tao ho so."

        elif hanh_dong == "tu_lam_ro" and ho_so_hien_tai:
            kq_tu = tu_dong_sinh_va_tra_loi_lam_ro(ho_so_hien_tai)
            ho_so_hien_tai.refresh_from_db()
            thong_bao_log = (
                f"AI tu tra loi: {kq_tu.da_tu_tra_loi} | "
                f"Con hoi: {len(kq_tu.con_hoi_nguoi_dung)} | "
                f"Da chot: {kq_tu.da_chot_thong_tin}"
            )

        elif hanh_dong == "luu_tra_loi" and ho_so_hien_tai:
            dap_an_dict = {}
            for ch in ho_so_hien_tai.cac_cau_hoi.filter(can_hoi_lai=True):
                gia_tri = (request.POST.get(f"cau_{ch.ma_cau_hoi}") or "").strip()
                if gia_tri:
                    dap_an_dict[ch.ma_cau_hoi] = gia_tri
            if dap_an_dict:
                ho_so_hien_tai = luu_cau_tra_loi_lam_ro(ho_so_hien_tai, dap_an_dict)
                thong_bao_log = f"Da luu cau tra loi cho: {list(dap_an_dict.keys())}"
            else:
                thong_bao_log = "Chua nhap noi dung tra loi nao."

        elif hanh_dong in ("phan_tich_goi_y", "chot_goi_y") and ho_so_hien_tai:
            nhom_hien_tai = (request.POST.get("nhom_goi_y") or "nghiep_vu").strip()
            prompt_bo_sung = (request.POST.get("prompt_goi_y") or "").strip()
            ma_da_chon = set(request.POST.getlist("chon_goi_y"))

            # Dong bo trang thai checkbox hien tai truoc khi phan tich hoac chot
            for idx, muc in enumerate(danh_sach_goi_y):
                ma_muc = str(muc.get("ma") or f"M{idx + 1}")
                muc["da_chon"] = ma_muc in ma_da_chon

            if hanh_dong == "phan_tich_goi_y":
                # Neu doi sang nhom moi va chua nhap prompt thi sinh theo nhom do cho gon context
                nhom_truoc = danh_sach_goi_y[0].get("nhom") if danh_sach_goi_y else nhom_hien_tai
                du_lieu_nen = danh_sach_goi_y if nhom_truoc == nhom_hien_tai else None
                danh_sach_goi_y = lap_danh_sach_goi_y(
                    ho_so_hien_tai,
                    nhom=nhom_hien_tai,
                    prompt_dieu_chinh=prompt_bo_sung,
                    goi_y_hien_tai=du_lieu_nen,
                )
                thong_bao_log = f"Da cap nhat {len(danh_sach_goi_y)} dau muc goi y nhom [{nhom_hien_tai}]."
            else:
                danh_sach_goi_y, ban_tom_tat = chot_dau_muc_thanh_tom_tat(danh_sach_goi_y)
                session_tom_tat = request.session.get("tom_tat_theo_ho_so", {})
                session_tom_tat[str(ho_so_hien_tai.id)] = ban_tom_tat
                request.session["tom_tat_theo_ho_so"] = session_tom_tat
                thong_bao_log = f"Da chot {len(ban_tom_tat)} dau muc vao ban tom tat cong viec."

            session_goi_y = request.session.get("goi_y_theo_ho_so", {})
            session_goi_y[str(ho_so_hien_tai.id)] = danh_sach_goi_y
            request.session["goi_y_theo_ho_so"] = session_goi_y
            request.session.modified = True

        elif hanh_dong == "chay_muc" and ho_so_hien_tai:
            ma_muc = (request.POST.get("ma_muc") or "M1").strip()
            kq_muc = thuc_thi_mot_dau_muc(ho_so_hien_tai, ma_muc)
            ho_so_hien_tai.refresh_from_db()
            thong_bao_log = (
                f"{ma_muc}: pytest={kq_muc.chay_pytest_dat} | "
                f"file={kq_muc.duong_dan_file} | {kq_muc.thong_bao}"
            )

        elif hanh_dong == "chay_lai_test" and ho_so_hien_tai:
            ma_muc = (request.POST.get("ma_muc") or "M3").strip()
            kq_test = hoan_thien_va_chay_lai_test(ho_so_hien_tai, ma_muc)
            ho_so_hien_tai.refresh_from_db()
            thong_bao_log = (
                f"Test nghiep vu {ma_muc}: dat={kq_test.chay_pytest_dat} | {kq_test.thong_bao}"
            )

    cac_cau_hoi = list(ho_so_hien_tai.cac_cau_hoi.order_by("ma_cau_hoi")) if ho_so_hien_tai else []
    cac_dau_muc = list(ho_so_hien_tai.cac_dau_muc.order_by("ma_muc")) if ho_so_hien_tai else []
    doi_chieu = doi_chieu_hoan_tat_theo_ho_so(ho_so_hien_tai) if ho_so_hien_tai else None

    cac_nhom_mau = [
        ("nghiep_vu", "Nhóm: Nghiệp vụ & luồng"),
        ("du_lieu", "Nhóm: Dữ liệu & đối soát"),
        ("rang_buoc", "Nhóm: Ràng buộc & ngoại lệ"),
    ]
    danh_sach_nhom_goi_y = [
        {
            "gia_tri": ma_n,
            "nhan": ten_n,
            "dang_chon": (ma_n == nhom_hien_tai),
        }
        for ma_n, ten_n in cac_nhom_mau
    ]

    context = {
        "danh_sach_ho_so": danh_sach_ho_so,
        "ho_so": ho_so_hien_tai,
        "cac_cau_hoi": cac_cau_hoi,
        "cac_dau_muc": cac_dau_muc,
        "doi_chieu": doi_chieu,
        "thong_bao_log": thong_bao_log,
        "nhom_hien_tai": nhom_hien_tai,
        "danh_sach_nhom_goi_y": danh_sach_nhom_goi_y,
        "danh_sach_goi_y": danh_sach_goi_y,
        "ban_tom_tat": ban_tom_tat,
    }
    return render(request, "quan_ly_du_an/trang_dieu_khien.html", context)