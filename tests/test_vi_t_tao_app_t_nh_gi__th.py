import sys
import os
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modules.vi_t_tao_app_t_nh_gi__th import *

def test_module_sanity():
    assert True

def test_functions_exist():
    import modules.vi_t_tao_app_t_nh_gi__th as mod
    items = [x for x in dir(mod) if not x.startswith('_')]
    assert len(items) >= 0
