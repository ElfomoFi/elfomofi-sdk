"""Per-chain configuration for the ElfomoFi SDK."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True, slots=True)
class ChainConfig:
    """Configuration for a single chain deployment."""

    chain_id: int
    name: str
    helper_address: str  # checksummed address of ElfomoFiHelper


# ── Chain definitions ────────────────────────────────────────────────

BASE: Final[ChainConfig] = ChainConfig(
    chain_id=8453,
    name="Base",
    helper_address="0xc1b13606FC7227f2554067aFb3fb12De75C02d81",
)

BSC: Final[ChainConfig] = ChainConfig(
    chain_id=56,
    name="Bsc",
    helper_address="0x78015E3544d989f0712a0b9986cB05838c3fE06D",
)

CHAINS: Final[dict[int, ChainConfig]] = {
    BASE.chain_id: BASE,
    BSC.chain_id: BSC,
}
