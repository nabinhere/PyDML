"""State-based UPS and diesel supervisory control."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class UPSController:
    undervoltage_threshold_pu: float = 0.9
    overvoltage_threshold_pu: float = 1.1
    underfrequency_hz: float = 59.0
    overfrequency_hz: float = 61.0

    def update(
        self,
        current_mode: str,
        grid_available: bool,
        v_pcc_pu: float | None,
        f_pcc_hz: float | None,
        diesel_running: bool,
    ) -> str:
        """Return next UPS mode based on disturbance and source availability."""

        if not grid_available:
            if diesel_running:
                return "diesel_support"
            return "battery_feed"

        if v_pcc_pu is None or f_pcc_hz is None:
            return "battery_feed"

        disturbed = (
            v_pcc_pu < self.undervoltage_threshold_pu
            or v_pcc_pu > self.overvoltage_threshold_pu
            or f_pcc_hz < self.underfrequency_hz
            or f_pcc_hz > self.overfrequency_hz
        )
        if disturbed:
            return "battery_feed"

        if current_mode in {"battery_feed", "diesel_support"} and diesel_running:
            return "recovery"
        return "rectifier_feed"


@dataclass(slots=True)
class DieselController:
    start_delay_s: float = 60.0
    min_runtime_s: float = 30.0

    _grid_loss_start_s: float | None = None
    _diesel_start_s: float | None = None

    def update(self, t_s: float, grid_available: bool, diesel_running: bool) -> bool:
        """Return whether diesel should be running at this time."""

        if not grid_available:
            if self._grid_loss_start_s is None:
                self._grid_loss_start_s = t_s
            if (t_s - self._grid_loss_start_s) >= self.start_delay_s:
                if self._diesel_start_s is None:
                    self._diesel_start_s = t_s
                return True
            return diesel_running

        self._grid_loss_start_s = None
        if not diesel_running:
            self._diesel_start_s = None
            return False
        if self._diesel_start_s is None:
            return False
        return (t_s - self._diesel_start_s) < self.min_runtime_s
