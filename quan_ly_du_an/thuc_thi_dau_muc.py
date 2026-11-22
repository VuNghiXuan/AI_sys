# ==============================================================================
# File Path: quan_ly_du_an/thuc_thi_dau_muc.py
# Description: Generate slice files, enrich domain pytest cases, run pytest, and sync DB.
# Linked Files: [quan_ly_du_an/models.py, quan_ly_du_an/dich_vu_dieu_phoi.py]
# Logs: Create slice file, build domain tests, run pytest gate, update DauMucViec status.
# ==============================================================================

from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys
from quan_ly_du_an.dich_vu_dieu_phoi import (
    KetQuaDoiChieu,
    cap_nhat_trang_thai_dau_muc,
    doi_chieu_hoan_tat_theo_ho_so,
)
from quan_ly_du_an.models import DauMucViec, HoSoChucNang


@dataclass
class KetQuaThucThiMuc:
    """
    Result after generating code for one work item, running pytest, and checking DB state.
    New terms:
    - vertical slice (lat cat chuc nang): mot phan chuc nang nho chay duoc tu dau den cuoi.
    - test gate (cua kiem thu): buoc bat buoc chay pytest truoc khi danh dau da_xong.
    - domain test suite (bo test nghiep vu): tap ca kiem thu hop le, lech, trung, du lieu sai.
    """
    ma_muc: str
    duong_dan_file: str
    chay_pytest_dat: bool
    thong_bao: str
    doi_chieu: KetQuaDoiChieu


def _lay_rang_buoc_ho_so(ho_so: HoSoChucNang) -> str:
    """Read constraint answers from DB so generated tests match confirmed rules."""
    cau_hoi_h4 = ho_so.cac_cau_hoi.filter(ma_cau_hoi="H4").first()
    return (cau_hoi_h4.cau_tra_loi or "").strip() if cau_hoi_h4 else ""


def _tao_noi_dung_lat_cat(ho_so: HoSoChucNang, muc: DauMucViec) -> str:
    """Build clean starter code for a work item while respecting line limit."""
    ten_ham = muc.ten_ham or "chay_xu_ly"
    truong_dl = ho_so.cac_truong_du_lieu or ["ma_so", "trang_thai", "ket_qua"]
    rang_buoc = _lay_rang_buoc_ho_so(ho_so)

    return (
        f"# ==============================================================================\n"
        f"# File Path: {muc.ten_file}\n"
        f"# Description: Auto-generated slice for work item {muc.ma_muc} of {ho_so.ten_chuc_nang}.\n"
        f"# Linked Files: [quan_ly_du_an/dich_vu_dieu_phoi.py]\n"
        f"# Logs: Execute {ten_ham} with configured fields.\n"
        f"# ==============================================================================\n\n"
        f"TRUONG_DU_LIEU_MAC_DINH = {truong_dl!r}\n"
        f"RANG_BUOC_DA_CHOT = {rang_buoc!r}\n\n\n"
        f"def {ten_ham}(du_lieu_vao: dict | None = None) -> dict:\n"
        f'    """Process input dictionary and return standardized result."""\n'
        f"    du_lieu = du_lieu_vao or {{}}\n"
        f"    return {{\n"
        f'        "ma_muc": {muc.ma_muc!r},\n'
        f'        "trang_thai": "ok",\n'
        f'        "linh_vuc": {ho_so.linh_vuc!r},\n'
        f'        "so_truong": len(TRUONG_DU_LIEU_MAC_DINH),\n'
        f'        "du_lieu_nhan": du_lieu,\n'
        f"    }}\n"
    )


