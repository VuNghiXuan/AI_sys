# ==============================================================================
# File Path: quan_ly_du_an/admin.py
# Description: Register database models in Django admin for easy viewing and editing.
# Linked Files: [quan_ly_du_an/models.py]
# Logs: Configure admin list views, filters, and search for CauHinhMay, HoSoChucNang, CauHoiLamRo, DauMucViec.
# ==============================================================================

from django.contrib import admin
from quan_ly_du_an.models import (
    CauHinhMay,
    CauHoiLamRo,
    DauMucViec,
    HoSoChucNang,
)


class CauHoiLamRoDongCon(admin.TabularInline):
    """
    Show related clarifying questions inline inside a feature record page.
    New terms:
    - inline (hien thi noi tuyen): xem va sua cac dong lien quan ngay tren trang ban ghi cha.
    - tabular inline (hien thi dang bang con): trinh bay cac dong con thanh tung hang gon gang.
    """
    model = CauHoiLamRo
    extra = 0
    fields = ("ma_cau_hoi", "nhom_hoi", "noi_dung_hoi", "da_tra_loi", "cau_tra_loi", "can_hoi_lai")


class DauMucViecDongCon(admin.TabularInline):
    """
    Show related work items inline inside a feature record page for quick status check.
    New terms:
    - completion audit (doi chieu hoan tat): nhin nhanh trang thai tung dau muc da xong hay con ton dong.
    """
    model = DauMucViec
    extra = 0
    fields = ("ma_muc", "ten_viec", "ten_file", "ten_ham", "trang_thai", "ghi_chu")


@admin.register(CauHinhMay)
class QuanTriCauHinhMay(admin.ModelAdmin):
    """
    Admin configuration for host machine specs and running limits.
    New terms:
    - list display (cot hien thi danh sach): cac cot hien ra o bang tong hop trong trang admin.
    - list filter (bo loc ben canh): o loc nhanh theo gia tri cot.
    """
    list_display = (
        "ten_may",
        "so_luong_cpu",
        "tong_ram_gb",
        "co_gpu_roi",
        "muc_chay_goi_y",
        "gioi_han_so_dong_file",
        "gioi_han_luot_sua_loi",
        "thoi_diem_cap_nhat",
    )
    list_filter = ("co_gpu_roi", "muc_chay_goi_y")
    search_fields = ("ten_may", "he_dieu_hanh", "mo_ta_gpu")


@admin.register(HoSoChucNang)
class QuanTriHoSoChucNang(admin.ModelAdmin):
    """
    Admin configuration for feature records, code links, and inline questions/tasks.
    New terms:
    - feature record (ho so chuc nang): noi luu thong tin chuc nang, truong du lieu, file/ham/bien va ca kiem thu.
    """
    list_display = (
        "ten_chuc_nang",
        "linh_vuc",
        "da_chot_thong_tin",
        "ngay_cap_nhat",
    )
    list_filter = ("linh_vuc", "da_chot_thong_tin")
    search_fields = ("ten_chuc_nang", "lam_cho_ai", "muc_dich")
    inlines = [CauHoiLamRoDongCon, DauMucViecDongCon]


@admin.register(CauHoiLamRo)
class QuanTriCauHoiLamRo(admin.ModelAdmin):
    """
    Admin configuration to review self-answered vs pending user questions.
    New terms:
    - clarifying question (cau hoi lam ro): cau hoi hoi cho ro y truoc khi chot viec lam.
    """
    list_display = (
        "ho_so",
        "ma_cau_hoi",
        "nhom_hoi",
        "da_tra_loi",
        "can_hoi_lai",
    )
    list_filter = ("nhom_hoi", "da_tra_loi", "can_hoi_lai")
    search_fields = ("ma_cau_hoi", "noi_dung_hoi", "cau_tra_loi")


@admin.register(DauMucViec)
class QuanTriDauMucViec(admin.ModelAdmin):
    """
    Admin configuration to track and audit work item statuses.
    New terms:
    - work item (dau muc viec): mot viec nho cu th e gan voi file va ham xu ly.
    """
    list_display = (
        "ho_so",
        "ma_muc",
        "ten_viec",
        "ten_file",
        "trang_thai",
        "cap_nhat_luc",
    )
    list_filter = ("trang_thai", "ten_file")
    search_fields = ("ma_muc", "ten_viec", "ten_ham", "ghi_chu")