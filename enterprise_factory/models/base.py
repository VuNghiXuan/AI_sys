# File: enterprise_factory/models/base.py
"""
Các mô hình cơ sở hệ thống (SystemConfig, Company, AgentRole) cho vnxBox Enterprise.
"""

from django.db import models


class SystemConfig(models.Model):
    """Bảng lưu trữ cấu hình hệ thống động (KeyValuePair)"""
    key = models.CharField(max_length=100, unique=True, verbose_name="Khóa cấu hình")
    value = models.TextField(blank=True, null=True, verbose_name="Giá trị cấu hình")
    description = models.TextField(blank=True, null=True, verbose_name="Mô tả cấu hình")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Thời gian cập nhật")

    class Meta:
        verbose_name = "Cấu hình hệ thống"
        verbose_name_plural = "Danh mục cấu hình hệ thống"

    def __str__(self):
        return f"{self.key} = {self.value}"


class Company(models.Model):
    """Mô hình quản lý công ty/đơn vị trực thuộc tập đoàn"""
    code = models.CharField(max_length=50, unique=True, verbose_name="Mã công ty")
    name = models.CharField(max_length=255, verbose_name="Tên công ty")
    is_active = models.BooleanField(default=True, verbose_name="Đang hoạt động")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Công ty"
        verbose_name_plural = "Danh sách Công ty"

    def __str__(self):
        return f"{self.name} ({self.code})"


