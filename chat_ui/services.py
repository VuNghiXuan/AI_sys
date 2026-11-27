# ============================================================================
# File Path: chat_ui/services.py
# Module: Tang Dieu Phoi Nghiep Vu Cho Giao Dien Chat Va API Django
# Linked Files: core_policy/loader.py,
#               core_policy/hardware.py,
#               core_policy/budget.py,
#               core_policy/gateway.py,
#               code_map/scanner.py,
#               app_builder/executor.py,
#               app_builder/verifier.py
# Purpose: Xu ly prompt tu giao dien: uu tien truy van metadata/tep thuc te
#          qua scanner, rang buoc intent ro rang truoc khi goi app_builder.
# ============================================================================

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from django.conf import settings

from app_builder.executor import thuc_thi_yeu_cau
from app_builder.verifier import kiem_chung_tep_da_ghi
from code_map.scanner import quet_danh_sach_tep, tim_tep_vuot_nguong_dong
from core_policy.budget import BoKiemSoatNganSach, uoc_luong_token
from core_policy.gateway import BoDieuPhoiGateway, LoiHetNganSachHoacFallback
from core_policy.hardware import nhan_dien_phan_cung
from core_policy.loader import tai_cau_hinh_chien_thuat

logger = logging.getLogger(__name__)

MAU_NGUONG_DONG = re.compile(r"(?:>|>=|trên|quá|vượt|hơn)\s*(\d+)\s*dòng", re.I)
MAU_DUOI_TEP = re.compile(
    r"(?:\.|^|\s)(html|htm|css|js|jsx|ts|tsx|py|json|sql|md|txt|csv)(?=$|\s|,|;)",
    re.I,
)
MAU_LIET_KE_TEP = re.compile(
    r"(liệt\s*kê|danh\s*sách|có\s+(?:những\s+)?(?:file|tệp)|(?:những\s+|các\s+)?(?:file|tệp)\s+(?:nào|có\s+(?:trong|liên\s+quan)))",
    re.I,
)
MAU_THONG_SO_MAY = re.compile(
    r"(cấu\s*hình\s*máy|phần\s*cứng|\bcpu\b|\bram\b|\bvram\b|\bgpu\b)",
    re.I,
)
MAU_YEU_CAU_GHI_CODE = re.compile(
    r"(tạo\s+(?:file|tệp|module|code|mã)|viết\s+(?:file|tệp|module|code|mã)|sửa\s+(?:file|tệp|code)|chỉnh\s*sửa|cập\s*nhật\s+(?:file|tệp|code)|thêm\s+(?:file|tệp|hàm|class)|xóa\s+(?:file|tệp)|refactor|\bgenerate\b|\bcreate\b)",
    re.I,
)
MAU_CO_YEU_CAU_PHAN_TICH = re.compile(
    r"(phân\s*tích|mô\s*tả\s*chức\s*năng|giải\s*thích|đánh\s*giá)",
    re.I,
)


def _lay_goc_du_an(goc_tuy_chon: str | Path | None = None) -> Path:
    """Lay thu muc goc du an can quet/thao tac."""
    if goc_tuy_chon:
        return Path(goc_tuy_chon).resolve()
    return Path(getattr(settings, "BASE_DIR", Path.cwd())).resolve()


def _lay_phan_cung_dict(policy) -> dict[str, Any] | None:
    """Lay thong tin phan cung hien tai neu ham ho tro sang_dict()."""
    try:
        ho_so = nhan_dien_phan_cung(policy.hardware)
        if hasattr(ho_so, "sang_dict"):
            return ho_so.sang_dict()
        return {
            "he_dieu_hanh": ho_so.he_dieu_hanh,
            "cpu_logic": ho_so.cpu_logic,
            "cpu_vat_ly": ho_so.cpu_vat_ly,
            "tong_ram_mb": ho_so.tong_ram_mb,
            "ram_kha_dung_mb": ho_so.ram_kha_dung_mb,
            "ram_su_dung_phan_tram": ho_so.ram_su_dung_phan_tram,
            "goi_y_num_thread": ho_so.goi_y_num_thread,
            "goi_y_num_ctx": ho_so.goi_y_num_ctx,
            "gpus": [g.__dict__ for g in getattr(ho_so, "gpu_ds", [])],
        }
    except Exception as exc:
        logger.debug("Bo qua loi lay phan cung: %s", exc)
        return None


