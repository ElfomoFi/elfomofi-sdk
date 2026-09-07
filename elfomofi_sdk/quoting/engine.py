"""Deterministic quoting engine.

<<<<<<< HEAD
Calculates ``amountOut`` by walking orderbook levels derived from
cumulative probe points.
=======
Calculates ``amountOut`` from in-memory orderbook state using
**piecewise linear interpolation** over probe points.
>>>>>>> 253e165 (init)

┌─────────────────────────────────────────────────────────────────────┐
│  All arithmetic is integer-only.                                    │
│  Division is floor-division (``//``) for outputs, matching          │
│  Solidity uint256 semantics.                                        │
└─────────────────────────────────────────────────────────────────────┘

<<<<<<< HEAD
The engine consumes levels sequentially.  For each level it either:
- fills completely (input >= level.size_in), adding level.size_out
- fills partially, interpolating within the level:

    out += (remaining * level.size_out) // level.size_in

If the input exceeds all levels, the output is capped at the sum
of all level outputs.
=======
Probe points form a curve from the origin ``(0, 0)`` through each
sampled ``(amountIn, amountOut)``.  For any query amount we locate the
enclosing segment and interpolate linearly:

    segment [P_i, P_{i+1}]:
        delta_in  = P_{i+1}.amount_in  - P_i.amount_in
        delta_out = P_{i+1}.amount_out - P_i.amount_out
        excess    = query - P_i.amount_in

        result = P_i.amount_out + (excess * delta_out) // delta_in

If the query exceeds the last probe, the engine caps at the last
probe point.
>>>>>>> 253e165 (init)
"""

from __future__ import annotations

<<<<<<< HEAD
from ..state.models import DirectionBook, OrderbookLevel, QuoteResult
=======
from ..state.models import DirectionBook, ProbePoint, QuoteResult
>>>>>>> 253e165 (init)


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
<<<<<<< HEAD
        direction:    Orderbook levels for the desired trade direction.
        amount_in:    Input token amount (smallest unit).
        block_number: Block at which the state was snapshotted.
=======
        direction:    Probe data for the desired trade direction.
        amount_in:    Input token amount (smallest unit).
        block_number: Block at which the orderbook was snapshotted.
>>>>>>> 253e165 (init)

    Returns:
        A :class:`QuoteResult` with the calculated ``amount_out``.
    """
<<<<<<< HEAD
    levels = direction.levels

    if amount_in <= 0 or not levels:
        return _empty_result(direction, amount_in, 0, block_number)

    amount_out = _calc_quote(levels, amount_in)
=======
    probes = direction.probes

    if amount_in <= 0 or not probes:
        return _empty_result(direction, amount_in, 0, block_number)

    amount_out = _calc_quote(probes, amount_in)
>>>>>>> 253e165 (init)

    return QuoteResult(
        from_token=direction.from_token,
        to_token=direction.to_token,
        amount_in=amount_in,
        amount_out=amount_out,
        block_number=block_number,
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<<<<<<< HEAD
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
=======
#  Interpolation  (amountIn → amountOut)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def _calc_quote(
    probes: list[ProbePoint], amount_in: int
) -> int:
    # ── Segment 0: origin (0, 0) → probes[0] ──────────────────────
    first = probes[0]
    if amount_in <= first.amount_in:
        if first.amount_in == 0:
            return 0
        out = (amount_in * first.amount_out) // first.amount_in
        return out

    # ── Segments 1 … N-1: probes[i] → probes[i+1] ────────────────
    for i in range(len(probes) - 1):
        upper = probes[i + 1]
        if amount_in <= upper.amount_in:
            lower = probes[i]
            delta_in = upper.amount_in - lower.amount_in
            delta_out = upper.amount_out - lower.amount_out
            if delta_in == 0:
                return lower.amount_out
            excess = amount_in - lower.amount_in
            out = lower.amount_out + (excess * delta_out) // delta_in
            return out

    # ── Beyond last probe: cap at last probe point ────────────────
    last = probes[-1]
    return last.amount_out
>>>>>>> 253e165 (init)


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
