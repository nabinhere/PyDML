"""Minimal simulation primitives for PyDML."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class SimulationCase:
    name: str = "central_ups_dc"
    base_frequency_hz: float = 60.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class DisturbanceEvent:
    time_s: float
    event_type: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SimulationResult:
    time_s: list[float]
    states: list[dict[str, Any]]
    events_applied: list[str]


def create_case(name: str = "central_ups_dc", base_frequency_hz: float = 60.0) -> SimulationCase:
    """Create a minimal simulation case."""

    return SimulationCase(name=name, base_frequency_hz=base_frequency_hz)


def run_disturbance(
    case: SimulationCase,
    events: list[DisturbanceEvent],
    end_time_s: float,
    time_step_s: float = 0.05,
) -> SimulationResult:
    """Run a minimal time-stepped disturbance sequence.

    This is intentionally simple and acts as the starting scaffold before
    ANDES network and dynamic model bindings are added.
    """

    t = 0.0
    events_by_time: dict[float, list[DisturbanceEvent]] = {}
    for event in events:
        key = round(event.time_s, 9)
        events_by_time.setdefault(key, []).append(event)

    mode = "normal"
    grid_available = True
    time_points: list[float] = []
    states: list[dict[str, Any]] = []
    applied: list[str] = []

    while t <= end_time_s + 1e-12:
        key = round(t, 9)
        for event in events_by_time.get(key, []):
            applied.append(event.event_type)
            if event.event_type == "grid_fail":
                grid_available = False
                mode = "battery"
            elif event.event_type == "grid_restore":
                grid_available = True
                mode = "recovery"
            elif event.event_type == "set_mode":
                mode = str(event.payload.get("mode", mode))

        time_points.append(round(t, 6))
        states.append(
            {
                "time_s": round(t, 6),
                "mode": mode,
                "grid_available": grid_available,
                "frequency_hz": case.base_frequency_hz if grid_available else case.base_frequency_hz - 0.5,
            }
        )
        t += time_step_s

    return SimulationResult(time_s=time_points, states=states, events_applied=applied)
