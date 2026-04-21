from PyDML.controls.supervisory import DieselController, UPSController


def test_ups_transfers_to_battery_when_grid_bad():
    ups = UPSController()
    mode = ups.update(
        current_mode="rectifier_feed",
        grid_available=True,
        v_pcc_pu=0.82,
        f_pcc_hz=59.8,
        diesel_running=False,
    )
    assert mode == "battery_feed"


def test_diesel_starts_after_delay():
    diesel = DieselController(start_delay_s=1.0, min_runtime_s=0.0)
    running = False
    running = diesel.update(t_s=0.0, grid_available=False, diesel_running=running)
    assert running is False
    running = diesel.update(t_s=1.0, grid_available=False, diesel_running=running)
    assert running is True
