"""Disturbance and fault scenario runners."""

from __future__ import annotations

from collections.abc import Sequence

from PyDML.analysis.powerflow import run_power_flow
from PyDML.controls.supervisory import DieselController, UPSController
from PyDML.simulation.scheduler import index_events
from PyDML.types import Event, FaultScenario, ScenarioResults, SystemModel


def _set_switch(system: SystemModel, switch_name: str, closed: bool) -> None:
    net = system.net
    mask = net.switch["name"] == switch_name
    if mask.any():
        idx = net.switch[mask].index[0]
        net.switch.at[idx, "closed"] = closed


def _set_grid(system: SystemModel, available: bool) -> None:
    net = system.net
    if len(net.ext_grid.index) > 0:
        net.ext_grid.loc[:, "in_service"] = available
    system.state["grid_available"] = available


def _set_load_scale(system: SystemModel, scale: float) -> None:
    net = system.net
    if len(net.load.index) > 0:
        net.load.loc[:, "scaling"] = max(scale, 0.0)
    system.state["load_scale"] = scale


def _set_fault_state(system: SystemModel, active: bool, severity_pu: float = 0.5) -> None:
    net = system.net
    if len(net.ext_grid.index) > 0:
        net.ext_grid.loc[:, "vm_pu"] = 1.0 - severity_pu if active else 1.0
    system.state["fault_active"] = active


def _apply_event(system: SystemModel, event: Event) -> str:
    action = event.action
    payload = event.payload
    if action == "grid_fail":
        _set_grid(system, available=False)
    elif action == "grid_restore":
        _set_grid(system, available=True)
    elif action == "breaker_open":
        _set_switch(system, switch_name=payload["name"], closed=False)
    elif action == "breaker_close":
        _set_switch(system, switch_name=payload["name"], closed=True)
    elif action == "set_load_scale":
        _set_load_scale(system, scale=float(payload.get("scale", 1.0)))
    elif action == "apply_fault":
        _set_fault_state(system, active=True, severity_pu=float(payload.get("severity_pu", 0.5)))
    elif action == "clear_fault":
        _set_fault_state(system, active=False)
    return action


def _set_diesel_dispatch(system: SystemModel, running: bool) -> None:
    net = system.net
    if len(net.gen.index) > 0:
        net.gen.loc[:, "in_service"] = running
    system.state["diesel_running"] = running


def _set_ups_dispatch(system: SystemModel, mode: str) -> None:
    net = system.net
    storage_mask = net.storage["name"] == "ups_battery"
    if storage_mask.any():
        idx = net.storage[storage_mask].index[0]
        if mode == "battery_feed":
            max_discharge = abs(float(net.storage.at[idx, "min_p_mw"]))
            net.storage.at[idx, "p_mw"] = -0.7 * max_discharge
        else:
            net.storage.at[idx, "p_mw"] = 0.0
    system.state["ups_mode"] = mode


def _estimate_frequency_hz(base_hz: float, v_pu: float | None, fault_active: bool) -> float | None:
    if v_pu is None:
        return None
    f = base_hz - 2.0 * max(0.0, 1.0 - v_pu)
    if fault_active:
        f -= 0.4
    return f


def run_disturbance_sequence(
    system: SystemModel,
    events: Sequence[Event],
    end_time_s: float,
    time_step_s: float = 0.05,
    ups_controller: UPSController | None = None,
    diesel_controller: DieselController | None = None,
) -> ScenarioResults:
    """Run event-driven disturbance simulation with supervisory controls."""

    ups = ups_controller or UPSController()
    diesel = diesel_controller or DieselController(
        start_delay_s=float(system.metadata.get("diesel_start_delay_s", 60.0))
    )
    scheduled = index_events(list(events))

    t = 0.0
    times: list[float] = []
    records: list[dict[str, object]] = []
    applied: list[str] = []
    base_hz = float(system.metadata.get("nominal_frequency_hz", 60.0))

    while t <= end_time_s + 1e-12:
        rounded_t = round(t / 1e-9) * 1e-9
        for event in scheduled.get(rounded_t, []):
            applied.append(_apply_event(system, event))

        diesel_running = diesel.update(
            t_s=t,
            grid_available=bool(system.state["grid_available"]),
            diesel_running=bool(system.state["diesel_running"]),
        )
        _set_diesel_dispatch(system, diesel_running)

        pf = run_power_flow(system)
        v_pcc = pf.bus_vm_pu.get("pcc")
        f_pcc = _estimate_frequency_hz(base_hz=base_hz, v_pu=v_pcc, fault_active=bool(system.state["fault_active"]))
        next_mode = ups.update(
            current_mode=str(system.state["ups_mode"]),
            grid_available=bool(system.state["grid_available"]),
            v_pcc_pu=v_pcc,
            f_pcc_hz=f_pcc,
            diesel_running=bool(system.state["diesel_running"]),
        )
        _set_ups_dispatch(system, next_mode)

        pf_after = run_power_flow(system)
        pcc_voltage = pf_after.bus_vm_pu.get("pcc")
        lv_voltage = pf_after.bus_vm_pu.get("lv_main")

        times.append(round(t, 6))
        records.append(
            {
                "time_s": round(t, 6),
                "converged": pf_after.converged,
                "ups_mode": system.state["ups_mode"],
                "diesel_running": system.state["diesel_running"],
                "grid_available": system.state["grid_available"],
                "fault_active": system.state["fault_active"],
                "v_pcc_pu": pcc_voltage,
                "v_lv_pu": lv_voltage,
                "f_pcc_hz": _estimate_frequency_hz(base_hz, pcc_voltage, bool(system.state["fault_active"])),
            }
        )
        t += time_step_s

    return ScenarioResults(
        time_s=times,
        records=records,
        events_applied=applied,
        final_state=dict(system.state),
        notes=["phasor_first_supervisory_sequence"],
    )


def run_fault_scenario(system: SystemModel, scenario: FaultScenario) -> ScenarioResults:
    """Run default pre-fault, fault, and post-fault sequence."""

    events = [
        Event(
            time_s=scenario.start_time_s,
            action="apply_fault",
            payload={
                "fault_type": scenario.fault_type,
                "location": scenario.location,
                "distance_pu": scenario.distance_pu,
                "severity_pu": scenario.severity_pu,
            },
        ),
        Event(time_s=scenario.start_time_s + scenario.duration_s, action="clear_fault"),
    ]
    result = run_disturbance_sequence(
        system=system,
        events=events,
        end_time_s=scenario.end_time_s,
        time_step_s=scenario.time_step_s,
    )
    result.notes.append("fault_scenario_complete")
    return result
