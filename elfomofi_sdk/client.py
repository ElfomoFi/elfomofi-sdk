"""ElfomoFi SDK client.

Usage:
    client = ElfomoFiClient(
        rpc_url="https://...",
        ws_url="wss://...",
        chain_id=8453,
    )
    await client.start()

    result = client.quote(WETH, USDC, 10**18)
    print(result.amount_out)

    await client.stop()
"""

from __future__ import annotations

import asyncio
import logging

from .chains import CHAINS
from .fetcher.onchain import OnchainFetcher
from .quoting.engine import get_amount_out
from .rpc.listener import BlockListener
from .rpc.provider import Web3Provider
from .state.models import DirectionBook, QuoteResult
from .state.orderbook import build_direction_book

logger = logging.getLogger(__name__)


class ElfomoFiClient:
    """High-level SDK entry point.

    Maintains in-memory probe data that is refreshed on every new block.
    The ``quote()`` method performs no RPC calls — it operates purely on
    the latest in-memory snapshot.
    """

    def __init__(
        self,
        rpc_url: str,
        ws_url: str,
        chain_id: int,
    ) -> None:
        config = CHAINS.get(chain_id)
        if config is None:
            raise ValueError(f"Unsupported chain_id {chain_id}")

        self._provider = Web3Provider(rpc_url, ws_url)
        self._helper = self._provider.contract(config.helper_address, "elfomofi_helper")
        self._fetcher = OnchainFetcher(self._helper)
        self._listener = BlockListener(ws_url)

        # ── State ──────────────────────────────────────────────────
        # direction key (from_token, to_token) → DirectionBook
        self._directions: dict[tuple[str, str], DirectionBook] = {}
        self._pair_keys: list[tuple[str, str]] = []  # (base, quote)

        self._current_block: int = 0
        self._block_timestamp: int = 0
        self._initialized = asyncio.Event()

    # ── Lifecycle ──────────────────────────────────────────────────

    async def start(self, timeout: float = 30.0) -> None:
        """Start the block listener and wait for the first snapshot."""
        logger.info("Starting ElfomoFi client…")
        await self._listener.start(self._on_new_block)
        await asyncio.wait_for(self._initialized.wait(), timeout=timeout)

    async def stop(self) -> None:
        """Stop the block listener."""
        logger.info("Stopping ElfomoFi client…")
        await self._listener.stop()

    # ── Read-only accessors ────────────────────────────────────────

    @property
    def current_block(self) -> int:
        """Block number of the most recent state update."""
        return self._current_block

    @property
    def block_timestamp(self) -> int:
        """Timestamp of the most recent state update."""
        return self._block_timestamp

    @property
    def pairs(self) -> list[tuple[str, str]]:
        """List of tracked pair keys ``(base_token, quote_token)``."""
        return list(self._pair_keys)

    def _get_direction(self, from_token: str, to_token: str) -> DirectionBook | None:
        """Return the DirectionBook for a given trade direction, or None."""
        f = self._provider.w3.to_checksum_address(from_token)
        t = self._provider.w3.to_checksum_address(to_token)
        return self._directions.get((f, t))

    # ── Quoting (synchronous, no RPC) ─────────────────────────────

    def quote(
        self,
        from_token: str,
        to_token: str,
        amount_in: int,
    ) -> QuoteResult | None:
        """Calculate ``amountOut`` locally from the in-memory state.

        **No RPC calls.**  Deterministic quoting over latest fetched on-chain state.

        Args:
            from_token: Input token address.
            to_token:   Output token address.
            amount_in:  Input amount in the token's smallest unit.

        Returns:
            :class:`QuoteResult` with ``amount_out`` populated, or ``None``
            if no data is loaded for this direction.
        """
        direction = self._get_direction(from_token, to_token)
        if direction is None:
            return None
        return get_amount_out(direction, amount_in, self._current_block)

    # ── Block callback ─────────────────────────────────────────────

    async def _on_new_block(self, block_number: int) -> None:
        """Fetch fresh probe data and atomically rebuild all directions."""
        logger.debug("Processing block %d", block_number)

        try:
            result = await self._fetcher.fetch_all_orderbooks()
        except Exception:
            logger.exception("Failed to fetch data at block %d", block_number)
            return

        # Build new state off the hot path, then swap atomically
        new_dirs: dict[tuple[str, str], DirectionBook] = {}
        new_pairs: list[tuple[str, str]] = []

        for raw in result.pairs:
            base = raw.pair.base_token
            quote = raw.pair.quote_token
            new_pairs.append((base, quote))

            # asks: quote → base (user buys base)
            asks = build_direction_book(
                quote, base, raw.ask_probes, raw.balance_quote, raw.balance_base,
            )
            # bids: base → quote (user sells base)
            bids = build_direction_book(
                base, quote, raw.bid_probes, raw.balance_base, raw.balance_quote,
            )
            new_dirs[(asks.from_token, asks.to_token)] = asks
            new_dirs[(bids.from_token, bids.to_token)] = bids

        # Only apply if this result is fresher than what we already have
        if result.block_number <= self._current_block:
            logger.debug(
                "Skipping stale update for block %d (current: %d)",
                result.block_number,
                self._current_block,
            )
            return

        self._directions = new_dirs
        self._pair_keys = new_pairs
        self._current_block = result.block_number
        self._block_timestamp = result.block_timestamp

        logger.info(
            "Updated %d pair(s) at block %d (timestamp %d)",
            len(new_pairs),
            result.block_number,
            result.block_timestamp,
        )
        self._initialized.set()
