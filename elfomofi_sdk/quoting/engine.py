"""Deterministic quoting engine.

Calculates ``amountOut`` by walking orderbook levels derived from
cumulative probe points.

┌─────────────────────────────────────────────────────────────────────┐
│  All arithmetic is integer-only.                                    │
│  Division is floor-division (``//``) for outputs, matching          │
│  Solidity uint256 semantics.                                        │
└─────────────────────────────────────────────────────────────────────┘

The engine consumes levels sequentially.  For each level it either:
- fills completely (input >= level.size_in), adding level.size_out
- fills partially, interpolating within the level:

    out += (remaining * level.size_out) // level.size_in

If the input exceeds all levels, the output is capped at the sum
of all level outputs.
"""

from __future__ import annotations

from ..state.models import DirectionBook, OrderbookLevel, QuoteResult


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Public API
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def get_amount_out(
    direction: DirectionBook,
    amount_in: int,
    block_number: int,
) -> QuoteResult:
    """Calculate output amount for a given input.

    Pure computation — **no RPC calls**.

    Args:
        direction:    Orderbook levels for the desired trade direction.
        amount_in:    Input token amount (smallest unit).
        block_number: Block at which the state was snapshotted.

    Returns:
        A :class:`QuoteResult` with the calculated ``amount_out``.
    """
    levels = direction.levels

    if amount_in <= 0 or not levels:
        return _empty_result(direction, amount_in, 0, block_number)

    amount_out = _calc_quote(levels, amount_in)

    return QuoteResult(
        from_token=direction.from_token,
        to_token=direction.to_token,
        amount_in=amount_in,
        amount_out=amount_out,
        block_number=block_number,
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Level-walking quote
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def _calc_quote(levels: list[OrderbookLevel], amount_in: int) -> int:
    remaining = amount_in
    total_out = 0

    for level in levels:
        if remaining <= 0:
            break

        if remaining >= level.size_in:
            # Full fill of this level
            total_out += level.size_out
            remaining -= level.size_in
        else:
            # Partial fill — interpolate within level
            total_out += (remaining * level.size_out) // level.size_in
            remaining = 0

    return total_out


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Utilities
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def _empty_result(
    direction: DirectionBook,
    amount_in: int,
    amount_out: int,
    block_number: int,
) -> QuoteResult:
    return QuoteResult(
        from_token=direction.from_token,
        to_token=direction.to_token,
        amount_in=amount_in,
        amount_out=amount_out,
        block_number=block_number,
    )
