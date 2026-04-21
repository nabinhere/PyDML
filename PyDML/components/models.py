"""Simple component abstractions for scenario configuration."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class TransformerModel:
    name: str
    hv_kv: float
    lv_kv: float
    rating_mva: float
    vector_group: str = "YNd"


@dataclass(slots=True)
class LineModel:
    name: str
    length_km: float
    r_ohm_per_km: float
    x_ohm_per_km: float


@dataclass(slots=True)
class BreakerModel:
    name: str
    normally_closed: bool = True


@dataclass(slots=True)
class FaultModel:
    fault_type: str
    severity_pu: float
    duration_s: float
    distance_pu: float = 0.5


@dataclass(slots=True)
class UPSModel:
    rated_mw: float
    battery_mw: float
    battery_mwh: float


@dataclass(slots=True)
class ITLoadModel:
    name: str
    p_mw: float
    q_mvar: float
    profile: str = "constant_pq"
