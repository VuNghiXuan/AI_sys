# ============================================================================
# File Path: core_policy/loader.py
# Module: Bo Tai Va Xac Thuc Cau Hinh Chien Thuat (YAML + Pydantic)
# Linked Files: config/policy/routing_policy.yaml,
#               core_policy/hardware.py,
#               core_policy/budget.py,
#               core_policy/gateway.py
# Purpose: Doc, xac thuc va tu dong cap nhat (hot-reload) file cau hinh chien
#          thuat dieu phoi, ngan sach token/luot goi va danh sach nha cung cap.
# ============================================================================

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Literal

import yaml
from django.conf import settings
from pydantic import BaseModel, Field, model_validator

logger = logging.getLogger(__name__)


class BudgetConfig(BaseModel):
    """Cau hinh gioi han token va so lan goi theo buoc/luot."""

    max_input_tokens_per_step: int = Field(default=4500, ge=256)
    max_output_tokens_per_step: int = Field(default=2000, ge=128)
    max_total_tokens_per_step: int = Field(default=6500, ge=512)
    max_total_tokens_per_turn: int = Field(default=18000, ge=512)
    warn_ratio: float = Field(default=0.8, gt=0.0, lt=1.0)
    max_llm_calls_per_turn: int = Field(default=6, ge=1)
    max_turns_per_task: int = Field(default=5, ge=1)


class FileLimitConfig(BaseModel):
    """Cau hinh gioi han file dau vao, file lien quan, map va file dau ra."""

    max_input_files: int = Field(default=6, ge=1)
    max_related_files: int = Field(default=4, ge=0)
    max_map_tokens: int = Field(default=1500, ge=128)
    max_output_files_per_turn: int = Field(default=3, ge=1)
    ignore_dirs: list[str] = Field(
        default_factory=lambda: [
            ".venv",
            "venv",
            "__pycache__",
            ".git",
            "node_modules",
            "migrations",
        ]
    )


class HardwareConfig(BaseModel):
    """Cau hinh tu dong nhan dien phan cung va nguong an toan local."""

    auto_detect: bool = True
    min_free_ram_mb: int = Field(default=2048, ge=512)
    local_max_ctx_cap: int = Field(default=8192, ge=1024)


class ProfileConfig(BaseModel):
    """Chien thuat van hanh theo tung profile."""

    allow_paid_fallback: bool = False
    tier_order: list[str] = Field(default_factory=lambda: ["free_cloud", "local_ollama"])
    max_total_tokens_per_step: int | None = Field(default=None, ge=512)
    max_llm_calls_per_turn: int | None = Field(default=None, ge=1)


class ProviderConfig(BaseModel):
    """Thong tin ket noi va gioi han cho mot model/endpoint."""

    name: str
    kind: Literal["openai_compatible", "ollama"]
    base_url: str
    model: str
    api_key_env: str | None = None
    rpm_limit: int = Field(default=30, ge=1)
    daily_token_budget: int = Field(default=200000, ge=1000)
    min_free_ram_mb: int = Field(default=2048, ge=512)
    timeout_s: float = Field(default=40.0, gt=1.0)

    def lay_api_key(self) -> str:
        """Doc API key tu bien moi truong neu co khai bao."""
        if not self.api_key_env:
            return ""
        return os.environ.get(self.api_key_env, "").strip()


class RoutingPolicy(BaseModel):
    """Tong hop toan bo chinh sach chien thuat trong file YAML."""

    active_profile: str = "quality_first_free_first"
    budgets: BudgetConfig = Field(default_factory=BudgetConfig)
    file_limits: FileLimitConfig = Field(default_factory=FileLimitConfig)
    hardware: HardwareConfig = Field(default_factory=HardwareConfig)
    profiles: dict[str, ProfileConfig] = Field(default_factory=dict)
    providers: dict[str, list[ProviderConfig]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def kiem_tra_profile_ton_tai(self) -> "RoutingPolicy":
        """Dam bao profile hien hanh luon ton tai trong danh sach profiles."""
        if not self.profiles:
            self.profiles["quality_first_free_first"] = ProfileConfig(
                allow_paid_fallback=True,
                tier_order=["free_cloud", "local_ollama", "paid_low_cost", "paid_reasoning"],
            )
        if self.active_profile not in self.profiles:
            self.active_profile = next(iter(self.profiles.keys()))
        return self

    def lay_profile_hien_hanh(self) -> ProfileConfig:
        """Tra ve profile dang kich hoat."""
        return self.profiles[self.active_profile]

    def lay_ngan_sach_hieu_luc(self) -> BudgetConfig:
        """Ap ghi de ngan sach cua profile (neu co) len bo budgets goc."""
        prof = self.lay_profile_hien_hanh()
        du_lieu: dict[str, Any] = self.budgets.model_dump()
        if prof.max_total_tokens_per_step is not None:
            du_lieu["max_total_tokens_per_step"] = prof.max_total_tokens_per_step
        if prof.max_llm_calls_per_turn is not None:
            du_lieu["max_llm_calls_per_turn"] = prof.max_llm_calls_per_turn
        return BudgetConfig(**du_lieu)


_DUONG_DAN_CACHE: Path | None = None
_MTIME_CACHE: float = -1.0
_POLICY_CACHE: RoutingPolicy | None = None


def lay_duong_dan_policy(duong_dan_tuy_chon: str | Path | None = None) -> Path:
    """Xac dinh duong dan file routing_policy.yaml."""
    if duong_dan_tuy_chon:
        return Path(duong_dan_tuy_chon).resolve()
    env_path = os.environ.get("VNX_ROUTING_POLICY_PATH", "").strip()
    if env_path:
        return Path(env_path).resolve()
    base_dir = Path(getattr(settings, "BASE_DIR", Path.cwd()))
    return (base_dir / "config" / "policy" / "routing_policy.yaml").resolve()


def tai_cau_hinh_chien_thuat(
    duong_dan_tuy_chon: str | Path | None = None,
    bat_buoc_tai_lai: bool = False,
) -> RoutingPolicy:
    """Tai file YAML chien thuat va tu dong reload khi file thay doi tren dia."""
    global _DUONG_DAN_CACHE, _MTIME_CACHE, _POLICY_CACHE

    duong_dan = lay_duong_dan_policy(duong_dan_tuy_chon)
    if not duong_dan.exists():
        logger.warning("Khong tim thay file policy tai %s, dung cau hinh mac dinh.", duong_dan)
        _POLICY_CACHE = RoutingPolicy()
        return _POLICY_CACHE

    mtime_hien_tai = duong_dan.stat().st_mtime
    if (
        not bat_buoc_tai_lai
        and _POLICY_CACHE is not None
        and _DUONG_DAN_CACHE == duong_dan
        and _MTIME_CACHE == mtime_hien_tai
    ):
        return _POLICY_CACHE

    with duong_dan.open(encoding="utf-8") as tep:
        du_lieu_raw = yaml.safe_load(tep) or {}

    policy = RoutingPolicy.model_validate(du_lieu_raw)
    _DUONG_DAN_CACHE = duong_dan
    _MTIME_CACHE = mtime_hien_tai
    _POLICY_CACHE = policy
    logger.info(
        "Da tai routing policy (%s) profile=%s",
        duong_dan.name,
        policy.active_profile,
    )
    return policy