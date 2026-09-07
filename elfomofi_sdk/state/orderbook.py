"""Orderbook builder.

Converts cumulative probe points into orderbook levels and constructs
``DirectionBook`` instances.  Each consecutive pair of cumulative probes
defines one level: ``(size_in, size_out)``.
"""

from __future__ import annotations

from .models import (
    DirectionBook,
    OrderbookLevel,
    ProbePoint,
)


def build_levels(probes: list[ProbePoint]) -> list[OrderbookLevel]:
    """Derive orderbook levels from cumulative probe points.

    Each level is the delta between two consecutive probes.  The implicit
    origin ``(0, 0)`` is used as the starting point for the first level.
    
    """
    if not probes:
        return []

    levels: list[OrderbookLevel] = []
    prev_in, prev_out = 0, 0

    for probe in probes:
        if probe.amount_in <= prev_in or probe.amount_out <= prev_out:
            continue

        delta_in = probe.amount_in - prev_in
        delta_out = probe.amount_out - prev_out

        levels.append(OrderbookLevel(size_in=delta_in, size_out=delta_out))

        prev_in = probe.amount_in
        prev_out = probe.amount_out

    return levels


def build_direction_book(
    from_token: str,
    to_token: str,
    probes: list[ProbePoint],
    from_balance: int = 0,
    to_balance: int = 0,
) -> DirectionBook:
    """Build a :class:`DirectionBook` from cumulative probe data."""
    levels = build_levels(probes)
    return DirectionBook(
        from_token=from_token,
        to_token=to_token,
        levels=levels,
        from_balance=from_balance,
        to_balance=to_balance,
    )
