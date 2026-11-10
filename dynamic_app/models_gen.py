from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class PhieuNhapVangNguyenLieu(models.Model):
    so_phieu = models.CharField(max_length=50, unique=True)
    ngay_lap = models.DateTimeField(default=timezone.now)
    kho_nhap = models.CharField(max_length=100)
    chi_nhanh = models.CharField(max_length=100)
    mo_ta = models.TextField()
    chung_tu_tham_chiêu = models.CharField(max_length=100)
    nguoi_tao = models.ForeignKey(User, on_delete=models.CASCADE, related_name='phieunhapvangnguyenlieu_tao')
    nguoi_duyet = models.ForeignKey(User, on_delete=models.CASCADE, related_name='phieunhapvangnguyenlieu_duyet', null=True, blank=True)
    ngay_duyet = models.DateTimeField(null=True, blank=True)
    trang_thai = models.CharField(max_length=20, choices=[
        ('KhoiTao', 'Khởi tạo'),
        ('ChoDuyet', 'Chờ duyệt'),
        ('DaDuyet', 'Đã duyệt'),
        ('KhongDuyet', 'Không duyệt'),
        ('Huy', 'Hủy')
    ], default='KhoiTao')

    def save(self, *args, **kwargs):
        if not self.so_phieu:
            self.so_phieu = f"PNVNL{self.chi_nhanh}{self.ngay_lap.strftime('%Y%m%d')}{self.id}"
        super().save(*args, **kwargs)

class ItemLine(models.Model):
    phieu_nhap = models.ForeignKey(PhieuNhapVangNguyenLieu, on_delete=models.CASCADE, related_name='item_lines')
    loai_vang = models.CharField(max_length=100)
    hlv_thuc_te = models.DecimalField(max_digits=10, decimal_places=2)
    so_luong = models.IntegerField()
    tong_tl = models.DecimalField(max_digits=15, decimal_places=2)
    tl_hot = models.DecimalField(max_digits=15, decimal_places=2)
    tl_vang = models.DecimalField(max_digits=15, decimal_places=2, editable=False)
    ty_gia = models.DecimalField(max_digits=10, decimal_places=4)
    thanh_tien = models.DecimalField(max_digits=15, decimal_places=2, editable=False)
    tl_vang_quy_10 = models.DecimalField(max_digits=15, decimal_places=2, editable=False)
    so_lo = models.CharField(max_length=100)
    so_serial = models.CharField(max_length=100)

    def save(self, *args, **kwargs):
        self.tl_vang = self.tong_tl - self.tl_hot
        self.thanh_tien = self.tl_vang * self.ty_gia
        self.tl_vang_quy_10 = self.tl_vang * self.hlv_thuc_te / 100
        super().save(*args, **kwargs)