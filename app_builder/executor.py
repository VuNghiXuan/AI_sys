# ============================================================================
# File Path: app_builder/executor.py
# Module: Bo Thuc Thi Buoc Qua Gateway Va Ghi Tep Co Kiem Soat
# Linked Files: core_policy/loader.py,
#               core_policy/budget.py,
#               core_policy/gateway.py,
#               code_map/context_builder.py,
#               app_builder/planner.py,
#               app_builder/prompt_builder.py
# Purpose: Chay tung buoc trong ke hoach qua BoDieuPhoiGateway, dung prompt
#          theo che do (chi doc/phan tich vs ghi tep) va ghi an toan.
# ============================================================================

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

from code_map.context_builder import GoiNguCanhCode, xay_dung_ngu_canh_code
from core_policy.budget import BoKiemSoatNganSach
from core_policy.gateway import BoDieuPhoiGateway
from core_policy.loader import RoutingPolicy, tai_cau_hinh_chien_thuat

from .planner import KeHoachThucThi, lap_ke_hoach_tac_vu
from .prompt_builder import xay_dung_system_prompt, xay_dung_user_prompt

logger = logging.getLogger(__name__)

MAU_KHOI_TEP = re.compile(
    r"(?:^|\n)(?:#+\s*`?([A-Za-z0-9_./\\-]+\.[A-Za-z0-9]+)`?[^\n]*\n)?```[a-zA-Z0-9_-]*[ \t]*([^\n`]*)\n(.*?)```",
    re.DOTALL,
)
MAU_DUONG_DAN_DONG = re.compile(
    r"(?:file|tep|tệp|path)\s*:\s*`?([A-Za-z0-9_./\\-]+\.[A-Za-z0-9]+)`?",
    re.I,
)


@dataclass
class KetQuaThucThi:
    """Ket qua sau khi thuc thi ke hoach qua gateway va ghi tep (neu co)."""

    ke_hoach: KeHoachThucThi
    ngu_canh: GoiNguCanhCode
    phan_hoi_llm: str
    provider_da_dung: str
    tier_da_dung: str
    tep_da_ghi: list[str] = field(default_factory=list)
    tep_bi_bo_qua_do_gioi_han: list[str] = field(default_factory=list)
    nhat_ky_gateway: list[str] = field(default_factory=list)
    tong_hop_ngan_sach: dict[str, object] = field(default_factory=dict)


def _trich_cac_tep_tu_phan_hoi(phan_hoi: str) -> list[tuple[str, str]]:
    """Trich danh sach (duong_dan_tuong_doi, noi_dung_ma) tu cac khoi ```."""
    ds: list[tuple[str, str]] = []
    for match in MAU_KHOI_TEP.finditer(phan_hoi or ""):
        ten_tieu_de = (match.group(1) or "").strip()
        ghi_chu_dong = (match.group(2) or "").strip()
        noi_dung = (match.group(3) or "").strip("\r\n")
        if not noi_dung:
            continue

        duong_dan = ""
        m_dong = MAU_DUONG_DAN_DONG.search(ghi_chu_dong)
        if m_dong:
            duong_dan = m_dong.group(1).strip()
        elif ten_tieu_de:
            duong_dan = ten_tieu_de
        else:
            dong_dau = noi_dung.splitlines()[0] if noi_dung.splitlines() else ""
            m_dau = MAU_DUONG_DAN_DONG.search(dong_dau)
            if m_dau:
                duong_dan = m_dau.group(1).strip()

        duong_dan_sach = duong_dan.lstrip("/\\").replace("\\", "/")
        if duong_dan_sach and ".." not in Path(duong_dan_sach).parts:
            ds.append((duong_dan_sach, noi_dung + "\n"))
    return ds


def _ghi_tep_an_toan(
    goc_du_an: Path,
    cac_tep: list[tuple[str, str]],
    max_output_files: int,
) -> tuple[list[str], list[str]]:
    """Ghi toi da max_output_files tep vao trong goc_du_an, chan path traversal."""
    goc_resolved = goc_du_an.resolve()
    da_ghi: list[str] = []
    bi_bo_qua: list[str] = []

    for rel, noi_dung in cac_tep:
        if len(da_ghi) >= max_output_files:
            bi_bo_qua.append(rel)
            continue
        dich = (goc_resolved / rel).resolve()
        if goc_resolved != dich and goc_resolved not in dich.parents:
            bi_bo_qua.append(rel)
            continue
        dich.parent.mkdir(parents=True, exist_ok=True)
        dich.write_text(noi_dung, encoding="utf-8")
        da_ghi.append(rel)

    return da_ghi, bi_bo_qua


def thuc_thi_yeu_cau(
    goc_du_an: str | Path,
    yeu_cau: str,
    ghi_ra_dia: bool = False,
    policy: RoutingPolicy | None = None,
    gateway: BoDieuPhoiGateway | None = None,
    ngan_sach: BoKiemSoatNganSach | None = None,
) -> KetQuaThucThi:
    """Thuc thi lap ke hoach, gom ngu canh code, goi model qua gateway va ghi tep."""
    goc = Path(goc_du_an).resolve()
    cfg = policy or tai_cau_hinh_chien_thuat()
    budget = ngan_sach or BoKiemSoatNganSach(cfg.lay_ngan_sach_hieu_luc())
    budget.bat_dau_luot_moi()

    ke_hoach = lap_ke_hoach_tac_vu(yeu_cau, policy=cfg, file_limits=cfg.file_limits)
    ngu_canh = xay_dung_ngu_canh_code(goc, yeu_cau, file_limits=cfg.file_limits)

    quy_tac_ghi = (
        f"Chi tao hoac sua toi da {ke_hoach.max_output_files_per_turn} tep trong mot luot. "
        "Khi xuat ma cho tep, ghi ro duong dan o dong dau khoi ma dang "
        "`# File Path: duong/dan/tep.py`."
        if ghi_ra_dia
        else ""
    )
    sys_prompt = xay_dung_system_prompt(
        ghi_ra_dia=ghi_ra_dia,
        bo_sung_quy_tac=quy_tac_ghi,
    )
    user_prompt = xay_dung_user_prompt(
        yeu_cau=yeu_cau,
        ngu_canh=ngu_canh,
        ke_hoach=ke_hoach,
        ghi_ra_dia=ghi_ra_dia,
    )

    gw = gateway or BoDieuPhoiGateway(policy=cfg)
    kq_model = gw.goi(
        buoc="thuc_thi_chinh",
        prompt=user_prompt,
        system_prompt=sys_prompt,
        ngan_sach=budget,
    )

    tep_trich = _trich_cac_tep_tu_phan_hoi(kq_model.noi_dung)
    da_ghi: list[str] = []
    bi_bo_qua: list[str] = []
    if ghi_ra_dia and tep_trich:
        da_ghi, bi_bo_qua = _ghi_tep_an_toan(goc, tep_trich, ke_hoach.max_output_files_per_turn)

    return KetQuaThucThi(
        ke_hoach=ke_hoach,
        ngu_canh=ngu_canh,
        phan_hoi_llm=kq_model.noi_dung,
        provider_da_dung=kq_model.provider_ten,
        tier_da_dung=kq_model.tier,
        tep_da_ghi=da_ghi,
        tep_bi_bo_qua_do_gioi_han=bi_bo_qua,
        nhat_ky_gateway=kq_model.nhat_ky_chuyen_nguon,
        tong_hop_ngan_sach=budget.tom_tat(),
    )