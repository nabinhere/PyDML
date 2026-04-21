"""Shared datatypes for PyDML."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class MissingDependencyError(RuntimeError):
    """Raised when an optional simulation backend is not installed."""


@dataclass(slots=True)
class CaseConfig:
    """Configuration for building the baseline case."""

    name: str = "central_ups_dc_v1"
    grid_voltage_kv: float = 33.0
    pcc_voltage_kv: float = 33.0
    lv_voltage_kv: float = 0.4
    line_length_km: float = 5.0
    load_mw: float = 5.0
    load_mvar: float = 1.0
    diesel_mw: float = 6.0
    battery_mw: float = 2.5
    battery_mwh: float = 2.0
    base_frequency_hz: float = 60.0


@dataclass(slots=True)
class SystemModel:
    """Container for the simulation network and runtime state."""

    name: str
    network_engine: str
    net: Any
    metadata: dict[str, Any] = field(default_factory=dict)
    state: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class PowerFlowResults:
    converged: bool
    bus_vm_pu: dict[str, float]
    line_loading_pct: dict[str, float]
    trafo_loading_pct: dict[str, float]
    generator_p_mw: dict[str, float]
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class FaultScenario:
    fault_type: str = "3ph"
    location: str = "pcc"
    start_time_s: float = 0.5
    duration_s: float = 0.2
    distance_pu: float = 0.5
    severity_pu: float = 0.5
    end_time_s: float = 5.0
    time_step_s: float = 0.05


@dataclass(slots=True)
class Event:
    time_s: float
    action: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ScenarioResults:
    time_s: list[float]
    records: list[dict[str, Any]]
    events_applied: list[str]
    final_state: dict[str, Any]
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ValidationReport:
    passed: bool
    score: float
    metric_errors: dict[str, float]
    details: dict[str, Any] = field(default_factory=dict)