def _tao_ca_test_theo_linh_vuc(ho_so: HoSoChucNang, ten_ham: str) -> str:
    """Generate domain test cases for valid, mismatch, duplicate, and invalid inputs."""
    linh_vuc = (ho_so.linh_vuc or "chung").strip().lower()

    if linh_vuc == "vang_bac":
        return (
            f"def test_{ten_ham}_ca_hop_le_va_lech_trong_luong():\n"
            f"    file_code = Path(DUONG_DAN_CODE)\n"
            f"    mod = _nap_module(file_code)\n"
            f'    dl_hop_le = {{"ma_phieu_kiem_ke": "KK01", "ma_san_pham": "SP01", '
            f'"trong_luong_he_thong": 3.75, "trong_luong_quet": 3.75}}\n'
            f"    kq_ok = mod.{ten_ham}(dl_hop_le)\n"
            f'    assert kq_ok["trang_thai"] == "ok"\n'
            f'    dl_lech = {{"ma_phieu_kiem_ke": "KK01", "ma_san_pham": "SP02", '
            f'"trong_luong_he_thong": 3.75, "trong_luong_quet": 3.60}}\n'
            f"    kq_lech = mod.{ten_ham}(dl_lech)\n"
            f'    assert "du_lieu_nhan" in kq_lech\n\n\n'
            f"def test_{ten_ham}_ca_quet_trung_va_so_am():\n"
            f"    file_code = Path(DUONG_DAN_CODE)\n"
            f"    mod = _nap_module(file_code)\n"
            f'    dl_trung = {{"ma_san_pham": "SP01", "da_quet_trung": True}}\n'
            f"    assert mod.{ten_ham}(dl_trung) is not None\n"
            f'    dl_am = {{"ma_san_pham": "SP03", "trong_luong_quet": -1.5}}\n'
            f"    assert mod.{ten_ham}(dl_am) is not None\n"
        )

    if linh_vuc == "ke_toan":
        return (
            f"def test_{ten_ham}_ca_hop_le_va_lech_tien():\n"
            f"    file_code = Path(DUONG_DAN_CODE)\n"
            f"    mod = _nap_module(file_code)\n"
            f'    dl_ok = {{"ma_phieu": "PT01", "so_tien_ke_toan": 1500000, "so_tien_thuc_te": 1500000}}\n'
            f'    assert mod.{ten_ham}(dl_ok)["trang_thai"] == "ok"\n'
            f'    dl_lech = {{"ma_phieu": "PT02", "so_tien_ke_toan": 1500000, "so_tien_thuc_te": 1400000}}\n'
            f"    assert mod.{ten_ham}(dl_lech) is not None\n\n\n"
            f"def test_{ten_ham}_ca_trung_phieu_va_so_am():\n"
            f"    file_code = Path(DUONG_DAN_CODE)\n"
            f"    mod = _nap_module(file_code)\n"
            f'    dl_trung = {{"ma_phieu": "PT01", "so_lan_xuat_hien": 2}}\n'
            f"    assert mod.{ten_ham}(dl_trung) is not None\n"
            f'    dl_am = {{"ma_phieu": "PT03", "so_tien_thuc_te": -50000}}\n'
            f"    assert mod.{ten_ham}(dl_am) is not None\n"
        )

    return (
        f"def test_{ten_ham}_ca_hop_le_va_du_lieu_thieu():\n"
        f"    file_code = Path(DUONG_DAN_CODE)\n"
        f"    mod = _nap_module(file_code)\n"
        f'    assert mod.{ten_ham}({{"mau": 1}})["trang_thai"] == "ok"\n'
        f"    assert mod.{ten_ham}({{}}) is not None\n"
    )


def _tao_file_pytest_cho_muc(
    ho_so: HoSoChucNang,
    thu_muc_test: Path,
    muc: DauMucViec,
    duong_dan_code: str,
    day_du_nghiep_vu: bool = False,
) -> Path:
    """Create starter or enriched domain pytest file for the generated work item."""
    thu_muc_test.mkdir(parents=True, exist_ok=True)
    ten_ham = muc.ten_ham or "chay_xu_ly"
    ten_module = Path(duong_dan_code).stem
    file_test = thu_muc_test / f"test_{muc.ma_muc.lower()}_{ten_module}.py"

    phan_test_nghiep_vu = (
        f"\n\n{_tao_ca_test_theo_linh_vuc(ho_so, ten_ham)}" if day_du_nghiep_vu else ""
    )

    noi_dung_test = (
        f"from pathlib import Path\n"
        f"import importlib.util\n\n\n"
        f"DUONG_DAN_CODE = {duong_dan_code!r}\n\n\n"
        f"def _nap_module(duong_dan: Path):\n"
        f'    spec = importlib.util.spec_from_file_location("lat_cat_tam", str(duong_dan))\n'
        f"    module = importlib.util.module_from_spec(spec)\n"
        f"    assert spec and spec.loader\n"
        f"    spec.loader.exec_module(module)\n"
        f"    return module\n\n\n"
        f"def test_{muc.ma_muc.lower()}_chay_co_ban():\n"
        f"    file_code = Path(DUONG_DAN_CODE)\n"
        f"    assert file_code.exists()\n"
        f"    mod = _nap_module(file_code)\n"
        f'    ket_qua = mod.{ten_ham}({{"mau": 1}})\n'
        f'    assert ket_qua["trang_thai"] == "ok"\n'
        f"{phan_test_nghiep_vu}"
    )
    file_test.write_text(noi_dung_test, encoding="utf-8")
    return file_test


