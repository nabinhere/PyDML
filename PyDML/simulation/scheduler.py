"""Event scheduling utilities."""

from __future__ import annotations

from collections import defaultdict

from PyDML.types import Event


def index_events(events: list[Event], tolerance_s: float = 1e-9) -> dict[float, list[Event]]:
    """Group events by time for quick lookup in fixed-step simulation."""

    grouped: dict[float, list[Event]] = defaultdict(list)
    for event in events:
        rounded = round(event.time_s / tolerance_s) * tolerance_s
        grouped[rounded].append(event)
    return dict(grouped)
