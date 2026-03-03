from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets
import math


class ShipItem(QtWidgets.QGraphicsItem):
    """
    Simple ship marker. Position in scene == world meters (1:1 scale).
    Heading rotates the triangle.
    """

    def __init__(self, eid: str, parent=None) -> None:
        super().__init__(parent)
        self.eid = eid

        self._heading_rad: float = 0.0
        self._size: float = 30.0  # meters/pixels
        self._pen = QtGui.QPen(QtGui.QColor(100, 0, 0), 1.0)
        self._brush = QtGui.QBrush(QtGui.QColor(255, 0, 0, 255))

        self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations, False)
        self.setZValue(10)

    def boundingRect(self) -> QtCore.QRectF:
        s = self._size
        return QtCore.QRectF(-s, -s, 2 * s, 2 * s)

    def paint(self, painter: QtGui.QPainter, option, widget=None) -> None:
        painter.setPen(self._pen)
        painter.setBrush(self._brush)

        # Triangle points (pointing -Y which is "up" on screen)
        # In Qt, Y increases downward, so -Y is "north/up"
        s = self._size
        pts = [
            QtCore.QPointF(0.0, -s),         # nose (pointing up/north on screen)
            QtCore.QPointF(-0.6 * s, -0.6 * s),  # left wing (down)
            QtCore.QPointF(-0.6 * s, 0.6 * s),  # left wing (down)
            QtCore.QPointF(0.6 * s, 0.6 * s),  # right wing (down)
            QtCore.QPointF(0.6 * s, -0.6 * s),  # right wing (down)
        ]
        poly = QtGui.QPolygonF(pts)

        painter.save()
        # In sim: 0 rad = North, π/2 = East (clockwise)
        # In Qt: Y-down means we rotate clockwise (positive angle) for headings
        # We negate because Qt's rotation is counterclockwise positive, but we want clockwise
        painter.rotate(math.degrees(self._heading_rad))
        painter.drawPolygon(poly)
        painter.restore()

        # Optional label
        painter.setPen(QtGui.QPen(QtGui.QColor(120, 220, 180), 1.0))
        painter.drawText(QtCore.QPointF(self._size * 0.8, -self._size * 0.8), self.eid)

    def set_pose(self, x: float, y: float, heading_rad: float) -> None:
        # Updating geometry/appearance
        self.prepareGeometryChange()
        self.setPos(float(x), float(y))
        self._heading_rad = float(heading_rad)
        self.update()