import pytest

from PyDML import (
    CaseConfig,
    Event,
    FaultScenario,
    build_case,
    compare_to_pscad,
    run_disturbance_sequence,
    run_fault_scenario,
    run_power_flow,
)


def _has_pandapower() -> bool:
    try:
        import pandapower  # noqa: F401
    except ImportError:
        return False
    return True


@pytest.mark.skipif(not _has_pandapower(), reason="pandapower not installed")
def test_power_flow_converges():
    system = build_case(CaseConfig())
    result = run_power_flow(system)
    assert result.converged
    assert "pcc" in result.bus_vm_pu


@pytest.mark.skipif(not _has_pandapower(), reason="pandapower not installed")
def test_fault_scenario_and_validation():
    system = build_case(CaseConfig())
    scenario = FaultScenario(end_time_s=0.6, start_time_s=0.1, duration_s=0.1, time_step_s=0.1)
    result = run_fault_scenario(system, scenario)
    assert len(result.records) > 0
    report = compare_to_pscad(
        result,
        {
            "metrics": {
                "v_pcc_pu": 0.9,
                "f_pcc_hz": 59.0,
            },
            "tolerance": 1.0,
        },
    )
    assert report.score >= 0.0


@pytest.mark.skipif(not _has_pandapower(), reason="pandapower not installed")
def test_grid_fail_triggers_ups_battery_then_diesel():
    cfg = CaseConfig()
    system = build_case(cfg)
    system.metadata["diesel_start_delay_s"] = 0.2

    events = [Event(time_s=0.1, action="grid_fail")]
    result = run_disturbance_sequence(
        system=system,
        events=events,
        end_time_s=0.6,
        time_step_s=0.1,
    )
    modes = [record["ups_mode"] for record in result.records]
    assert "battery_feed" in modes
