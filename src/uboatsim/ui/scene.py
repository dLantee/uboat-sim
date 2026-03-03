from __future__ import annotations

from typing import Dict, Optional
from PySide6 import QtCore, QtGui, QtWidgets

from uboatsim.sim.world import World
from uboatsim.sim.entity import Submarine, Ship
from .items.ship_item import ShipItem

from .items.sub_item import SubItem
from .items.overlays import RangeRingsOverlay, BearingLineOverlay

from uboatsim.utils.units import knots_to_mps, deg_to_rad, vector_to_rad, rad_to_vector
from uboatsim.utils.math import v2


class RadarScene(QtWidgets.QGraphicsScene):
    """
    Owns all QGraphicsItems and overlay tools.
    Simulation state -> graphics state should be one-way (world -> scene).
    """

    def __init__(self, world: World, parent=None) -> None:
        super().__init__(parent)
        self.world = world

        # World->Item mapping
        self._sub_items: Dict[str, SubItem] = {}
        self._enemy_items: Dict[str, ShipItem] = {}

        # Overlays (drawn above entities)
        self.range_rings = RangeRingsOverlay()
        self.bearing_line = BearingLineOverlay()

        self.addItem(self.range_rings)
        self.addItem(self.bearing_line)

        # Visual defaults
        self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(5, 10, 8)))
        self.setSceneRect(-20_000, -20_000, 40_000, 40_000)  # meters as pixels (1:1) for now

        # Mouse interactions for overlays
        self._dragging_bearing: bool = False

    def sync_from_world(self) -> None:
        """
        Create/update QGraphicsItems to match the current sim world.
        Call this once per UI tick after world.step().
        """
        # Ensure submarine item(s) exist
        for e in self.world.entities():
            if not e.alive:
                continue
            if isinstance(e, Submarine):
                if e.eid not in self._sub_items:
                    item = SubItem(eid=e.eid)
                    self._sub_items[e.eid] = item
                    self.addItem(item)

                self._sub_items[e.eid].set_pose(
                    x=e.kin.pos[0],
                    y=-e.kin.pos[1],  # Negate Y: sim uses Y-up, Qt uses Y-down
                    heading_rad=e.kin.heading,
                )
            if isinstance(e, Ship):
                if e.eid not in self._enemy_items:
                    item = ShipItem(eid=e.eid)
                    self._enemy_items[e.eid] = item
                    self.addItem(item)

                self._enemy_items[e.eid].set_pose(
                    x=e.kin.pos[0],
                    y=-e.kin.pos[1],  # Negate Y: sim uses Y-up, Qt uses Y-down
                    heading_rad=e.kin.heading,
                )

        # Choose a "player sub" for overlays (first sub for now)
        player = self._get_player_sub()
        if player:
            self.range_rings.set_center(player.kin.pos[0], -player.kin.pos[1])
            self.bearing_line.set_origin(player.kin.pos[0], -player.kin.pos[1])

    def _get_player_sub(self) -> Optional[Submarine]:
        for e in self.world.entities():
            if isinstance(e, Submarine) and e.alive:
                return e
        return None

    # -----------------
    # Overlay interaction (move to, bearing line tool)
    # -----------------

    def mousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self._dragging_bearing = True
            p = event.scenePos()
            self.bearing_line.set_target(p.x(), p.y())
            self.bearing_line.set_visible(True)
            event.accept()
            return
        if event.button() == QtCore.Qt.MouseButton.RightButton:
            # Set target position for player sub (if it exists)
            player = self._get_player_sub()
            if player:
                p = event.scenePos()
                offset = v2(p.x(), -p.y()) - player.kin.pos
                player.set_course(vector_to_rad(offset))  # Negate Y: sim uses Y-up, Qt uses Y-down
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        if self._dragging_bearing:
            p = event.scenePos()
            self.bearing_line.set_target(p.x(), p.y())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        if event.button() == QtCore.Qt.MouseButton.LeftButton and self._dragging_bearing:
            self._dragging_bearing = False
            event.accept()
            return
        super().mouseReleaseEvent(event)