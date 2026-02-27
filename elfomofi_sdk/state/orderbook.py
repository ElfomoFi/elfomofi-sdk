"""Probe-based builder.

Constructs ``DirectionBook`` from raw probe data.  Quoting is done via
piecewise-linear interpolation directly over cumulative probe points.
"""

from __future__ import annotations

from .models import (
    DirectionBook,
    ProbePoint,
)


def build_direction_book(
    from_token: str,
    to_token: str,
    probes: list[ProbePoint],
    from_balance: int = 0,
    to_balance: int = 0,
) -> DirectionBook:
    """Build a :class:`DirectionBook` from raw probe data."""
    return DirectionBook(
        from_token=from_token,
        to_token=to_token,
        probes=probes,
        from_balance=from_balance,
        to_balance=to_balance,
    )
