"""Onchain data fetcher — calls the ElfomoFiHelper contract.

Decodes the raw ABI-encoded response from ``getAllOrderbooks()`` /
``getOrderbook()`` into typed Python objects that the rest of the SDK
can consume.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from ..state.models import ProbePoint, TokenPair

logger = logging.getLogger(__name__)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Intermediate data type
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@dataclass(slots=True)
class RawPairData:
    """Raw cumulative levels for a single pair, as returned by the helper."""

    pair: TokenPair
    ask_probes: list[ProbePoint]    # quote → base  (user buys base)
    bid_probes: list[ProbePoint]    # base → quote  (user sells base)
    balance_base: int
    balance_quote: int


@dataclass(slots=True)
class FetchResult:
    """Result of a helper contract call, including block metadata."""

    pairs: list[RawPairData]
    block_number: int
    block_timestamp: int


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Fetcher
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class OnchainFetcher:
    """Fetches orderbook data from the ``ElfomoFiHelper`` contract."""

    def __init__(self, helper_contract: Any) -> None:
        self._helper = helper_contract

    async def fetch_all_orderbooks(self) -> FetchResult:
        """Call ``getAllOrderbooks()`` and return decoded data with block metadata."""
        books, block_number, block_timestamp = (
            await self._helper.functions.getAllOrderbooks().call()
        )
        return FetchResult(
            pairs=[self._decode_pair(entry) for entry in books],
            block_number=block_number,
            block_timestamp=block_timestamp,
        )

    async def fetch_orderbook(self, base_token: str, quote_token: str) -> FetchResult:
        """Call ``getOrderbook(base, quote)`` for a single pair."""
        book, block_number, block_timestamp = (
            await self._helper.functions.getOrderbook(base_token, quote_token).call()
        )
        return FetchResult(
            pairs=[self._decode_pair(book)],
            block_number=block_number,
            block_timestamp=block_timestamp,
        )

    # ── Decoding ───────────────────────────────────────────────────

    @staticmethod
    def _decode_pair(entry: Any) -> RawPairData:
        """Decode a single ``PairOrderbook`` struct from the ABI response.

        The struct layout is:
            (address base, address quote,
             CumulativeLevel[] askCumulativeLevels,
             CumulativeLevel[] bidCumulativeLevels,
             uint256 balanceBase, uint256 balanceQuote)

        Both sides use ``getAmountOut(fromToken, toToken, fromAmount)``.
        """
        base_token: str = entry[0]
        quote_token: str = entry[1]

        ask_probes = [
            ProbePoint(amount_in=p[0], amount_out=p[1])
            for p in entry[2]
            if p[0] > 0  # filter out failed / zero entries
        ]

        bid_probes = [
            ProbePoint(amount_in=p[0], amount_out=p[1])
            for p in entry[3]
            if p[0] > 0
        ]

        balance_base: int = entry[4]
        balance_quote: int = entry[5]

        return RawPairData(
            pair=TokenPair(base_token=base_token, quote_token=quote_token),
            ask_probes=ask_probes,
            bid_probes=bid_probes,
            balance_base=balance_base,
            balance_quote=balance_quote,
        )
