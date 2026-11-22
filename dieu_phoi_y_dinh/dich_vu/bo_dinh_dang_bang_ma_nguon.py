# ============================================================================
# File Path: dieu_phoi_y_dinh/dich_vu/bo_dinh_dang_bang_ma_nguon.py
# Module: Bo Dinh Dang Bang & Ket Qua Tra Cuu Ma Nguon
# Linked Files: chi_muc_ma_nguon.py
# Purpose: Chuyen doi du lieu chi muc AST/lien ket thanh bang Markdown va danh sach
#          de doc cho giao dien hoi thoai.
# ============================================================================

from pathlib import Path
import re


def _sach_o_bang(gia_tri: str) -> str:
    """Chuan hoa noi dung 1 o bang Markdown, tranh lech cot."""
    return re.sub(r"\s+", " ", str(gia_tri or "").replace("|", "/")).strip()


def _dinh_dang_tham_so(tham_so: list[str]) -> str:
    """Gop danh sach tham so ham an toan cho f-string."""
    return ", ".join(tham_so) if tham_so else "-"


def _tao_bang_tong_hop_thanh_phan(chi_muc: dict) -> str:
    """Tao bang Markdown tong hop cac thanh phan app, folder, file, ham, bien/class."""
    cac_file = chi_muc.get("files", {})
    ds_ham = chi_muc.get("ham", [])
    ds_bien = chi_muc.get("bien", [])

    apps = sorted({
        p.split("/", 1)[0]
        for p in cac_file
        if "/" in p and (p.split("/", 1)[0] not in {"he_thong", "lat_cat_da_tao", "static", "templates"})
    })
    folders = sorted({str(Path(p).parent) for p in cac_file if str(Path(p).parent) != "."})
    files = sorted(cac_file.keys())

    mau_app = _sach_o_bang(", ".join(f"`{a}`" for a in apps[:8]) or "-")
    mau_folder = _sach_o_bang(", ".join(f"`{fd}`" for fd in folders[:8]) or "-")
    mau_file = _sach_o_bang(", ".join(f"`{Path(fl).name}`" for fl in files[:8]) or "-")
    mau_ham = _sach_o_bang(", ".join(f"`{h['ten']}`" for h in ds_ham[:8]) or "-")
    mau_bien = _sach_o_bang(", ".join(f"`{b['ten']}`" for b in ds_bien[:8]) or "-")

    dong = [
        "📊 Bảng tổng hợp thành phần hệ thống:",
        "| Thành phần | Số lượng | Tiêu biểu / Chi tiết |",
        "| --- | --- | --- |",
        f"| **App** | {len(apps)} | {mau_app} |",
        f"| **Folder** | {len(folders)} | {mau_folder} |",
        f"| **File** | {len(files)} | {mau_file} |",
        f"| **Hàm** | {len(ds_ham)} | {mau_ham} |",
        f"| **Biến / Class** | {len(ds_bien)} | {mau_bien} |",
        "",
        "### Chi tiết từng nhóm (rút gọn dễ đọc)",
        "- **App (" + str(len(apps)) + "):** " + (", ".join(f"`{a}`" for a in apps) or "-"),
        "- **Folder (" + str(len(folders)) + "):** " + (", ".join(f"`{fd}`" for fd in folders[:15]) or "-"),
        "- **File (" + str(len(files)) + "):** " + (", ".join(f"`{fl}`" for fl in files[:15]) or "-"),
        "- **Hàm (" + str(len(ds_ham)) + "):** " + (", ".join(f"`{h['ten']}`" for h in ds_ham[:20]) or "-"),
        "- **Biến / Class (" + str(len(ds_bien)) + "):** " + (", ".join(f"`{b['ten']}`" for b in ds_bien[:20]) or "-"),
    ]
    return "\n".join(dong)


def _tao_bang_danh_sach_ham(ds_ham: list[dict], gioi_han: int = 50) -> str:
    """Tao bang Markdown liet ke danh sach ham."""
    dong = [
        f"📊 Bảng danh sách hàm ({min(len(ds_ham), gioi_han)}/{len(ds_ham)} hàm):",
        "| Hàm | File | Tham số | Chức năng |",
        "| --- | --- | --- | --- |",
    ]
    for h in ds_ham[:gioi_han]:
        ten_ham = _sach_o_bang(h.get("ten", ""))
        ten_file = _sach_o_bang(Path(str(h.get("file", ""))).name)
        ts = _sach_o_bang(_dinh_dang_tham_so(h.get("tham_so", [])))
        mo_ta = _sach_o_bang(h.get("mo_ta") or "Hàm xử lý")
        dong.append(f"| `{ten_ham}` | `{ten_file}` | `{ts}` | {mo_ta} |")
    return "\n".join(dong)


