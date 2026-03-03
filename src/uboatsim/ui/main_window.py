from __future__ import annotations

import time
from PySide6 import QtCore, QtGui, QtWidgets

from uboatsim.sim.world import World
from .scene import RadarScene
from .view import RadarView


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, world: World, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("UBoatSim - Attack Disc Trainer")

        self.world = world

        # Scene + View
        self.scene = RadarScene(world=self.world)
        self.view = RadarView(scene=self.scene)
        self.setCentralWidget(self.view)

        # Status bar (handy during early development)
        self.status = self.statusBar()
        self.status.showMessage("Ready")

        # Simulation clock
        self._last_t = time.perf_counter()

        # Timer-driven loop (UI thread)
        self.timer = QtCore.QTimer(self)
        self.timer.setTimerType(QtCore.Qt.TimerType.PreciseTimer)
        self.timer.timeout.connect(self._on_tick)
        # self.timer.start(16)  # ~60 FPS

        # Basic key controls
        self._install_shortcuts()

    def _install_shortcuts(self) -> None:
        QtGui.QShortcut(QtGui.QKeySequence("Space"), self, activated=self._toggle_pause)
        QtGui.QShortcut(QtGui.QKeySequence("+"), self, activated=lambda: self._bump_time_scale(2.0))
        QtGui.QShortcut(QtGui.QKeySequence("-"), self, activated=lambda: self._bump_time_scale(0.5))
        QtGui.QShortcut(QtGui.QKeySequence("0"), self, activated=lambda: self._set_time_scale(1.0))

    def _toggle_pause(self) -> None:
        self.world.set_paused(not self.world.config.paused)
        self.status.showMessage(f"Paused={self.world.config.paused}  TimeScale={self.world.config.time_scale:g}")

    def _bump_time_scale(self, mul: float) -> None:
        self._set_time_scale(self.world.config.time_scale * mul)

    def _set_time_scale(self, scale: float) -> None:
        scale = max(0.05, min(200.0, float(scale)))
        self.world.set_time_scale(scale)
        self.status.showMessage(f"Paused={self.world.config.paused}  TimeScale={self.world.config.time_scale:g}")

    @QtCore.Slot()
    def _on_tick(self) -> None:
        now = time.perf_counter()
        dt_real = now - self._last_t
        self._last_t = now

        # Step sim (fixed dt for determinism)
        self.world.step(dt_real, use_fixed_dt=True)

        # Update scene items from sim state
        self.scene.sync_from_world()

        # Lightweight HUD info
        self.status.showMessage(
            f"t={self.world.get_time():.2f}s  entities={len(list(self.world.entities()))}  "
            f"paused={self.world.config.paused}  x{self.world.config.time_scale:g}"
        )