from pathlib import Path
import importlib.util


def _nap_module(duong_dan: Path):
    spec = importlib.util.spec_from_file_location("lat_cat_tam", str(duong_dan))
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_m2_chay_co_ban():
    file_code = Path('lat_cat_da_tao\\lat_cat_da_tao\\xu_ly_chinh.py')
    assert file_code.exists()
    mod = _nap_module(file_code)
    ket_qua = mod.chay_xu_ly({"mau": 1})
    assert ket_qua["trang_thai"] == "ok"
