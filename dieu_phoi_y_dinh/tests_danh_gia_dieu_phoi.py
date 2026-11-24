# ============================================================================
# File Path: dieu_phoi_y_dinh/tests_danh_gia_dieu_phoi.py
# Module: Kiem Thu & Danh Gia Toc Do, Y Dinh, Model Cua He Thong
# Linked Files: dieu_phoi_nhanh.py, cau_hinh_ollama.py, tach_da_y_dinh.py
# Purpose: Chay tap prompt mau qua luong dieu phoi that de do thoi gian,
#          kiem tra y dinh/nhanh khop va danh gia muc do hop ly cua model.
# ============================================================================

import time
from django.test import TestCase

from dieu_phoi_y_dinh.dich_vu.cau_hinh_ollama import lay_cau_hinh_hien_tai
from dieu_phoi_y_dinh.dich_vu.dieu_phoi_nhanh import xu_ly_prompt_da_y_dinh

CAC_PROMPT_TEST = [
    ("cau_hinh_model", "Máy tao đang xài cấu hình gì các models đang xử dụng"),
    ("tong_hop_thanh_phan", "lập bảng tổng hợp thành phần app, folder, file, hàm, class"),
    ("liet_ke_app", "kể tên các app và chức năng từng app"),
    ("so_sanh_file", "so sánh chức năng và liên kết giữa dieu_phoi_nhanh.py và phan_tich_nhanh.py"),
    ("chat_ngan", "tóm tắt 2 ý ngắn gọn về lợi ích của việc tách file dưới 300 dòng"),
    ("phan_tich_bang", "đề xuất phương án tính lương nhân sự theo ca và sản lượng, lập bảng"),
    ("goi_y_toi_uu", "gợi ý 2 cách tối ưu hiệu năng truy vấn cho hệ thống bán hàng khách đặt"),
    ("da_y_dinh", "kể tên các app và gợi ý 2 cách tối ưu hiệu năng truy vấn"),
    ("du_lieu_ngoai", "phân tích chứng khoán hôm nay"),
]


def _danh_gia_luot(nhan: str, thoi_gian_s: float, kq: dict, cfg: dict) -> str:
    """Dua ra nhan xet ngan gon ve toc do va cach chon model cho tung prompt."""
    y_dinh = kq.get("y_dinh") or ""
    cac_nhanh = kq.get("cac_nhanh") or []
    loai_cac_nhanh = [str(n.get("loai_nhanh") or "") for n in cac_nhanh]
    dung_registry = any(str(n.get("nhan_nhanh", "")).startswith("Registry:") for n in cac_nhanh)

    if dung_registry and len(cac_nhanh) == 1:
        return "OK — Khớp Registry trực tiếp, không tốn thời gian suy luận LLM."
    if dung_registry and len(cac_nhanh) > 1:
        return f"OK ({thoi_gian_s:.2f}s) — Khớp Registry + tách {len(cac_nhanh)} nhánh ({', '.join(loai_cac_nhanh)})."
    if nhan == "goi_y_toi_uu":
        trang_thai = "OK" if "phan_tich_nghiep_vu" in loai_cac_nhanh else "Cảnh báo (vẫn vào db_file)"
        return f"{trang_thai} ({thoi_gian_s:.2f}s) — Nhánh: {', '.join(loai_cac_nhanh)}."
    if nhan == "du_lieu_ngoai":
        return (
            f"Lưu ý ({thoi_gian_s:.2f}s) — Chưa có nguồn dữ liệu real-time; "
            "nên cân nhắc chặn sớm thay vì để model sinh câu từ chối dài."
        )
    if thoi_gian_s > 8.0:
        return (
            f"Chậm ({thoi_gian_s:.2f}s) — Cần kiểm tra tải CPU/RAM hoặc model đang nạp "
            f"(nhanh={cfg.get('model_nhanh')}, code={cfg.get('model_code')})."
        )
    if nhan in {"chat_ngan", "phan_tich_bang", "da_y_dinh"}:
        return f"Ổn ({thoi_gian_s:.2f}s) — Dùng '{cfg.get('model_nhanh')}' cho phản hồi/gợi ý gọn."
    return f"Ổn ({thoi_gian_s:.2f}s) — Ý định: {y_dinh}."


class DanhGiaDieuPhoiTest(TestCase):
    """Chay bo kiem thu danh gia luong dieu phoi, toc do va phan bo model."""

    def test_danh_gia_toan_bo_y_dinh(self):
        cfg = lay_cau_hinh_hien_tai()
        print("\n=== CẤU HÌNH HIỆN TẠI ===")
        print(
            f"GPU={cfg.get('has_gpu')} | num_thread={cfg.get('num_thread')} | "
            f"llm_song_song={cfg.get('gioi_han_llm')} | model_nhanh={cfg.get('model_nhanh')} | "
            f"model_code={cfg.get('model_code')}"
        )
        print("\n=== KẾT QUẢ TEST TỪNG PROMPT ===")

        for nhan, prompt in CAC_PROMPT_TEST:
            t0 = time.perf_counter()
            kq = xu_ly_prompt_da_y_dinh(prompt, bo_qua_cache=True)
            dt = time.perf_counter() - t0

            self.assertTrue(kq.get("ok"), f"Lỗi prompt [{nhan}]: {kq.get('error')}")
            cac_nhanh = kq.get("cac_nhanh") or []
            nhan_nhanh = ", ".join(n.get("nhan_nhanh", "") for n in cac_nhanh)
            do_dai_kq = sum(len(str(n.get("ket_qua") or "")) for n in cac_nhanh)
            nhan_xet = _danh_gia_luot(nhan, dt, kq, cfg)

            print(
                f"[{nhan}] {dt:.2f}s | nhánh={len(cac_nhanh)} ({nhan_nhanh}) | "
                f"ký_tự={do_dai_kq} | {nhan_xet}"
            )