# PyDML

Minimal ANDES-first scaffold for centralized UPS data center simulations.

## Install

```bash
pip install -e ".[dev]"
```

## What is included

- `PyDML/engine_andes.py`: single integration point to load ANDES.
- `PyDML/core.py`: minimal case, event, and disturbance-runner primitives.
- `PyDML/__init__.py`: clean public API export.

## Public API

```python
from PyDML import (
    initialize_andes,
    create_case,
    DisturbanceEvent,
    run_disturbance,
)
```

### 1) Initialize ANDES

```python
andes = initialize_andes()
print(andes.__version__)
```

### 2) Create a simple case

```python
case = create_case(name="dc_v1", base_frequency_hz=60.0)
```

### 3) Run a basic disturbance timeline

```python
events = [
    DisturbanceEvent(time_s=0.5, event_type="grid_fail"),
    DisturbanceEvent(time_s=5.0, event_type="grid_restore"),
]
result = run_disturbance(case, events, end_time_s=10.0, time_step_s=0.1)
print(result.states[-1])
```

## Current scope

- The current runner is intentionally simple.
- It is a starting point for wiring ANDES network models and dynamic components next.
- No pandapower dependency remains.
- ANDES is a required dependency.
