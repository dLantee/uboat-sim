from __future__ import annotations

from PySide6 import QtWidgets

from uboatsim.sim.world import World, WorldConfig
from uboatsim.sim.entity import Submarine, Ship
from uboatsim.ui.main_window import MainWindow
from uboatsim.utils.units import knots_to_mps, deg_to_rad


def build_demo_world() -> World:
    """
    Creates a small demo scenario so the UI has something to show:
    - 1 submarine at origin
    - 1 ship moving across the screen
    """
    cfg = WorldConfig(
        fixed_dt=1.0 / 30.0,
        max_substeps=5,
        time_scale=1.0,
        paused=False,
        seed=12345,
    )
    world = World(config=cfg)

    # Player submarine
    sub = Submarine(eid="U-47")
    sub.set_pos(0.0, 0.0)
    sub.set_speed(knots_to_mps(6.0))
    sub.set_course(deg_to_rad(0.0))         # 0° = North
    # sub.set_course_speed(deg_to_rad(0.0), knots_to_mps(6.0))  # 0° = North
    world.add(sub)

    # Simple target ship (for now no ShipItem is implemented, but it will exist in sim)
    ship = Ship(eid="TRG-1")
    ship.set_pos(6000.0, 2000.0)
    ship.set_speed(knots_to_mps(6.0))
    ship.set_course(deg_to_rad(270.0))      # West
    # ship.set_course_speed(deg_to_rad(270.0), knots_to_mps(12.0))  # West
    world.add(ship)

    return world

def trigger_events(world: World) -> None:
    """Example event: after 10 seconds, change the ship's course and speed."""
    # After 3 seconds, turn the ship west and speed up to 8 knots
    if world.get_time() > 3.0:
        world.get("U-47").set_course(deg_to_rad(70.0))
        world.get("U-47").set_speed(knots_to_mps(12.0))
    if world.get_time() > 6.0:
        world.get("U-47").set_course(deg_to_rad(320.0))


def main() -> None:
    app = QtWidgets.QApplication([])
    app.setApplicationName("UBoatSim")
    app.setOrganizationName("uboatsim")

    world = build_demo_world()

    window = MainWindow(world=world)
    window.resize(1280, 800)
    window.show()

    # window.timer.timeout.connect(lambda: trigger_events(world))
    window.timer.start(16)

    app.exec()


if __name__ == "__main__":
    main()