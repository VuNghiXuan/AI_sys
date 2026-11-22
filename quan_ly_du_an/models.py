# ==============================================================================
# File Path: quan_ly_du_an/models.py
# Description: Database models for machine config, feature profiles, questions, and tasks.
# Linked Files: [he_thong/settings.py]
# Logs: Define CauHinhMay, HoSoChucNang, CauHoiLamRo, DauMucViec models.
# ==============================================================================

from django.db import models


class CauHinhMay(models.Model):
    """
    Stores host machine specs and running limits in database.
    New terms:
    - model / table (bang du lieu): noi luu du lieu co dinh trong database.
    - primary key (khoa chinh): ma dinh danh rieng cho tung dong du lieu.
    """
    ten_may = models.CharField(max_length=120, unique=True)
    he_dieu_hanh = models.CharField(max_length=120, blank=True, default="")
    phien_ban_python = models.CharField(max_length=40, blank=True, default="")
    so_luong_cpu = models.IntegerField(default=1)
    tong_ram_gb = models.FloatField(default=0.0)
    dung_luong_trong_gb = models.FloatField(default=0.0)
    co_gpu_roi = models.BooleanField(default=False)
    mo_ta_gpu = models.CharField(max_length=200, blank=True, default="")
    muc_chay_goi_y = models.CharField(max_length=60, default="tiet_kiem_cpu_ram")
    gioi_han_so_dong_file = models.IntegerField(default=300)
    gioi_han_luot_sua_loi = models.IntegerField(default=4)
    thoi_diem_cap_nhat = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cấu hình máy"
        verbose_name_plural = "Cấu hình máy"

    def __str__(self) -> str:
        return f"{self.ten_may} ({self.muc_chay_goi_y})"


class HoSoChucNang(models.Model):
    """
    Stores feature details, fields, code links, and test cases in database.
    New terms:
    - feature record (ho so chuc nang): ban luu thong tin chuc nang, truong du lieu, file/ham/bien va ca kiem thu.
    - JSONField (truong luu du lieu cau truc JSON): cot luu danh sach hoac tu dien nho gon trong database.
    """
    ten_chuc_nang = models.CharField(max_length=200, unique=True)
    linh_vuc = models.CharField(max_length=80, default="chung")
    lam_cho_ai = models.TextField(blank=True, default="")
    muc_dich = models.TextField(blank=True, default="")
    cac_truong_du_lieu = models.JSONField(default=list, blank=True)
    so_do_bang_gon = models.JSONField(default=dict, blank=True)
    file_ham_bien = models.JSONField(default=dict, blank=True)
    phan_anh_huong = models.JSONField(default=dict, blank=True)
    ca_kiem_thu = models.JSONField(default=list, blank=True)
    da_chot_thong_tin = models.BooleanField(default=False)
    ngay_tao = models.DateTimeField(auto_now_add=True)
    ngay_cap_nhat = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Hồ sơ chức năng"
        verbose_name_plural = "Hồ sơ chức năng"

    def __str__(self) -> str:
        return self.ten_chuc_nang


class CauHoiLamRo(models.Model):
    """
    Stores questions generated to clarify a feature before building.
    New terms:
    - foreign key (khoa ngoai): lien ket dong cau hoi nay toi dung HoSoChucNang.
    - clarifying question (cau hoi lam ro): cau hoi hoi cho ro y truoc khi chot viec lam.
    """
    ho_so = models.ForeignKey(HoSoChucNang, on_delete=models.CASCADE, related_name="cac_cau_hoi")
    ma_cau_hoi = models.CharField(max_length=20)
    nhom_hoi = models.CharField(max_length=50)
    noi_dung_hoi = models.TextField()
    da_tra_loi = models.BooleanField(default=False)
    cau_tra_loi = models.TextField(blank=True, default="")
    can_hoi_lai = models.BooleanField(default=True)

    class Meta:
        unique_together = ("ho_so", "ma_cau_hoi")
        verbose_name = "Câu hỏi làm rõ"
        verbose_name_plural = "Câu hỏi làm rõ"

    def __str__(self) -> str:
        return f"{self.ho_so.ten_chuc_nang} - {self.ma_cau_hoi}"


class DauMucViec(models.Model):
    """
    Stores each work item inside a feature plan to track completion.
    New terms:
    - work item (dau muc viec): mot viec nho cu the gan voi file va ham xu ly.
    - completion check (doi chieu hoan tat): kiem tra xem tung viec da xong that chua.
    """
    TRANG_THAI_LUA_CHON = [
        ("chua_lam", "Chưa làm"),
        ("dang_lam", "Đang làm"),
        ("da_xong", "Đã xong"),
        ("loi", "Bị lỗi"),
    ]

    ho_so = models.ForeignKey(HoSoChucNang, on_delete=models.CASCADE, related_name="cac_dau_muc")
    ma_muc = models.CharField(max_length=20)
    ten_viec = models.CharField(max_length=255)
    ten_file = models.CharField(max_length=150, blank=True, default="")
    ten_ham = models.CharField(max_length=150, blank=True, default="")
    trang_thai = models.CharField(max_length=20, choices=TRANG_THAI_LUA_CHON, default="chua_lam")
    ghi_chu = models.TextField(blank=True, default="")
    cap_nhat_luc = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("ho_so", "ma_muc")
        verbose_name = "Đầu mục việc"
        verbose_name_plural = "Đầu mục việc"

    def __str__(self) -> str:
        return f"{self.ma_muc} [{self.trang_thai}] - {self.ten_viec}"