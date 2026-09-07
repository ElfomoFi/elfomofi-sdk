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

<<<<<<< HEAD
<<<<<<< HEAD
from .chains import BASE, BSC, CHAINS, X_LAYER, ChainConfig
=======
from .chains import BASE, CHAINS, ChainConfig
>>>>>>> 253e165 (init)
=======
from .chains import BASE, CHAINS, ROBINHOOD, ChainConfig
>>>>>>> a0c81a5 (add robinhood helper)
from .client import ElfomoFiClient
from .quoting.engine import get_amount_out
from .state.models import (
    DirectionBook,
<<<<<<< HEAD
    OrderbookLevel,
=======
>>>>>>> 253e165 (init)
    ProbePoint,
    QuoteResult,
    TokenPair,
)

__all__ = [
    "BASE",
<<<<<<< HEAD
    "BSC",
    "CHAINS",
    "X_LAYER",
    "ChainConfig",
    "ElfomoFiClient",
    "DirectionBook",
    "OrderbookLevel",
=======
    "CHAINS",
    "ROBINHOOD",
    "ChainConfig",
    "ElfomoFiClient",
    "DirectionBook",
>>>>>>> 253e165 (init)
    "ProbePoint",
    "QuoteResult",
    "TokenPair",
    "get_amount_out",
]

__version__ = "0.1.0"
