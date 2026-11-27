# ============================================================================
# File Path: core_policy/gateway.py
# Module: Bo Dieu Phoi Goi Model Va Tu Dong Chuyen Nguon (Fallback Gateway)
# Linked Files: core_policy/loader.py,
#               core_policy/hardware.py,
#               core_policy/budget.py
# Purpose: Thuc thi goi model theo thu tu tier/profile trong cau hinh,
#          kiem tra RAM/ngan sach/RPM, tu dong chuyen API khi gap 429,
#          timeout, het han muc ngay hoac loi ket noi.
# ============================================================================

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

import requests

from .budget import BoKiemSoatNganSach, ThongKeBuoc, uoc_luong_token
from .hardware import HoSoPhanCung, nhan_dien_phan_cung
from .loader import ProviderConfig, RoutingPolicy, tai_cau_hinh_chien_thuat

logger = logging.getLogger(__name__)

PAID_TIERS = frozenset({"paid_low_cost", "paid_reasoning"})


@dataclass
class KetQuaGoiModel:
    """Ket qua tra ve sau khi goi thanh cong qua gateway."""

    noi_dung: str
    provider_ten: str
    tier: str
    model: str
    thong_ke_buoc: ThongKeBuoc
    nhat_ky_chuyen_nguon: list[str] = field(default_factory=list)


class LoiHetNganSachHoacFallback(RuntimeError):
    """Ngoai le khi khong con nguon nao kha dung hoac vuot ngan sach."""