def _tao_bang_so_sanh_file_va_ham(cac_file: dict[str, dict], ds_file: list[str]) -> str:
    """Tao bang Markdown so sanh vai tro file va liet ke chuc nang tung ham cua moi file."""
    dong_bang = [
        "📊 Bảng so sánh file hệ thống:",
        "| File | Chức năng chính | Số hàm | Biến/Class tiêu biểu | Liên kết đi ra |",
        "| --- | --- | --- | --- | --- |",
    ]
    chi_tiet_ham: list[str] = ["", "⚙️ Chức năng từng hàm để đối chiếu:"]

    for f in ds_file[:8]:
        tt = cac_file[f]
        mo_ta = _sach_o_bang(str(tt.get("mo_ta", ""))[:75])
        so_ham = len(tt.get("ham", []))
        bien_tieu_bieu = _sach_o_bang(", ".join(b["ten"] for b in tt.get("bien", [])[:4]) or "-")
        lk_ra = _sach_o_bang(", ".join(Path(x).name for x in tt.get("lien_ket_di_ra", [])[:4]) or "-")
        dong_bang.append(f"| `{Path(f).name}` | {mo_ta} | {so_ham} | {bien_tieu_bieu} | {lk_ra} |")

        chi_tiet_ham.append(f"### `{Path(f).name}` ({f})")
        cac_ham = tt.get("ham", [])
        if cac_ham:
            for h in cac_ham:
                ts = ", ".join(h.get("tham_so", []))
                chi_tiet_ham.append(f"- `{h['ten']}({ts})` (dòng {h['dong']}): {h.get('mo_ta') or 'Hàm xử lý'}")
        else:
            chi_tiet_ham.append("- Không có hàm top-level.")

    return "\n".join(dong_bang + chi_tiet_ham)


def _tao_bang_so_sanh_ham(ham_trung: list[dict]) -> str:
    """Tao bang Markdown so sanh chuc nang giua cac ham duoc nhac den."""
    dong = [
        "📊 Bảng so sánh chức năng các hàm:",
        "| Hàm | File | Tham số | Chức năng |",
        "| --- | --- | --- | --- |",
    ]
    for h in ham_trung[:10]:
        ts = _sach_o_bang(_dinh_dang_tham_so(h.get("tham_so", [])))
        mo_ta = _sach_o_bang(h.get("mo_ta") or "Hàm xử lý")
        ten_ham = _sach_o_bang(h["ten"])
        dong.append(f"| `{ten_ham}` | `{Path(h['file']).name}` | `{ts}` | {mo_ta} |")
    return "\n".join(dong)


def _dinh_dang_mo_ta_tung_file(chi_muc: dict, goi_nhieu_ham: bool = False) -> str:
    """Liet ke de doc tung file kem chuc nang va danh sach ham/bien."""
    cac_file = chi_muc.get("files", {})
    if not cac_file:
        return "Không tìm thấy file mã nguồn nào để mô tả."

    dong_ket_qua: list[str] = [f"📚 Chức năng từng file ({len(cac_file)} file):"]
    for duong_dan, tt in list(cac_file.items())[:25]:
        dong_ket_qua.append(f"### `{duong_dan}` ({tt.get('so_dong', 0)} dòng)")
        dong_ket_qua.append(f"- Chức năng: {tt.get('mo_ta', '')}")
        cac_ham = tt.get("ham", [])
        if cac_ham:
            dong_ket_qua.append("- Các hàm:")
            for h in cac_ham[: 12 if goi_nhieu_ham else 6]:
                ts = ", ".join(h.get("tham_so", []))
                mo_ta_h = f": {h['mo_ta']}" if h.get("mo_ta") else ""
                dong_ket_qua.append(f"  * `{h['ten']}({ts})` (dòng {h['dong']}){mo_ta_h}")
        else:
            dong_ket_qua.append("- Các hàm: không có hàm riêng")
        cac_bien = tt.get("bien", [])
        if cac_bien:
            dong_ket_qua.append("- Biến / Class: " + ", ".join(f"`{b['ten']}`" for b in cac_bien[:8]))
        dong_ket_qua.append("")

    return "\n".join(dong_ket_qua).strip()


def _dinh_dang_quan_he_lien_ket(chi_muc: dict, file_khop: list[str]) -> str:
    """Tra cuu file nao lien quan file nao (2 chieu) va kem bang so sanh neu nhieu file."""
    cac_file = chi_muc.get("files", {})
    if len(file_khop) == 1:
        f = file_khop[0]
        tt = cac_file[f]
        ra = ", ".join(f"`{x}`" for x in tt.get("lien_ket_di_ra", [])) or "không có"
        vao = ", ".join(f"`{x}`" for x in tt.get("lien_ket_di_vao", [])) or "không có"
        return f"🔗 Quan hệ liên kết của `{f}`:\n- Phụ thuộc / gọi tới: {ra}\n- Được gọi / liên kết từ: {vao}"

    if len(file_khop) >= 2:
        dong = ["🔗 Liên kết giữa các file được nhắc tới:"]
        for f in file_khop[:8]:
            tt = cac_file[f]
            ra = ", ".join(Path(x).name for x in tt.get("lien_ket_di_ra", [])) or "-"
            vao = ", ".join(Path(x).name for x in tt.get("lien_ket_di_vao", [])) or "-"
            dong.append(f"- `{f}` -> gọi tới: {ra} | được gọi từ: {vao}")
        dong.append("")
        dong.append(_tao_bang_so_sanh_file_va_ham(cac_file, file_khop))
        return "\n".join(dong)

    dong = ["🔗 Bản đồ liên kết giữa các file:"]
    for duong_dan, tt in cac_file.items():
        ra = tt.get("lien_ket_di_ra", [])
        if ra:
            dong.append(f"- `{duong_dan}` -> liên quan: {', '.join(f'`{x}`' for x in ra[:6])}")
    return "\n".join(dong[:30]) if len(dong) > 1 else "Chưa phát hiện liên kết giữa các file."