def _lay_danh_sach_tep_thuc_te(goc: Path, prompt: str, policy) -> tuple[list[str], str]:
    """Quet danh sach tep thuc te theo duoi neu nguoi dung co chi dinh."""
    cac_duoi = [
        ("html" if m.group(1).lower() == "htm" else m.group(1).lower())
        for m in MAU_DUOI_TEP.finditer(prompt)
    ]
    duoi_duy_nhat = list(dict.fromkeys(cac_duoi))
    ds_tep = quet_danh_sach_tep(
        goc,
        duoi_file=duoi_duy_nhat or None,
        gioi_han_tep=120,
        file_limits=policy.file_limits,
    )
    if not ds_tep:
        mo_ta_duoi = ", ".join(f".{d}" for d in duoi_duy_nhat) if duoi_duy_nhat else "phù hợp"
        return [], f"Không tìm thấy tệp nào thuộc loại {mo_ta_duoi} trong dự án."

    tieu_de = (
        f"Danh sách tệp ({', '.join('.' + d for d in duoi_duy_nhat)}) — {len(ds_tep)} tệp:"
        if duoi_duy_nhat
        else f"Danh sách tệp trong dự án — {len(ds_tep)} tệp:"
    )
    ds_rel = [item.duong_dan_tuong_doi for item in ds_tep]
    noi_dung = tieu_de + "\n" + "\n".join(
        f"- `{item.duong_dan_tuong_doi}` ({item.so_dong} dòng)" for item in ds_tep
    )
    return ds_rel, noi_dung


def _xu_ly_nhanh_metadata(goc: Path, prompt: str, policy) -> dict[str, Any] | None:
    """Tra loi truc tiep tu metadata tep thuc te hoac phan cung neu khop mau."""
    m_dong = MAU_NGUONG_DONG.search(prompt)
    if m_dong:
        nguong = int(m_dong.group(1))
        ds_vuot = tim_tep_vuot_nguong_dong(goc, nguong_dong=nguong, file_limits=policy.file_limits)
        if not ds_vuot:
            noi_dung = f"Không có tệp `.py` nào vượt quá {nguong} dòng."
        else:
            dong_kq = [f"Các tệp có số dòng lớn hơn {nguong} ({len(ds_vuot)} tệp):"]
            dong_kq.extend(f"- `{item.duong_dan_tuong_doi}`: {item.so_dong} dòng" for item in ds_vuot)
            noi_dung = "\n".join(dong_kq)
        t_in = uoc_luong_token(prompt)
        t_out = uoc_luong_token(noi_dung)
        return {
            "che_do": "scanner_truc_tiep",
            "provider": "local_scanner",
            "tier": "deterministic",
            "noi_dung": noi_dung,
            "token": {"input": t_in, "output": t_out, "tong": t_in + t_out},
            "canh_bao": [],
        }

    # Chi tra nhanh scanner khi la cau hoi liet ke thuan tuy (khong kem phan tich sau)
    if MAU_LIET_KE_TEP.search(prompt) and not MAU_CO_YEU_CAU_PHAN_TICH.search(prompt):
        _, noi_dung = _lay_danh_sach_tep_thuc_te(goc, prompt, policy)
        t_in = uoc_luong_token(prompt)
        t_out = uoc_luong_token(noi_dung)
        return {
            "che_do": "scanner_truc_tiep",
            "provider": "local_scanner",
            "tier": "deterministic",
            "noi_dung": noi_dung,
            "token": {"input": t_in, "output": t_out, "tong": t_in + t_out},
            "canh_bao": [],
        }

    if MAU_THONG_SO_MAY.search(prompt) and "file" not in prompt.lower() and "tệp" not in prompt.lower():
        ho_so = nhan_dien_phan_cung(policy.hardware)
        dong_may = [
            "Thông số phần cứng & cấu hình đề xuất:",
            f"- Hệ điều hành: {ho_so.he_dieu_hanh}",
            f"- CPU: {ho_so.cpu_logic} luồng ({ho_so.cpu_vat_ly} nhân vật lý)",
            f"- RAM: trống {ho_so.ram_kha_dung_mb} MB / tổng {ho_so.tong_ram_mb} MB ({ho_so.ram_su_dung_phan_tram}%)",
            f"- Đề xuất local: `num_thread={ho_so.goi_y_num_thread}`, `num_ctx={ho_so.goi_y_num_ctx}`",
        ]
        for gpu in ho_so.gpu_ds:
            dong_may.append(f"- GPU: {gpu.ten} (VRAM trống/tổng: {gpu.trong_vram_mb}/{gpu.tong_vram_mb} MB)")
        noi_dung = "\n".join(dong_may)
        t_in = uoc_luong_token(prompt)
        t_out = uoc_luong_token(noi_dung)
        return {
            "che_do": "hardware_probe",
            "provider": "local_hardware",
            "tier": "deterministic",
            "noi_dung": noi_dung,
            "token": {"input": t_in, "output": t_out, "tong": t_in + t_out},
            "canh_bao": [],
        }

    return None


