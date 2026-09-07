"""Data models for ElfomoFi SDK.

All monetary amounts are stored as raw integers in the token's smallest unit
(e.g. wei for ETH, 1e-6 for USDC).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Core primitives
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@dataclass(frozen=True, slots=True)
class TokenPair:
    """A supported token pair as returned by the contract."""

    base_token: str  # checksummed address
    quote_token: str  # checksummed address

    @property
    def key(self) -> tuple[str, str]:
        return (self.base_token, self.quote_token)


@dataclass(frozen=True, slots=True)
class ProbePoint:
    """Single (amountIn, amountOut) measurement from onchain probing.

    These are *cumulative*: probes are sorted by increasing amountIn,
    and each amountOut is the total output for that total input.
    """

    amount_in: int  # raw token amount (smallest unit)
    amount_out: int  # raw token amount (smallest unit)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Orderbook level
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@dataclass(frozen=True, slots=True)
class OrderbookLevel:
    """A single level in the synthetic orderbook.

    Derived from consecutive cumulative probe points.  Each level
    represents a price band with a fixed marginal rate:

        size_in  = probe[i].amount_in  - probe[i-1].amount_in
        size_out = probe[i].amount_out - probe[i-1].amount_out
        price    = size_out / size_in  (rational, kept as ints)
    """

    size_in: int   # input token size at this level
    size_out: int  # output token size at this level


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Direction
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@dataclass(slots=True)
class DirectionBook:
    """Orderbook levels for a single trade direction (e.g. quote → base).

    Built from cumulative probe points: each consecutive pair of probes
    defines a level with ``(size_in, size_out)``.  The quoting engine
    walks these levels to compute output amounts.
    """

    from_token: str
    to_token: str
    levels: list[OrderbookLevel] = field(default_factory=list)
    from_balance: int = 0  # vault balance of from_token
    to_balance: int = 0  # vault balance of to_token


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Quote result
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@dataclass(slots=True)
class QuoteResult:
    """Result of a local quote calculation."""

    from_token: str
    to_token: str
    amount_in: int
    amount_out: int
    block_number: int  # block at which the state was snapshotted
