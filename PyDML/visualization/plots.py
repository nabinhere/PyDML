"""Scenario plotting helpers."""

from __future__ import annotations

from PyDML.types import ScenarioResults


def plot_scenario(results: ScenarioResults):
    """Plot voltage and frequency traces for a scenario."""

    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("matplotlib is required for plotting. Install with `pip install -e \".[viz]\"`.") from exc

    t = results.time_s
    vpcc = [r.get("v_pcc_pu") for r in results.records]
    f = [r.get("f_pcc_hz") for r in results.records]

    fig, axes = plt.subplots(2, 1, sharex=True, figsize=(8, 5))
    axes[0].plot(t, vpcc, label="PCC Voltage (pu)")
    axes[0].set_ylabel("Voltage (pu)")
    axes[0].grid(True, alpha=0.25)
    axes[0].legend(loc="best")

    axes[1].plot(t, f, label="PCC Frequency (Hz)", color="tab:orange")
    axes[1].set_ylabel("Frequency (Hz)")
    axes[1].set_xlabel("Time (s)")
    axes[1].grid(True, alpha=0.25)
    axes[1].legend(loc="best")
    fig.tight_layout()
    return fig
