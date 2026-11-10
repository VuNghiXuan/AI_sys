from django.db import transaction
from .models import PhieuNhapVangNguyenLieu, ItemLine

@transaction.atomic
def create_phieu_nhap_vang_nguyen_lieu(data):
    phieu_nhap = PhieuNhapVangNguyenLieu.objects.create(**data)
    for item_line_data in data['item_lines']:
        item_line_data['phieu_nhap'] = phieu_nhap
        ItemLine.objects.create(**item_line_data)
    return phieu_nhap

@transaction.atomic
def update_phieu_nhap_vang_nguyen_lieu(pk, data):
    phieu_nhap = PhieuNhapVangNguyenLieu.objects.get(pk=pk)
    phieu_nhap.update(**data)
    phieu_nhap.item_lines.all().delete()
    for item_line_data in data['item_lines']:
        item_line_data['phieu_nhap'] = phieu_nhap
        ItemLine.objects.create(**item_line_data)
    return phieu_nhap

def approve_phieu_nhap_vang_nguyen_lieu(pk):
    phieu_nhap = PhieuNhapVangNguyenLieu.objects.get(pk=pk)
    phieu_nhap.trang_thai = 'DaDuyet'
    phieu_nhap.ngay_duyet = timezone.now()
    phieu_nhap.save()

def reject_phieu_nhap_vang_nguyen_lieu(pk):
    phieu_nhap = PhieuNhapVangNguyenLieu.objects.get(pk=pk)
    phieu_nhap.trang_thai = 'KhongDuyet'
    phieu_nhap.save()

def cancel_phieu_nhap_vang_nguyen_lieu(pk):
    phieu_nhap = PhieuNhapVangNguyenLieu.objects.get(pk=pk)
    phieu_nhap.trang_thai = 'Huy'
    phieu_nhap.save()