# ============================================================================
# File Path: dieu_phoi_y_dinh/models.py
# Module: Model Luu Lich Su Prompt & Cau Tra Loi Hien Thi
# Linked Files: bo_nao_cache_cosine.py, truy_van_du_lieu.py
# Purpose: Luu tru ben vung prompt nguoi dung, ket qua hien thi, nhanh dieu phoi
#          va linh vuc de phuc vu tra cuu lich su va noi ngu canh hoi thoai.
# ============================================================================

from django.db import models


class LichSuDieuPhoi(models.Model):
    """Luu moi luot dieu phoi gom ca cau hoi (prompt) va cau tra loi hien thi."""

    prompt = models.TextField(verbose_name="Prompt người dùng")
    ket_qua_hien_thi = models.TextField(blank=True, default="", verbose_name="Kết quả hiển thị")
    y_dinh = models.CharField(max_length=64, blank=True, default="", verbose_name="Ý định / Nhánh")
    ma_linh_vuc = models.CharField(max_length=64, blank=True, default="tong_quat", verbose_name="Mã lĩnh vực")
    ten_linh_vuc = models.CharField(max_length=128, blank=True, default="Đa ngành / Tổng quát", verbose_name="Tên lĩnh vực")
    trung_cache = models.BooleanField(default=False, verbose_name="Trúng cache")
    thoi_gian_tao = models.DateTimeField(auto_now_add=True, verbose_name="Thời gian tạo")

    class Meta:
        ordering = ["-id"]
        verbose_name = "Lịch sử điều phối"
        verbose_name_plural = "Lịch sử điều phối"

    def __str__(self) -> str:
        return f"[{self.id}] {self.prompt[:50]}"