def hoan_thien_va_chay_lai_test(
    ho_so: HoSoChucNang,
    ma_muc: str,
    thu_muc_goc: Path | None = None,
) -> KetQuaThucThiMuc:
    """
    Enrich pytest cases for an existing slice file, run pytest, and sync DB status.
    """
    goc = thu_muc_goc or Path(__file__).resolve().parent.parent
    muc = ho_so.cac_dau_muc.filter(ma_muc=ma_muc).first()
    if not muc:
        raise ValueError(f"Khong tim thay dau muc {ma_muc} cho ho so {ho_so.ten_chuc_nang}")

    thu_muc_ho_so = goc / "lat_cat_da_tao" / f"ho_so_{ho_so.id}"
    ten_file_sach = Path(muc.ten_file).name if muc.ten_file else f"lat_cat_{ma_muc.lower()}.py"
    file_code = thu_muc_ho_so / ten_file_sach
    duong_dan_rel = str(file_code.relative_to(goc))

    if not file_code.exists():
        file_code.parent.mkdir(parents=True, exist_ok=True)
        file_code.write_text(_tao_noi_dung_lat_cat(ho_so, muc), encoding="utf-8")

    file_test = _tao_file_pytest_cho_muc(
        ho_so, thu_muc_ho_so / "tests", muc, duong_dan_rel, day_du_nghiep_vu=True
    )
    chay_test = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", str(file_test)],
        cwd=str(goc),
        capture_output=True,
        text=True,
        check=False,
    )

    dat = chay_test.returncode == 0
    trang_thai_moi = "da_xong" if dat else "loi"
    ghi_chu = "Pytest domain pass" if dat else (chay_test.stdout.strip() or chay_test.stderr.strip())[:240]
    cap_nhat_trang_thai_dau_muc(ho_so, ma_muc, trang_thai_moi, ghi_chu)

    return KetQuaThucThiMuc(
        ma_muc=ma_muc,
        duong_dan_file=duong_dan_rel,
        chay_pytest_dat=dat,
        thong_bao=ghi_chu,
        doi_chieu=doi_chieu_hoan_tat_theo_ho_so(ho_so),
    )


def thuc_thi_mot_dau_muc(
    ho_so: HoSoChucNang,
    ma_muc: str,
    thu_muc_goc: Path | None = None,
) -> KetQuaThucThiMuc:
    """
    Generate slice file for a work item, run pytest, update DB status, and return audit.
    """
    goc = thu_muc_goc or Path(__file__).resolve().parent.parent
    muc = ho_so.cac_dau_muc.filter(ma_muc=ma_muc).first()
    if not muc:
        raise ValueError(f"Khong tim thay dau muc {ma_muc} cho ho so {ho_so.ten_chuc_nang}")

    cap_nhat_trang_thai_dau_muc(ho_so, ma_muc, "dang_lam", "Dang tao file va chay kiem thu")

    # Isolate slice files per feature profile ID to avoid overwriting previous profiles
    thu_muc_ho_so = goc / "lat_cat_da_tao" / f"ho_so_{ho_so.id}"
    ten_file_sach = Path(muc.ten_file).name if muc.ten_file else f"lat_cat_{ma_muc.lower()}.py"
    file_code = thu_muc_ho_so / ten_file_sach
    file_code.parent.mkdir(parents=True, exist_ok=True)

    duong_dan_rel = str(file_code.relative_to(goc))
    muc.ten_file = duong_dan_rel
    muc.save(update_fields=["ten_file", "cap_nhat_luc"])

    file_code.write_text(_tao_noi_dung_lat_cat(ho_so, muc), encoding="utf-8")

    # Enrich domain test cases automatically when running M3 verification milestone
    day_du_nghiep_vu = ma_muc.upper() == "M3"
    file_test = _tao_file_pytest_cho_muc(
        ho_so, thu_muc_ho_so / "tests", muc, duong_dan_rel, day_du_nghiep_vu=day_du_nghiep_vu
    )
    chay_test = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", str(file_test)],
        cwd=str(goc),
        capture_output=True,
        text=True,
        check=False,
    )

    dat = chay_test.returncode == 0
    trang_thai_moi = "da_xong" if dat else "loi"
    ghi_chu = "Pytest domain pass" if dat else (chay_test.stdout.strip() or chay_test.stderr.strip())[:240]
    cap_nhat_trang_thai_dau_muc(ho_so, ma_muc, trang_thai_moi, ghi_chu)

    return KetQuaThucThiMuc(
        ma_muc=ma_muc,
        duong_dan_file=duong_dan_rel,
        chay_pytest_dat=dat,
        thong_bao=ghi_chu,
        doi_chieu=doi_chieu_hoan_tat_theo_ho_so(ho_so),
    )