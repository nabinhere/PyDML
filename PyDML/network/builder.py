"""Pandapower-backed network creation."""

from __future__ import annotations

from typing import Any

from PyDML.types import CaseConfig, MissingDependencyError, SystemModel


def _require_pandapower() -> Any:
    try:
        import pandapower as pp
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise MissingDependencyError(
            "pandapower is required for network simulation. Install with `pip install -e \".[sim]\"`."
        ) from exc
    return pp


def build_case(config: CaseConfig | None = None) -> SystemModel:
    """Build baseline centralized UPS data-center case."""

    cfg = config or CaseConfig()
    pp = _require_pandapower()

    net = pp.create_empty_network(sn_mva=100.0, f_hz=cfg.base_frequency_hz)

    b_grid = pp.create_bus(net, vn_kv=cfg.grid_voltage_kv, name="grid")
    b_pcc = pp.create_bus(net, vn_kv=cfg.pcc_voltage_kv, name="pcc")
    b_lv_main = pp.create_bus(net, vn_kv=cfg.lv_voltage_kv, name="lv_main")
    b_it = pp.create_bus(net, vn_kv=cfg.lv_voltage_kv, name="it_bus")

    pp.create_ext_grid(net, b_grid, vm_pu=1.0, va_degree=0.0, name="grid_slack")

    line_idx = pp.create_line_from_parameters(
        net,
        from_bus=b_grid,
        to_bus=b_pcc,
        length_km=cfg.line_length_km,
        r_ohm_per_km=0.08,
        x_ohm_per_km=0.22,
        c_nf_per_km=10.0,
        max_i_ka=2.0,
        name="grid_to_pcc",
    )
    pp.create_switch(net, bus=b_grid, element=line_idx, et="l", closed=True, name="brk_grid")

    pp.create_transformer_from_parameters(
        net,
        hv_bus=b_pcc,
        lv_bus=b_lv_main,
        sn_mva=10.0,
        vn_hv_kv=cfg.pcc_voltage_kv,
        vn_lv_kv=cfg.lv_voltage_kv,
        vk_percent=8.0,
        vkr_percent=1.0,
        pfe_kw=5.0,
        i0_percent=0.2,
        shift_degree=30.0,
        name="xfmr_pcc_to_lv",
    )

    line_lv_idx = pp.create_line_from_parameters(
        net,
        from_bus=b_lv_main,
        to_bus=b_it,
        length_km=0.2,
        r_ohm_per_km=0.06,
        x_ohm_per_km=0.04,
        c_nf_per_km=100.0,
        max_i_ka=3.0,
        name="lv_feeder",
    )
    pp.create_switch(net, bus=b_lv_main, element=line_lv_idx, et="l", closed=True, name="brk_ups")
    pp.create_load(net, bus=b_it, p_mw=cfg.load_mw, q_mvar=cfg.load_mvar, name="it_load")

    pp.create_storage(
        net,
        bus=b_lv_main,
        p_mw=0.0,
        max_e_mwh=cfg.battery_mwh,
        soc_percent=80.0,
        min_e_mwh=0.2 * cfg.battery_mwh,
        max_p_mw=cfg.battery_mw,
        min_p_mw=-cfg.battery_mw,
        name="ups_battery",
    )

    pp.create_gen(
        net,
        bus=b_lv_main,
        p_mw=cfg.diesel_mw * 0.5,
        vm_pu=1.0,
        name="diesel_gen",
        in_service=False,
        slack=True,
    )

    return SystemModel(
        name=cfg.name,
        network_engine="pandapower",
        net=net,
        metadata={
            "nominal_frequency_hz": cfg.base_frequency_hz,
            "diesel_start_delay_s": 60.0,
            "ups_fault_transfer_delay_s": 0.1,
        },
        state={
            "ups_mode": "normal",
            "fault_active": False,
            "grid_available": True,
            "diesel_running": False,
            "load_scale": 1.0,
            "notes": [],
        },
    )
