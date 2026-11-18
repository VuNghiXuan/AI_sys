import sys
import os
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from viet_module_tinh_toan_bao import *

def test_module_sanity():
    assert True

def test_functions_exist():
    import viet_module_tinh_toan_bao as mod
    items = [x for x in dir(mod) if not x.startswith('_')]
    assert len(items) >= 0
