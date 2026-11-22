from pathlib import Path
import importlib.util


DUONG_DAN_CODE = 'lat_cat_da_tao\\ho_so_2\\kiem_tra_ket_qua.py'


def _nap_module(duong_dan: Path):
    spec = importlib.util.spec_from_file_location("lat_cat_tam", str(duong_dan))
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_m3_chay_co_ban():
    file_code = Path(DUONG_DAN_CODE)
    assert file_code.exists()
    mod = _nap_module(file_code)
    ket_qua = mod.doi_chieu_hoan_tat({"mau": 1})
    assert ket_qua["trang_thai"] == "ok"


def test_doi_chieu_hoan_tat_ca_hop_le_va_lech_trong_luong():
    file_code = Path(DUONG_DAN_CODE)
    mod = _nap_module(file_code)
    dl_hop_le = {"ma_phieu_kiem_ke": "KK01", "ma_san_pham": "SP01", "trong_luong_he_thong": 3.75, "trong_luong_quet": 3.75}
    kq_ok = mod.doi_chieu_hoan_tat(dl_hop_le)
    assert kq_ok["trang_thai"] == "ok"
    dl_lech = {"ma_phieu_kiem_ke": "KK01", "ma_san_pham": "SP02", "trong_luong_he_thong": 3.75, "trong_luong_quet": 3.60}
    kq_lech = mod.doi_chieu_hoan_tat(dl_lech)
    assert "du_lieu_nhan" in kq_lech


def test_doi_chieu_hoan_tat_ca_quet_trung_va_so_am():
    file_code = Path(DUONG_DAN_CODE)
    mod = _nap_module(file_code)
    dl_trung = {"ma_san_pham": "SP01", "da_quet_trung": True}
    assert mod.doi_chieu_hoan_tat(dl_trung) is not None
    dl_am = {"ma_san_pham": "SP03", "trong_luong_quet": -1.5}
    assert mod.doi_chieu_hoan_tat(dl_am) is not None
