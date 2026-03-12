from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets
import numpy as np
import math


class RangeRingsOverlay(QtWidgets.QGraphicsItem):
    """
    Draw concentric rings around the player sub to help estimate range.
    """
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._center = QtCore.QPointF(0.0, 0.0)
        self._rings_m = [500.0, 1000.0, 2000.0, 4000.0]  # meters
        self._pen = QtGui.QPen(QtGui.QColor(0, 90, 70, 160), 1.0)
        self.setZValue(1000)

    def set_center(self, x: float, y: float) -> None:
        self._center = QtCore.QPointF(float(x), float(y))
        self.update()

    def set_rings(self, rings_m: list[float]) -> None:
        self._rings_m = [float(r) for r in rings_m]
        self.update()

    def boundingRect(self) -> QtCore.QRectF:
        if not self._rings_m:
            return QtCore.QRectF()
        r = max(self._rings_m)
        return QtCore.QRectF(self._center.x() - r, self._center.y() - r, 2 * r, 2 * r)

    def paint(self, painter: QtGui.QPainter, option, widget=None) -> None:
        painter.setPen(self._pen)
        painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)

        cx, cy = self._center.x(), self._center.y()
        for r in self._rings_m:
            painter.drawEllipse(QtCore.QPointF(cx, cy), r, r)


class BearingLineOverlay(QtWidgets.QGraphicsItem):
    """
    Click-drag bearing/range tool: origin anchored at player sub.
    Target follows mouse position in scene coords.
    """
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._origin = QtCore.QPointF(0.0, 0.0)
        self._target = QtCore.QPointF(0.0, 0.0)
        self._visible = False

        self._pen = QtGui.QPen(QtGui.QColor(0, 200, 140, 200), 1.5)
        self._text_pen = QtGui.QPen(QtGui.QColor(120, 240, 200), 1.0)
        self.setZValue(1100)

    def set_visible(self, v: bool) -> None:
        self._visible = bool(v)
        self.update()

    def set_origin(self, x: float, y: float) -> None:
        self._origin = QtCore.QPointF(float(x), float(y))
        self.update()

    def set_target(self, x: float, y: float) -> None:
        self._target = QtCore.QPointF(float(x), float(y))
        self.update()

    def boundingRect(self) -> QtCore.QRectF:
        # Conservative bounds around the segment
        x1, y1 = self._origin.x(), self._origin.y()
        x2, y2 = self._target.x(), self._target.y()
        left = min(x1, x2) - 50
        top = min(y1, y2) - 50
        right = max(x1, x2) + 50
        bottom = max(y1, y2) + 50
        return QtCore.QRectF(left, top, right - left, bottom - top)

    def paint(self, painter: QtGui.QPainter, option, widget=None) -> None:
        if not self._visible:
            return

        painter.setPen(self._pen)
        painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)

        o = self._origin
        t = self._target
        painter.drawLine(o, t)

        # Compute range + nautical bearing (0=N, 90=E) in degrees for display
        dx = float(t.x() - o.x())
        dy = float(t.y() - o.y())
        rng = math.hypot(dx, dy)

        # Bearing calculation for Qt's Y-down coordinate system:
        # In Qt: -Y is north (up state screen), +X is east
        # So we need atan2(dx, -dy) for nautical bearing (0=N, 90=E clockwise)
        bearing_rad = math.atan2(dx, -dy)
        bearing_deg = (math.degrees(bearing_rad) + 360.0) % 360.0

        painter.setPen(self._text_pen)
        painter.drawText(
            t + QtCore.QPointF(10.0, 10.0),
            f"{bearing_deg:06.2f}°  {rng:,.0f} m"
        )