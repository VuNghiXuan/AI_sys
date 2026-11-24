# ============================================================================
# File Path: dieu_phoi_y_dinh/dich_vu/dinh_tuyen/bo_dang_ky_y_dinh.py
# Module: Bo Dang Ky Y Dinh Thong Nhat Tu cau_hinh_y_dinh.json
# Linked Files: dieu_phoi_y_dinh/dich_vu/dinh_tuyen/bo_dinh_tuyen_ngu_nghia.py,
#               dieu_phoi_y_dinh/dich_vu/thuc_thi_nhanh/trinh_xu_ly_chung.py
# Purpose: Nap cau hinh y dinh tu JSON, khop tu khoa/ngu nghia va thuc thi
#          theo che do xu ly hoac handler rieng.
# ============================================================================

from collections.abc import Callable
from dataclasses import dataclass, field
import importlib
import json
import logging
from pathlib import Path
from typing import Any

from ..thuc_thi_nhanh.trinh_xu_ly_chung import (
    ThongTinYDinhThucThi,
    thuc_thi_theo_che_do,
)
from .bo_dinh_tuyen_ngu_nghia import dinh_tuyen_ngu_nghia

logger = logging.getLogger(__name__)

TrinhXuLyRieng = Callable[[Path, str, dict[str, Any] | None], Any]


@dataclass
class DinhNghiaYDinh:
    """Cau hinh mot y dinh."""

    ma_y_dinh: str
    mien: str = ""
    nhom_lon: str = "he_thong"
    uu_tien_nhanh: bool = False
    che_do_xu_ly: str = "chat_tu_do"
    db_muc_tieu: str = "models_theo_app"
    tu_khoa_nhanh: list[str] = field(default_factory=list)
    cau_mau_ngu_nghia: list[str] = field(default_factory=list)
    mo_ta_ngu_nghia: str = ""
    mau_tra_loi: str = ""
    chi_dan_llm: str = ""
    module_trinh_xu_ly: str = ""
    ten_trinh_xu_ly: str = ""
    trinh_xu_ly_rieng: TrinhXuLyRieng | None = None


