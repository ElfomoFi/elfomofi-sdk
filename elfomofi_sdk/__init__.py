"""ElfomoFi SDK — onchain-driven quoting with offchain probe state.

Architecture
────────────
1. Subscribe to new blocks (WebSocket).
2. On each block, call ``ElfomoFiHelper.getAllOrderbooks()`` which
   probes ``ElfomoFi.getAmountOut()`` at configurable amount buckets
   per direction.
3. Store cumulative levels in memory.
4. Expose synchronous ``quote()`` that does deterministic
   piecewise-linear interpolation — **no RPC calls**.
"""

from .chains import BASE, CHAINS, ChainConfig
from .client import ElfomoFiClient
from .quoting.engine import get_amount_out
from .state.models import (
    DirectionBook,
    ProbePoint,
    QuoteResult,
    TokenPair,
)

__all__ = [
    "BASE",
    "CHAINS",
    "ChainConfig",
    "ElfomoFiClient",
    "DirectionBook",
    "ProbePoint",
    "QuoteResult",
    "TokenPair",
    "get_amount_out",
]

__version__ = "0.1.0"