class BoDieuPhoiGateway:
    """Quan ly trang thai RPM/token ngay/cooldown va thuc thi fallback theo policy."""

    def __init__(self, policy: RoutingPolicy | None = None) -> None:
        self.policy = policy or tai_cau_hinh_chien_thuat()
        self._thoi_gian_goi: dict[str, list[float]] = {}
        self._token_trong_ngay: dict[str, int] = {}
        self._ngay_theo_doi: str = time.strftime("%Y-%m-%d")
        self._tam_ngung_den: dict[str, float] = {}

    def _lam_moi_theo_ngay(self) -> None:
        """Reset bo dem token theo ngay khi sang ngay moi."""
        hom_nay = time.strftime("%Y-%m-%d")
        if hom_nay != self._ngay_theo_doi:
            self._ngay_theo_doi = hom_nay
            self._token_trong_ngay.clear()

    def _dang_tam_ngung(self, ten_provider: str) -> bool:
        """Kiem tra provider co dang bi cooldown do loi/429 hay khong."""
        moc = self._tam_ngung_den.get(ten_provider, 0.0)
        if moc <= 0.0:
            return False
        if time.monotonic() >= moc:
            self._tam_ngung_den.pop(ten_provider, None)
            return False
        return True

    def _dat_tam_ngung(self, ten_provider: str, giay: float = 45.0) -> None:
        """Dat thoi gian tam nghi cho provider bi 429 hoac loi lien tiep."""
        self._tam_ngung_den[ten_provider] = time.monotonic() + giay

    def _cho_rpm_neu_can(self, cfg: ProviderConfig) -> None:
        """Kiem soat so lan goi trong 60 giay gan nhat theo rpm_limit."""
        moc_hien_tai = time.monotonic()
        ds = [t for t in self._thoi_gian_goi.get(cfg.name, []) if moc_hien_tai - t < 60.0]
        if len(ds) >= cfg.rpm_limit:
            thoi_gian_cho = max(0.05, 60.0 - (moc_hien_tai - ds[0]))
            time.sleep(min(thoi_gian_cho, 5.0))
            moc_hien_tai = time.monotonic()
            ds = [t for t in ds if moc_hien_tai - t < 60.0]
        ds.append(moc_hien_tai)
        self._thoi_gian_goi[cfg.name] = ds

    def _lay_chuoi_ung_vien(self, ho_so_may: HoSoPhanCung) -> list[tuple[str, ProviderConfig]]:
        """Lap danh sach (tier, provider) hop le theo profile va dieu kien phan cung."""
        self.policy = tai_cau_hinh_chien_thuat()
        prof = self.policy.lay_profile_hien_hanh()
        ung_vien: list[tuple[str, ProviderConfig]] = []

        for tier in prof.tier_order:
            if tier in PAID_TIERS and not prof.allow_paid_fallback:
                continue
            for prov in self.policy.providers.get(tier, []):
                if self._dang_tam_ngung(prov.name):
                    continue
                if prov.kind == "openai_compatible" and prov.api_key_env and not prov.lay_api_key():
                    continue
                nguong_ram = max(prov.min_free_ram_mb, self.policy.hardware.min_free_ram_mb)
                if prov.kind == "ollama" and not ho_so_may.du_ram_cho_local(nguong_ram):
                    continue
                ung_vien.append((tier, prov))
        return ung_vien

    def _goi_ollama(self, cfg: ProviderConfig, prompt: str, system_prompt: str, ho_so_may: HoSoPhanCung, max_tokens: int) -> str:
        """Goi endpoint /api/chat cua Ollama voi tham so an toan tu phan cung."""
        url = f"{cfg.base_url.rstrip('/')}/api/chat"
        payload = {
            "model": cfg.model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "options": {
                "num_ctx": ho_so_may.goi_y_num_ctx,
                "num_thread": ho_so_may.goi_y_num_thread,
                "num_predict": max_tokens,
            },
        }
        resp = requests.post(url, json=payload, timeout=cfg.timeout_s)
        if resp.status_code == 429:
            raise requests.HTTPError("429 Too Many Requests", response=resp)
        resp.raise_for_status()
        data = resp.json()
        return str((data.get("message") or {}).get("content") or "").strip()

    def _goi_openai_compatible(self, cfg: ProviderConfig, prompt: str, system_prompt: str, max_tokens: int) -> str:
        """Goi endpoint /chat/completions chuan OpenAI-compatible."""
        url = f"{cfg.base_url.rstrip('/')}/chat/completions"
        headers = {"Content-Type": "application/json"}
        api_key = cfg.lay_api_key()
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        payload = {
            "model": cfg.model,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
        }
        resp = requests.post(url, json=payload, headers=headers, timeout=cfg.timeout_s)
        if resp.status_code == 429:
            raise requests.HTTPError("429 Too Many Requests", response=resp)
        resp.raise_for_status()
        data = resp.json()
        choices = data.get("choices") or []
        if not choices:
            return ""
        msg = (choices[0] or {}).get("message") or {}
        return str(msg.get("content") or "").strip()

    def goi(
        self,
        buoc: str,
        prompt: str,
        system_prompt: str = "",
        ngan_sach: BoKiemSoatNganSach | None = None,
    ) -> KetQuaGoiModel:
        """Goi model theo thu tu uu tien; gap 429/timeout/loi/het han muc thi chuyen ngay."""
        self._lam_moi_theo_ngay()
        budget = ngan_sach or BoKiemSoatNganSach(self.policy.lay_ngan_sach_hieu_luc())
        ok_goi, ly_do_chan = budget.co_the_goi_llm_tiep()
        if not ok_goi:
            raise LoiHetNganSachHoacFallback(ly_do_chan or "Het ngan sach luot goi LLM.")

        input_tokens = uoc_luong_token(system_prompt) + uoc_luong_token(prompt)
        ok_in, canh_bao_in = budget.kiem_tra_dau_vao_buoc(input_tokens)
        if not ok_in:
            raise LoiHetNganSachHoacFallback("; ".join(canh_bao_in))

        ho_so_may = nhan_dien_phan_cung(self.policy.hardware)
        ung_vien = self._lay_chuoi_ung_vien(ho_so_may)
        if not ung_vien:
            raise LoiHetNganSachHoacFallback("Khong co provider nao kha dung theo profile va tai nguyen hien tai.")

        nhat_ky: list[str] = []
        max_out = budget.cau_hinh.max_output_tokens_per_step

        for tier, prov in ung_vien:
            da_dung_ngay = self._token_trong_ngay.get(prov.name, 0)
            if da_dung_ngay + input_tokens > prov.daily_token_budget:
                nhat_ky.append(f"{prov.name}: vuot han muc token ngay ({da_dung_ngay}/{prov.daily_token_budget})")
                continue

            self._cho_rpm_neu_can(prov)
            try:
                if prov.kind == "ollama":
                    noi_dung = self._goi_ollama(prov, prompt, system_prompt, ho_so_may, max_out)
                else:
                    noi_dung = self._goi_openai_compatible(prov, prompt, system_prompt, max_out)

                out_tokens = uoc_luong_token(noi_dung)
                self._token_trong_ngay[prov.name] = da_dung_ngay + input_tokens + out_tokens
                thong_ke = budget.ghi_nhan_buoc(
                    buoc=buoc,
                    provider=prov.name,
                    input_tokens=input_tokens,
                    output_tokens=out_tokens,
                    canh_bao_dau_vao=canh_bao_in,
                )
                return KetQuaGoiModel(
                    noi_dung=noi_dung,
                    provider_ten=prov.name,
                    tier=tier,
                    model=prov.model,
                    thong_ke_buoc=thong_ke,
                    nhat_ky_chuyen_nguon=nhat_ky,
                )
            except requests.HTTPError as exc:
                status = exc.response.status_code if exc.response is not None else 0
                if status == 429:
                    self._dat_tam_ngung(prov.name, giay=60.0)
                nhat_ky.append(f"{prov.name}: HTTP {status or exc}")
                logger.warning("Fallback tu %s (%s): HTTP %s", prov.name, tier, status or exc)
            except requests.RequestException as exc:
                self._dat_tam_ngung(prov.name, giay=30.0)
                nhat_ky.append(f"{prov.name}: loi ket noi/timeout ({exc})")
                logger.warning("Fallback tu %s (%s): %s", prov.name, tier, exc)

        raise LoiHetNganSachHoacFallback("Tat ca provider kha dung deu that bai: " + " | ".join(nhat_ky))