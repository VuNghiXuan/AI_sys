# ============================================================================
# File Path: core_policy/hardware.py
# Module: Tu Dong Nhan Dien Phan Cung Va Tinh Nguong An Toan Local
# Linked Files: core_policy/loader.py,
#               core_policy/gateway.py
# Purpose: Phat hien so luong CPU, tong RAM, RAM kha dung, thong tin GPU/VRAM
#          (neu co) va tinh tham so an toan cho model local.
# ============================================================================

from __future__ import annotations

import logging
import os
import platform
import subprocess
from dataclasses import dataclass, field
from typing import Any

import psutil

from .loader import HardwareConfig

logger = logging.getLogger(__name__)


@dataclass
class ThongTinGpu:
    """Thong tin co ban ve GPU neu co driver ho tro."""

    ten: str
    tong_vram_mb: int | None = None
    trong_vram_mb: int | None = None


@dataclass
class HoSoPhanCung:
    """Tong hop trang thai phan cung thoi diem hien tai."""

    he_dieu_hanh: str
    cpu_logic: int
    cpu_vat_ly: int
    tong_ram_mb: int
    ram_kha_dung_mb: int
    ram_su_dung_phan_tram: float
    goi_y_num_thread: int
    goi_y_num_ctx: int
    gpu_ds: list[ThongTinGpu] = field(default_factory=list)

    def du_ram_cho_local(self, toi_thieu_mb: int) -> bool:
        """Kiem tra RAM kha dung co dat nguong toi thieu de chay model local khong."""
        return self.ram_kha_dung_mb >= toi_thieu_mb

    def sang_dict(self) -> dict[str, Any]:
        """Chuyen ho so thanh dict phuc vu log hoac tra API."""
        return {
            "he_dieu_hanh": self.he_dieu_hanh,
            "cpu_logic": self.cpu_logic,
            "cpu_vat_ly": self.cpu_vat_ly,
            "tong_ram_mb": self.tong_ram_mb,
            "ram_kha_dung_mb": self.ram_kha_dung_mb,
            "ram_su_dung_phan_tram": self.ram_su_dung_phan_tram,
            "goi_y_num_thread": self.goi_y_num_thread,
            "goi_y_num_ctx": self.goi_y_num_ctx,
            "gpu_count": len(self.gpu_ds),
            "gpus": [g.__dict__ for g in self.gpu_ds],
        }


def _do_gpu_nvidia() -> list[ThongTinGpu]:
    """Thu doc thong tin VRAM qua nvidia-smi neu co GPU NVIDIA."""
    try:
        kq = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,memory.free",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=2.0,
            check=False,
        )
    except OSError:
        return []

    if kq.returncode != 0 or not kq.stdout.strip():
        return []

    ds: list[ThongTinGpu] = []
    for dong in kq.stdout.strip().splitlines():
        phan = [p.strip() for p in dong.split(",")]
        if len(phan) < 3:
            continue
        try:
            tong_mb = int(float(phan[1]))
            trong_mb = int(float(phan[2]))
        except ValueError:
            tong_mb, trong_mb = None, None
        ds.append(ThongTinGpu(ten=phan[0], tong_vram_mb=tong_mb, trong_vram_mb=trong_mb))
    return ds


def _tinh_num_ctx_an_toan(ram_kha_dung_mb: int, cap_max: int) -> int:
    """Tinh context window an toan dua tren RAM kha dung."""
    if ram_kha_dung_mb >= 16384:
        de_xuat = 8192
    elif ram_kha_dung_mb >= 8192:
        de_xuat = 4096
    elif ram_kha_dung_mb >= 4096:
        de_xuat = 2048
    else:
        de_xuat = 1024
    return max(1024, min(de_xuat, cap_max))


def nhan_dien_phan_cung(cau_hinh: HardwareConfig | None = None) -> HoSoPhanCung:
    """Tu dong quet tai nguyen CPU/RAM/GPU hien tai."""
    cfg = cau_hinh or HardwareConfig()
    vm = psutil.virtual_memory()
    cpu_logic = os.cpu_count() or 4
    cpu_vat_ly = psutil.cpu_count(logical=False) or max(1, cpu_logic // 2)
    tong_ram_mb = int(vm.total // (1024 * 1024))
    ram_kha_dung_mb = int(vm.available // (1024 * 1024))

    # Giu lai it nhat 2 luong cho he dieu hanh va UI
    goi_y_thread = max(1, min(cpu_logic - 2 if cpu_logic > 4 else cpu_logic, 16))
    goi_y_ctx = _tinh_num_ctx_an_toan(ram_kha_dung_mb, cfg.local_max_ctx_cap)
    gpu_ds = _do_gpu_nvidia() if cfg.auto_detect else []

    ho_so = HoSoPhanCung(
        he_dieu_hanh=f"{platform.system()} {platform.release()}",
        cpu_logic=cpu_logic,
        cpu_vat_ly=cpu_vat_ly,
        tong_ram_mb=tong_ram_mb,
        ram_kha_dung_mb=ram_kha_dung_mb,
        ram_su_dung_phan_tram=float(vm.percent),
        goi_y_num_thread=goi_y_thread,
        goi_y_num_ctx=goi_y_ctx,
        gpu_ds=gpu_ds,
    )
    logger.debug(
        "Phan cung: RAM trong=%d/%dMB (%.1f%%), CPU=%d, num_ctx=%d",
        ho_so.ram_kha_dung_mb,
        ho_so.tong_ram_mb,
        ho_so.ram_su_dung_phan_tram,
        ho_so.cpu_logic,
        ho_so.goi_y_num_ctx,
    )
    return ho_so