def _chuan_hoa_yeu_cau_theo_intent(goc: Path, prompt: str, ghi_tep: bool, policy) -> str:
    """Nêu rõ phạm vi chỉ đọc/phân tích và bơm danh sách tệp thật nếu có hỏi liệt kê."""
    bo_sung: list[str] = []
    if MAU_LIET_KE_TEP.search(prompt):
        ds_rel, _ = _lay_danh_sach_tep_thuc_te(goc, prompt, policy)
        if ds_rel:
            ds_gon = "\n".join(f"- {p}" for p in ds_rel[:60])
            bo_sung.append(f"Danh sach tep thuc te trong repo:\n{ds_gon}")

    if not ghi_tep and not MAU_YEU_CAU_GHI_CODE.search(prompt):
        bo_sung.append(
            "[Intent: CHI DOC / PHAN TICH / TRA LOI — Khong tao file moi, khong sua file, "
            "khong tu bia ten file hoac ham khong co trong ngu canh. Tra loi ngan gon, ro rang.]"
        )

    if not bo_sung:
        return prompt
    return f"{prompt}\n\n" + "\n\n".join(bo_sung)


def xu_ly_prompt_chat(
    prompt: str,
    ghi_tep: bool = False,
    goc_du_an: str | Path | None = None,
    gateway: BoDieuPhoiGateway | None = None,
) -> dict[str, Any]:
    """Dieu phoi mot luot prompt tu UI/API va tra ve ket qua kem thong ke."""
    prompt_sach = (prompt or "").strip()
    policy = tai_cau_hinh_chien_thuat(bat_buoc_tai_lai=True)
    goc = _lay_goc_du_an(goc_du_an)
    phan_cung = _lay_phan_cung_dict(policy)

    if not prompt_sach:
        return {
            "che_do": "bo_trong",
            "provider": "-",
            "tier": "-",
            "noi_dung": "Vui lòng nhập yêu cầu.",
            "token": {"input": 0, "output": 0, "tong": 0},
            "canh_bao": [],
            "kiem_chung": None,
            "phan_cung": phan_cung,
        }

    nhanh = _xu_ly_nhanh_metadata(goc, prompt_sach, policy)
    if nhanh is not None:
        nhanh["profile"] = policy.active_profile
        nhanh["kiem_chung"] = None
        nhanh["phan_cung"] = phan_cung
        return nhanh

    budget = BoKiemSoatNganSach(policy.lay_ngan_sach_hieu_luc())
    yeu_cau_dieu_phoi = _chuan_hoa_yeu_cau_theo_intent(goc, prompt_sach, ghi_tep, policy)
    try:
        kq = thuc_thi_yeu_cau(
            goc_du_an=goc,
            yeu_cau=yeu_cau_dieu_phoi,
            ghi_ra_dia=ghi_tep,
            policy=policy,
            gateway=gateway,
            ngan_sach=budget,
        )
    except LoiHetNganSachHoacFallback as exc:
        logger.warning("Khong the thuc thi qua gateway: %s", exc)
        return {
            "che_do": "chan_ngan_sach_hoac_loi_nguon",
            "provider": "-",
            "tier": "-",
            "profile": policy.active_profile,
            "noi_dung": f"Không thể hoàn tất yêu cầu: {exc}",
            "token": budget.tom_tat(),
            "canh_bao": [str(exc)],
            "kiem_chung": None,
            "phan_cung": phan_cung,
        }

    bao_cao_kc = None
    if kq.tep_da_ghi or kq.tep_bi_bo_qua_do_gioi_han:
        kc = kiem_chung_tep_da_ghi(
            goc_du_an=goc,
            danh_sach_tep=kq.tep_da_ghi,
            tep_bi_bo_qua=kq.tep_bi_bo_qua_do_gioi_han,
        )
        bao_cao_kc = {
            "dat_kiem_chung": kc.dat_kiem_chung,
            "so_tep_da_kiem_tra": kc.so_tep_da_kiem_tra,
            "thong_ke_tep": kc.thong_ke_tep,
            "cac_loi": [loi.__dict__ for loi in kc.cac_loi],
        }

    canh_bao_ds: list[str] = list(kq.nhat_ky_gateway)
    for b in budget.lich_su_buoc:
        canh_bao_ds.extend(b.canh_bao)

    return {
        "che_do": "app_builder_gateway",
        "provider": kq.provider_da_dung,
        "tier": kq.tier_da_dung,
        "profile": kq.ke_hoach.profile,
        "noi_dung": kq.phan_hoi_llm,
        "tep_dich": kq.ngu_canh.tep_dich,
        "tep_lien_quan": kq.ngu_canh.tep_lien_quan,
        "tep_da_ghi": kq.tep_da_ghi,
        "token": kq.tong_hop_ngan_sach,
        "canh_bao": list(dict.fromkeys(canh_bao_ds)),
        "kiem_chung": bao_cao_kc,
        "phan_cung": phan_cung,
    }