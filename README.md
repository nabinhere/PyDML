# PyDML

Phasor-first centralized UPS data center simulation toolkit.

## Quick Start

```bash
pip install -e ".[dev,sim,viz]"
pytest
```

## Package Descriptions

- `PyDML/types.py`: shared dataclasses and result types (`CaseConfig`, `SystemModel`, `PowerFlowResults`, `FaultScenario`, `Event`, `ScenarioResults`, `ValidationReport`).
- `PyDML/api.py`: public API surface for case build, power flow, fault scenarios, disturbance sequences, and PSCAD comparison.
- `PyDML/network/builder.py`: creates the baseline data center electrical network in `pandapower` (grid, PCC, transformer, LV feeder, IT load, battery storage, diesel generator placeholder).
- `PyDML/analysis/powerflow.py`: runs AC power flow and extracts bus voltage, line/transformer loading, and generator outputs.
- `PyDML/components/models.py`: component dataclasses for transformers, lines, breakers, faults, UPS, and IT loads.
- `PyDML/controls/supervisory.py`: supervisory control state machines for UPS mode transitions and diesel startup runtime logic.
- `PyDML/simulation/scheduler.py`: event indexing/grouping for fixed time-step simulations.
- `PyDML/simulation/runner.py`: event-driven disturbance engine and default fault scenario orchestration.
- `PyDML/validation/pscad.py`: metric-based comparison between PyDML scenario outputs and PSCAD reference values.
- `PyDML/visualization/plots.py`: plotting helpers for scenario voltage/frequency traces.
- `tests/test_api.py`: API-level tests for flow execution.
- `tests/test_controls.py`: controller behavior tests.

## Interdependencies (File-Level)

- `PyDML/__init__.py` imports from `PyDML/api.py`, `PyDML/types.py`, and `PyDML/controls/supervisory.py`.
- `PyDML/api.py` depends on:
  `PyDML/network/builder.py`,
  `PyDML/analysis/powerflow.py`,
  `PyDML/simulation/runner.py`,
  `PyDML/validation/pscad.py`,
  `PyDML/types.py`,
  `PyDML/controls/supervisory.py`.
- `PyDML/network/builder.py` depends on:
  `PyDML/types.py`,
  optional external dependency `pandapower`.
- `PyDML/analysis/powerflow.py` depends on:
  `PyDML/types.py`,
  external dependency `pandapower`.
- `PyDML/simulation/runner.py` depends on:
  `PyDML/types.py`,
  `PyDML/analysis/powerflow.py`,
  `PyDML/controls/supervisory.py`,
  `PyDML/simulation/scheduler.py`.
- `PyDML/simulation/scheduler.py` depends on `PyDML/types.py`.
- `PyDML/validation/pscad.py` depends on `PyDML/types.py`.
- `PyDML/visualization/plots.py` depends on:
  `PyDML/types.py`,
  optional external dependency `matplotlib`.
- `tests/test_api.py` depends on:
  top-level `PyDML` API,
  optional external dependency `pandapower`.
- `tests/test_controls.py` depends on `PyDML/controls/supervisory.py`.

## Using PyDML for Disturbance and EMT-Style Studies

PyDML v1 is **phasor-first** (not switching-level EMT). You can still run disturbance studies commonly used in EMT workflows: fault application/clearing, grid loss, UPS transfer to battery, diesel startup delay, and post-disturbance recovery.

### 1) Build a Base System and Run Power Flow

```python
from PyDML import CaseConfig, build_case, run_power_flow

system = build_case(CaseConfig(load_mw=5.0, load_mvar=1.0))
pf = run_power_flow(system)
print(pf.converged, pf.bus_vm_pu)
```

### 2) Run a Fault Scenario (Pre-Fault, Fault-On, Post-Fault)

```python
from PyDML import FaultScenario, run_fault_scenario

scenario = FaultScenario(
    fault_type="3ph",
    location="pcc",
    start_time_s=0.5,
    duration_s=0.2,
    severity_pu=0.5,
    end_time_s=2.0,
    time_step_s=0.05,
)
result = run_fault_scenario(system, scenario)
print(result.final_state)
```

### 3) Run Event-Driven Disturbance Sequences (UPS + Diesel Logic)

```python
from PyDML import Event, run_disturbance_sequence

system.metadata["diesel_start_delay_s"] = 10.0
events = [
    Event(time_s=0.5, action="grid_fail"),
    Event(time_s=1.0, action="set_load_scale", payload={"scale": 0.9}),
    Event(time_s=20.0, action="grid_restore"),
]
result = run_disturbance_sequence(system, events=events, end_time_s=30.0, time_step_s=0.1)
```

### 4) Compare with PSCAD Reference Metrics

```python
from PyDML import compare_to_pscad

report = compare_to_pscad(
    result,
    {
        "metrics": {"v_pcc_pu": 0.98, "f_pcc_hz": 59.9},
        "tolerance": 0.1,
    },
)
print(report.passed, report.score, report.metric_errors)
```

### 5) Plot Disturbance Response

```python
from PyDML.visualization import plot_scenario

fig = plot_scenario(result)
fig.show()
```

## EMT Extension Guidance

- Replace reduced-order UPS behavior in `PyDML/controls/supervisory.py` with detailed inverter/rectifier control blocks.
- Add higher-fidelity component equations behind `PyDML/components/models.py` interfaces.
- Keep event orchestration in `PyDML/simulation/runner.py` unchanged so scenario APIs remain stable.
- Use `PyDML/validation/pscad.py` to track parity against PSCAD as fidelity is increased.
