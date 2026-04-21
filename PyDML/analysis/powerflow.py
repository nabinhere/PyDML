"""Power-flow and network metrics."""

from __future__ import annotations

from typing import Any

from PyDML.types import PowerFlowResults, SystemModel


def _safe_row_name(df: Any, idx: int) -> str:
    if "name" in df.columns and isinstance(df.at[idx, "name"], str):
        return df.at[idx, "name"]
    return str(idx)


def run_power_flow(system: SystemModel) -> PowerFlowResults:
    """Run AC power flow on the pandapower network and return summarized metrics."""

    try:
        import pandapower as pp
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "pandapower is required to run power flow. Install with `pip install -e \".[sim]\"`."
        ) from exc

    net = system.net
    notes: list[str] = []
    converged = True
    try:
        pp.runpp(net, init="results", calculate_voltage_angles=True)
    except Exception as exc:  # pragma: no cover - protective path
        converged = False
        notes.append(f"runpp_failed:{type(exc).__name__}")

    bus_vm: dict[str, float] = {}
    line_load: dict[str, float] = {}
    trafo_load: dict[str, float] = {}
    gen_p: dict[str, float] = {}

    if converged:
        for idx in net.bus.index:
            bus_vm[_safe_row_name(net.bus, idx)] = float(net.res_bus.at[idx, "vm_pu"])
        if len(net.line.index) > 0 and hasattr(net, "res_line"):
            for idx in net.line.index:
                line_load[_safe_row_name(net.line, idx)] = float(net.res_line.at[idx, "loading_percent"])
        if len(net.trafo.index) > 0 and hasattr(net, "res_trafo"):
            for idx in net.trafo.index:
                trafo_load[_safe_row_name(net.trafo, idx)] = float(
                    net.res_trafo.at[idx, "loading_percent"]
                )
        if len(net.gen.index) > 0 and hasattr(net, "res_gen"):
            for idx in net.gen.index:
                gen_p[_safe_row_name(net.gen, idx)] = float(net.res_gen.at[idx, "p_mw"])
    else:
        notes.append("No result tables available due to solver failure.")

    return PowerFlowResults(
        converged=converged,
        bus_vm_pu=bus_vm,
        line_loading_pct=line_load,
        trafo_loading_pct=trafo_load,
        generator_p_mw=gen_p,
        notes=notes,
    )
