# ============================================================================
# File Path: core_policy/budget.py
# Module: Kiem Soat Token Va So Luot Goi Theo Buoc / Luot / Nhiem Vu
# Linked Files: core_policy/loader.py,
#               core_policy/gateway.py
# Purpose: Uoc luong va theo doi input_tokens, output_tokens, total_tokens,
#          so lan goi LLM, phat canh bao gan nguong va chan khi vuot ngan sach.
# ============================================================================

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from .loader import BudgetConfig

logger = logging.getLogger(__name__)


def uoc_luong_token(van_ban: str | None) -> int:
    """Uoc luong token an toan cho tieng Viet, JSON va ma nguon."""
    if not van_ban:
        return 0
    return max(1, int(len(van_ban) / 3.3))


@dataclass
class ThongKeBuoc:
    """Ket qua kiem soat token cho mot buoc goi model."""

    buoc: str
    provider: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    canh_bao: list[str] = field(default_factory=list)
    vuot_nguong: bool = False


@dataclass
class BoKiemSoatNganSach:
    """Quan ly ngan sach token va so luot goi trong mot luot/nhiem vu."""

    cau_hinh: BudgetConfig
    tong_input_tokens: int = 0
    tong_output_tokens: int = 0
    tong_tokens: int = 0
    so_lan_goi_llm: int = 0
    so_luot_thuc_thi: int = 0
    lich_su_buoc: list[ThongKeBuoc] = field(default_factory=list)

    def bat_dau_luot_moi(self) -> tuple[bool, str | None]:
        """Tang bo dem luot va kiem tra gioi han so luot cho mot nhiem vu."""
        self.so_luot_thuc_thi += 1
        if self.so_luot_thuc_thi > self.cau_hinh.max_turns_per_task:
            msg = (
                f"Vuot gioi han so luot cua nhiem vu: "
                f"{self.so_luot_thuc_thi}/{self.cau_hinh.max_turns_per_task}"
            )
            logger.warning(msg)
            return False, msg
        return True, None

    def co_the_goi_llm_tiep(self) -> tuple[bool, str | None]:
        """Kiem tra con du so lan goi LLM va ngan sach tong token luot hay khong."""
        if self.so_lan_goi_llm >= self.cau_hinh.max_llm_calls_per_turn:
            return False, (
                f"Da cham gioi han so lan goi LLM trong luot: "
                f"{self.so_lan_goi_llm}/{self.cau_hinh.max_llm_calls_per_turn}"
            )
        if self.tong_tokens >= self.cau_hinh.max_total_tokens_per_turn:
            return False, (
                f"Da cham gioi han tong token cua luot: "
                f"{self.tong_tokens}/{self.cau_hinh.max_total_tokens_per_turn}"
            )
        return True, None

    def kiem_tra_dau_vao_buoc(self, input_tokens: int) -> tuple[bool, list[str]]:
        """Kiem tra input_tokens cua mot buoc truoc khi goi model."""
        canh_bao: list[str] = []
        nguong_canh_bao = int(self.cau_hinh.max_input_tokens_per_step * self.cau_hinh.warn_ratio)
        if input_tokens > self.cau_hinh.max_input_tokens_per_step:
            canh_bao.append(
                f"input_tokens buoc ({input_tokens}) > gioi han ({self.cau_hinh.max_input_tokens_per_step})"
            )
            return False, canh_bao
        if input_tokens >= nguong_canh_bao:
            canh_bao.append(
                f"input_tokens buoc ({input_tokens}) sap cham nguong ({self.cau_hinh.max_input_tokens_per_step})"
            )
        return True, canh_bao

    def ghi_nhan_buoc(
        self,
        buoc: str,
        provider: str,
        input_tokens: int,
        output_tokens: int,
        canh_bao_dau_vao: list[str] | None = None,
    ) -> ThongKeBuoc:
        """Cong don token va so lan goi sau khi mot buoc hoan tat."""
        self.so_lan_goi_llm += 1
        tong_buoc = input_tokens + output_tokens
        self.tong_input_tokens += input_tokens
        self.tong_output_tokens += output_tokens
        self.tong_tokens += tong_buoc

        canh_bao = list(canh_bao_dau_vao or [])
        vuot = False

        if output_tokens > self.cau_hinh.max_output_tokens_per_step:
            canh_bao.append(
                f"output_tokens ({output_tokens}) > max_output ({self.cau_hinh.max_output_tokens_per_step})"
            )
            vuot = True

        nguong_buoc = int(self.cau_hinh.max_total_tokens_per_step * self.cau_hinh.warn_ratio)
        if tong_buoc > self.cau_hinh.max_total_tokens_per_step:
            canh_bao.append(
                f"total_tokens buoc ({tong_buoc}) > max_step ({self.cau_hinh.max_total_tokens_per_step})"
            )
            vuot = True
        elif tong_buoc >= nguong_buoc:
            canh_bao.append(f"total_tokens buoc ({tong_buoc}) >= nguong canh bao ({nguong_buoc})")

        nguong_luot = int(self.cau_hinh.max_total_tokens_per_turn * self.cau_hinh.warn_ratio)
        if self.tong_tokens > self.cau_hinh.max_total_tokens_per_turn:
            canh_bao.append(
                f"tong_tokens luot ({self.tong_tokens}) > max_turn ({self.cau_hinh.max_total_tokens_per_turn})"
            )
            vuot = True
        elif self.tong_tokens >= nguong_luot:
            canh_bao.append(f"tong_tokens luot ({self.tong_tokens}) >= nguong canh bao ({nguong_luot})")

        ban_ghi = ThongKeBuoc(
            buoc=buoc,
            provider=provider,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=tong_buoc,
            canh_bao=canh_bao,
            vuot_nguong=vuot,
        )
        self.lich_su_buoc.append(ban_ghi)

        if canh_bao:
            logger.warning("Canh bao ngan sach [%s/%s]: %s", buoc, provider, " | ".join(canh_bao))
        else:
            logger.info(
                "Token [%s/%s]: in=%d, out=%d, step_total=%d, turn_total=%d, calls=%d",
                buoc,
                provider,
                input_tokens,
                output_tokens,
                tong_buoc,
                self.tong_tokens,
                self.so_lan_goi_llm,
            )
        return ban_ghi

    def tom_tat(self) -> dict[str, Any]:
        """Tra ve tong hop ngan sach cua luot/nhiem vu hien tai."""
        return {
            "so_luot_thuc_thi": self.so_luot_thuc_thi,
            "max_turns_per_task": self.cau_hinh.max_turns_per_task,
            "so_lan_goi_llm": self.so_lan_goi_llm,
            "max_llm_calls_per_turn": self.cau_hinh.max_llm_calls_per_turn,
            "tong_input_tokens": self.tong_input_tokens,
            "tong_output_tokens": self.tong_output_tokens,
            "tong_tokens": self.tong_tokens,
            "max_total_tokens_per_turn": self.cau_hinh.max_total_tokens_per_turn,
            "so_buoc_co_canh_bao": sum(1 for b in self.lich_su_buoc if b.canh_bao),
        }