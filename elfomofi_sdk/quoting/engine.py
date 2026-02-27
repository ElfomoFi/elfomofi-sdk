"""Deterministic quoting engine.

Calculates ``amountOut`` from in-memory orderbook state using
**piecewise linear interpolation** over probe points.

┌─────────────────────────────────────────────────────────────────────┐
│  All arithmetic is integer-only.                                    │
│  Division is floor-division (``//``) for outputs, matching          │
│  Solidity uint256 semantics.                                        │
└─────────────────────────────────────────────────────────────────────┘

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
"""

from __future__ import annotations

from ..state.models import DirectionBook, ProbePoint, QuoteResult


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
        direction:    Probe data for the desired trade direction.
        amount_in:    Input token amount (smallest unit).
        block_number: Block at which the orderbook was snapshotted.

    Returns:
        A :class:`QuoteResult` with the calculated ``amount_out``.
    """
    probes = direction.probes

    if amount_in <= 0 or not probes:
        return _empty_result(direction, amount_in, 0, block_number)

    amount_out = _calc_quote(probes, amount_in)

    return QuoteResult(
        from_token=direction.from_token,
        to_token=direction.to_token,
        amount_in=amount_in,
        amount_out=amount_out,
        block_number=block_number,
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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