class BoDangKyYDinh:
    """Nap JSON, dinh tuyen va thuc thi y dinh."""

    def __init__(self) -> None:
        self._cac_y_dinh: dict[str, DinhNghiaYDinh] = {}
        self._duong_dan_json: Path | None = None
        self._du_lieu_json: dict[str, Any] = {}

    def _nap_ham_rieng(self, yd: DinhNghiaYDinh) -> None:
        """Neu khai bao module + ten ham rieng thi import dong."""
        if yd.module_trinh_xu_ly and yd.ten_trinh_xu_ly:
            try:
                mod = importlib.import_module(yd.module_trinh_xu_ly)
                ham = getattr(mod, yd.ten_trinh_xu_ly, None)
                if callable(ham):
                    yd.trinh_xu_ly_rieng = ham
            except Exception as loi:
                logger.warning(
                    "Khong nap duoc handler rieng %s.%s: %s",
                    yd.module_trinh_xu_ly,
                    yd.ten_trinh_xu_ly,
                    loi,
                )

    def nap_tu_json(self, duong_dan_json: Path) -> int:
        """Nap danh sach y dinh tu file cau_hinh_y_dinh.json."""
        du_lieu = json.loads(duong_dan_json.read_text(encoding="utf-8"))
        self._duong_dan_json = duong_dan_json
        self._du_lieu_json = du_lieu
        self._cac_y_dinh.clear()

        for muc in du_lieu.get("y_dinh") or []:
            if not isinstance(muc, dict):
                continue
            ma_yd = str(muc.get("ma_y_dinh") or "").strip()
            if not ma_yd:
                continue
            yd = DinhNghiaYDinh(
                ma_y_dinh=ma_yd,
                mien=str(muc.get("mien") or ""),
                nhom_lon=str(muc.get("nhom_lon") or "he_thong"),
                uu_tien_nhanh=bool(muc.get("uu_tien_nhanh", False)),
                che_do_xu_ly=str(muc.get("che_do_xu_ly") or "chat_tu_do"),
                db_muc_tieu=str(muc.get("db_muc_tieu") or "models_theo_app"),
                tu_khoa_nhanh=[str(k).strip() for k in (muc.get("tu_khoa_nhanh") or []) if str(k).strip()],
                cau_mau_ngu_nghia=[str(c).strip() for c in (muc.get("cau_mau_ngu_nghia") or []) if str(c).strip()],
                mo_ta_ngu_nghia=str(muc.get("mo_ta_ngu_nghia") or ""),
                mau_tra_loi=str(muc.get("mau_tra_loi") or ""),
                chi_dan_llm=str(muc.get("chi_dan_llm") or ""),
                module_trinh_xu_ly=str(muc.get("module_trinh_xu_ly") or "").strip(),
                ten_trinh_xu_ly=str(muc.get("ten_trinh_xu_ly") or "").strip(),
            )
            self._nap_ham_rieng(yd)
            self._cac_y_dinh[ma_yd] = yd

        logger.info("Da nap %d y dinh tu %s", len(self._cac_y_dinh), duong_dan_json)
        return len(self._cac_y_dinh)

    def lay_y_dinh(self, ma_yd: str) -> DinhNghiaYDinh | None:
        """Tra ve dinh nghia y dinh theo ma, hoac None neu khong ton tai."""
        return self._cac_y_dinh.get((ma_yd or "").strip())

    def lay_tat_ca(self) -> list[DinhNghiaYDinh]:
        """Tra ve danh sach y dinh."""
        return list(self._cac_y_dinh.values())

    def khop_nhanh(self, cau_hoi: str, dung_ngu_nghia: bool = True) -> DinhNghiaYDinh | None:
        """Khop tu khoa nhanh truoc, sau do dinh tuyen ngu nghia qua bo_dinh_tuyen_ngu_nghia."""
        thuong = " ".join((cau_hoi or "").lower().split())
        if not thuong:
            return None

        for yd in self._cac_y_dinh.values():
            for kw in yd.tu_khoa_nhanh:
                if kw.lower() in thuong:
                    return yd

        if dung_ngu_nghia and self._duong_dan_json and self._du_lieu_json:
            kq = dinh_tuyen_ngu_nghia(cau_hoi, self._duong_dan_json, self._du_lieu_json)
            if kq and kq.ma_y_dinh in self._cac_y_dinh:
                return self._cac_y_dinh[kq.ma_y_dinh]
        return None

    def thuc_thi(
        self,
        cau_hoi: str,
        goc_du_an: Path,
        chi_muc: dict[str, Any] | None = None,
        ma_y_dinh_chi_dinh: str | None = None,
    ) -> dict[str, Any]:
        """Thuc thi handler rieng neu co, nguoc lai dung trinh_xu_ly_chung theo che_do_xu_ly."""
        yd = self._cac_y_dinh.get(ma_y_dinh_chi_dinh) if ma_y_dinh_chi_dinh else self.khop_nhanh(cau_hoi)
        if yd is None:
            return {"noi_dung": "", "chuyen_huong_tao_app": False}

        if yd.trinh_xu_ly_rieng is not None:
            kq = yd.trinh_xu_ly_rieng(goc_du_an, cau_hoi, chi_muc)
            if isinstance(kq, dict):
                return kq
            return {"noi_dung": str(kq or ""), "chuyen_huong_tao_app": yd.che_do_xu_ly == "tao_app"}

        return thuc_thi_theo_che_do(
            ThongTinYDinhThucThi(
                ma_y_dinh=yd.ma_y_dinh,
                che_do_xu_ly=yd.che_do_xu_ly,
                db_muc_tieu=yd.db_muc_tieu,
                mau_tra_loi=yd.mau_tra_loi,
                chi_dan_llm=yd.chi_dan_llm,
                mo_ta_ngu_nghia=yd.mo_ta_ngu_nghia,
            ),
            goc_du_an,
            cau_hoi,
            chi_muc,
        )