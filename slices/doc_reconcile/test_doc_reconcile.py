# ==============================================================================
# File Path: slices/doc_reconcile/test_doc_reconcile.py
# Description: Unit test cho lát cắt đối soát chứng từ/bảng kê.
# Linked Files: [slices/doc_reconcile/contract.py, slices/doc_reconcile/core.py, slices/doc_reconcile/ui_view.py]
# Slice Tag: [SLICE: DOC_RECONCILE_TEST]
# ==============================================================================

from slices.doc_reconcile.contract import build_config_from_dict
from slices.doc_reconcile.core import reconcile_records
from slices.doc_reconcile.ui_view import format_reconcile_summary


def test_reconcile_matches_tolerance_and_mismatch():
    cfg = build_config_from_dict(
        {
            "key_fields": ["code"],
            "rules": [
                {"source_field": "amount", "target_field": "amount", "tolerance": "5", "compare_type": "numeric"},
                {"source_field": "vendor", "target_field": "vendor", "compare_type": "text"},
            ],
        }
    )
    src = [
        {"code": "CT01", "amount": 1000, "vendor": "NCC A"},
        {"code": "CT02", "amount": 2003, "vendor": "ncc b"},
        {"code": "CT03", "amount": 3050, "vendor": "NCC C"},
    ]
    tgt = [
        {"code": "CT01", "amount": 1000, "vendor": "NCC A"},
        {"code": "CT02", "amount": 2000, "vendor": "NCC B"},
        {"code": "CT03", "amount": 3000, "vendor": "NCC C"},
    ]

    report = reconcile_records(src, tgt, cfg)
    assert report.matched_count == 1
    assert report.within_tolerance_count == 1
    assert report.mismatch_count == 1

    view = format_reconcile_summary(report)
    assert len(view["actionable_items"]) == 2


def test_reconcile_missing_and_extra_rows():
    cfg = build_config_from_dict({"key_fields": ["code"], "rules": []})
    src = [{"code": "A1"}]
    tgt = [{"code": "B1"}]

    report = reconcile_records(src, tgt, cfg)
    assert report.missing_target_count == 1
    assert report.extra_target_count == 1