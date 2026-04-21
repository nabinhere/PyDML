"""Public API entrypoints."""

from __future__ import annotations

from collections.abc import Sequence

from PyDML.analysis.powerflow import run_power_flow
from PyDML.controls.supervisory import DieselController, UPSController
from PyDML.network.builder import build_case
from PyDML.simulation.runner import run_disturbance_sequence, run_fault_scenario
from PyDML.types import (
    CaseConfig,
    Event,
    FaultScenario,
    PowerFlowResults,
    ScenarioResults,
    SystemModel,
    ValidationReport,
)
from PyDML.validation.pscad import compare_to_pscad

__all__ = [
    "CaseConfig",
    "Event",
    "FaultScenario",
    "PowerFlowResults",
    "ScenarioResults",
    "SystemModel",
    "ValidationReport",
    "build_case",
    "run_power_flow",
    "run_fault_scenario",
    "run_disturbance_sequence",
    "compare_to_pscad",
    "UPSController",
    "DieselController",
]


def run_disturbance_sequence_api(
    system: SystemModel,
    events: Sequence[Event],
    end_time_s: float,
    time_step_s: float = 0.05,
) -> ScenarioResults:
    """Compatibility wrapper for public API naming from the plan."""

    return run_disturbance_sequence(
        system=system,
        events=list(events),
        end_time_s=end_time_s,
        time_step_s=time_step_s,
    )

