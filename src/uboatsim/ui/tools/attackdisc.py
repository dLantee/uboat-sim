"""

"""
import math
import sys
from dataclasses import dataclass, field
from typing import List, Tuple
import numpy as np

from PySide6 import QtCore, QtGui, QtWidgets


def clamp_angle_deg(a: float) -> float:
    # Keep angles in [0, 360)
    a = a % 360.0
    if a < 0:
        a += 360.0
    return a


def pos_to_angle_deg(p: QtCore.QPointF) -> float:
    # Qt: +x right, +y down. We want 0° at "up" and clockwise positive like bearings.
    x, y = p.x(), p.y()
    ang = math.degrees(math.atan2(y, x))  # 0 state +x, ccw positive (but y is down -> flipped)
    # Convert so that 0 is up and increases clockwise:
    bearing = 90.0 + ang
    return clamp_angle_deg(bearing)


def scene_pos_to_angle_deg(p: QtCore.QPointF, center: QtCore.QPointF) -> float:
    # Stable angle in scene coords regardless of item rotation.
    return pos_to_angle_deg(p - center)


@dataclass
class TickSpec:
    step_deg: float             # degrees between ticks (e.g. 1 for every degree)
    long_every: int             # how many ticks between long ticks (e.g. 5 for long tick_specs every 5 degrees)
    long_len: float             # length of long ticks in pixels
    short_len: float            # length of short ticks in pixels
    start_deg: float = 0.0      # starting angle for first tick (default: 0, i.e. 0° at "up" state screen)
    end_deg: float = 360.0      # ending angle for last tick (default
    pen_width: float = 1.0      # width of tick_specs lines in pixels
    radial_offset: float = 0.0  # radial offset of ticks from ring edge in pixels (positive = outward)
    reverse: bool = False       # If true, ticks point inward instead of outward. (Default: False)
    color: QtGui.QColor = field(default_factory=lambda: QtGui.QColor(100, 100, 100))


@dataclass
class LabelSpec:
    """LabelSpec is related to TickSpec by index. If label_every_long > 0, labels are drawn for every label_every_long'th long tick."""
    step_num: float = 1.0       # number to increment for each label (e.g. 10 for labels every 10 degrees)
    start_num: float = 0.0      # number to label at start_deg (default: 0)
    label_every_long: int = 0   # how many long ticks between labels (e.g. 2 for label every 10 degrees if long ticks every 5 degrees)
    radius: float | None = None # radius at which to place labels (if label_every_long > 0)
    font_size: int = 12
    bold: bool = False
    color: QtGui.QColor = field(default_factory=lambda: QtGui.QColor(100, 100, 100))


@dataclass
class CircleSpec:
    radius: float
    pen_width: float = 1.0
    color: QtGui.QColor = field(default_factory=lambda: QtGui.QColor(100, 100, 100))


class RotatableLayer(QtWidgets.QGraphicsObject):
    """
    Base class for rotatable disc layers.
    - Draw centered at (0,0)
    - Rotate around center
    - Drag with mouse to rotate
    """
    def __init__(self, radius: float, z: float = 0.0, draggable: bool = True, parent=None):
        super().__init__(parent)
        self.radius = radius
        self.setZValue(z)
        self.setTransformOriginPoint(0.0, 0.0)
        self.setAcceptedMouseButtons(QtCore.Qt.LeftButton)
        self._draggable = draggable

        self._dragging = False
        self._drag_start_angle = 0.0
        self._start_rotation = 0.0
        self._min_drag_radius = 12.0

    def boundingRect(self) -> QtCore.QRectF:
        r = self.radius + 2
        return QtCore.QRectF(-r, -r, 2 * r, 2 * r)

    def set_draggable(self, state: bool):
        self._draggable = state

    def mousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        if not self._draggable:
            event.ignore()
            return
        center = self.mapToScene(QtCore.QPointF(0.0, 0.0))
        if QtCore.QLineF(center, event.scenePos()).length() < self._min_drag_radius:
            event.ignore()
            return
        self._dragging = True
        self._drag_start_angle = scene_pos_to_angle_deg(event.scenePos(), center)
        self._start_rotation = self.rotation()
        event.accept()

    def mouseMoveEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        if not self._dragging:
            event.ignore()
            return
        center = self.mapToScene(QtCore.QPointF(0.0, 0.0))
        cur = scene_pos_to_angle_deg(event.scenePos(), center)
        delta = cur - self._drag_start_angle
        # handle wraparound nicely:
        if delta > 180:
            delta -= 360
        elif delta < -180:
            delta += 360
        self.setRotation(self._start_rotation + delta)
        event.accept()

    def mouseReleaseEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        self._dragging = False
        event.accept()


class TickRing(RotatableLayer):
    """
    A ring with ticks + optional numbers.

    Labels are only drawn for long ticks defined by tick_specs.
        - tick_specs define where ticks go and their styling
        - label_specs define where labels go and their styling, but only for long ticks.
    """
    def __init__(
        self,
        outer_radius: float,
        inner_radius: float,
        tick_specs: List[TickSpec],
        label_specs: List[LabelSpec] | None = None,
        circle_specs: List[CircleSpec] | None = None,
        z: float = 0.0,
        draggable: bool = True,
        ring_brush: QtGui.QBrush | None = None,
        parent=None,
    ):
        super().__init__(radius=outer_radius, z=z, draggable=draggable, parent=parent)
        self.outer_radius = outer_radius
        self.inner_radius = inner_radius
        self.tick_specs = tick_specs
        self.label_specs = label_specs or []
        self.circle_specs = circle_specs or []
        self.ring_brush = ring_brush

    def paint(self, painter: QtGui.QPainter, option, widget=None) -> None:
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

        def_label_radius = (self.outer_radius + self.inner_radius) / 2

        # Fill ring
        if self.ring_brush is not None:
            path = QtGui.QPainterPath()
            path.addEllipse(QtCore.QPointF(0, 0), self.outer_radius, self.outer_radius)
            inner = QtGui.QPainterPath()
            inner.addEllipse(QtCore.QPointF(0, 0), self.inner_radius, self.inner_radius)
            path = path.subtracted(inner)
            painter.fillPath(path, self.ring_brush)

        # Ticks
        label_specs = self.label_specs if self.label_specs else [LabelSpec()] * len(self.tick_specs)
        for tick_spec, label_spec in zip(self.tick_specs, label_specs):
            pen = QtGui.QPen(tick_spec.color)
            pen.setWidthF(tick_spec.pen_width)
            painter.setPen(pen)
            font = QtGui.QFont("Arial", label_spec.font_size)
            font.setBold(label_spec.bold)
            painter.setFont(font)

            deg_range = tick_spec.end_deg - tick_spec.start_deg
            if tick_spec.end_deg < tick_spec.start_deg:
                deg_range += 360.0

            # TODO: Add logarithmic tick spacing option. For now just use linear spacing.
            # labels = label_spec.values if label_spec.values else []
            # vmin = min(labels)
            # vmax = max(labels)
            # degrees = np.degree(2 * np.pi * (np.log(values) - np.log(vmin)) / (np.log(vmax) - np.log(vmin)))

            label_idx = 0  # label index
            steps = int(deg_range / tick_spec.step_deg)

            degrees = [tick_spec.start_deg + i * tick_spec.step_deg for i in range(steps)]

            for i, deg in enumerate(degrees):
                # deg = tick_spec.start_deg + i * tick_spec.step_deg

                # Draw ticks
                is_long = (i % tick_spec.long_every) == 0
                length = tick_spec.long_len if is_long else tick_spec.short_len

                start_radius = self.outer_radius if tick_spec.reverse else self.inner_radius
                end_radius = start_radius - length - 1 if tick_spec.reverse else start_radius + length + 1
                radial_offset = -tick_spec.radial_offset if tick_spec.reverse else tick_spec.radial_offset

                p1 = self._polar(start_radius + radial_offset, deg)
                p2 = self._polar(end_radius + radial_offset, deg)
                painter.drawLine(p1, p2)

                # Draw labels (0..350)
                if is_long and label_spec.label_every_long > 0 and (i % (tick_spec.long_every * label_spec.label_every_long)) == 0:
                    pt = self._polar(label_spec.radius or def_label_radius, deg)
                    txt = str(int(label_spec.start_num + label_idx * label_spec.step_num))
                    label_idx += 1
                    metrics = QtGui.QFontMetrics(font)
                    w = metrics.horizontalAdvance(txt)
                    h = metrics.height()
                    pivot = QtCore.QPoint(int(-w/2), int(h/2))
                    painter.save()
                    painter.translate(pt)   # move the coordinate system to the label position
                    painter.rotate(deg)
                    painter.drawText(pivot, txt)    # draw regarding the coordinate system
                    # TODO: Use label_spec.color for text color, but need to set pen
                    #  before drawing ticks if we want different colors for ticks vs labels.
                    #  For now just use tick_spec.color for both.
                    # pen = QtGui.QPen(label_spec.color)
                    # painter.setPen(pen)
                    # painter.setPen(pen)
                    # pen.setColor(label_spec.color)
                    # painter.setPen(pen)
                    painter.restore()

        # Draw circles
        for circ in self.circle_specs:
            pen = QtGui.QPen(circ.color)
            pen.setWidthF(circ.pen_width)
            painter.setPen(pen)
            painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QtCore.QPointF(0, 0), circ.radius, circ.radius)

    @staticmethod
    def _polar(r: float, deg: float) -> QtCore.QPointF:
        # bearing deg: 0 up, cw positive
        rad = math.radians(deg)
        x = r * math.sin(rad)
        y = -r * math.cos(rad)
        return QtCore.QPointF(x, y)


class RelativeBearingDisc(TickRing):
    """
    Outer ring with bearing ticks every 1 degree and labels every 10 degrees.
    """
    def __init__(self, z: float, parent=None):
        super().__init__(
            outer_radius=600,
            inner_radius=500,
            tick_specs=[TickSpec(step_deg=1, long_every=5, long_len=50,
                                 short_len=30, pen_width=3.5, radial_offset=15,
                                 reverse=False, start_deg=180, end_deg=540,
                                 color=QtGui.QColor(220, 220, 220, 200))],
            label_specs=[LabelSpec(label_every_long=2, radius=585, start_num=0, step_num=10,
                                   font_size=15, bold=True, color=QtGui.QColor(220, 220, 220, 200))],
            z=z,
            draggable=False,
            ring_brush=QtGui.QBrush(QtGui.QColor(70, 45, 50)),
            parent=parent
        )

    def paint(self, painter: QtGui.QPainter, option, widget=None) -> None:
        super().paint(painter, option, widget)

        # Add decoration: North arrowhead
        arrow_north = QtGui.QPolygonF([
            QtCore.QPointF(0, -self.inner_radius),
            QtCore.QPointF(10, -self.inner_radius - 15),
            QtCore.QPointF(-10, -self.inner_radius - 15)])
        painter.setBrush(self.tick_specs[0].color)
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.drawPolygon(arrow_north)


class CompassRoseDisc(TickRing):

    def __init__(self, z: float, parent=None):
        super().__init__(
            outer_radius=500,
            inner_radius=330,
            tick_specs=[TickSpec(step_deg=1, long_every=5, long_len=55, radial_offset=0,
                                 short_len=35, pen_width=2.0, reverse=True,
                                 start_deg=0, color=QtGui.QColor(0, 0, 0)),
                        TickSpec(step_deg=1, long_every=5, long_len=20, radial_offset=90,
                                 short_len=7, pen_width=2.0, reverse=True,
                                 start_deg=180, end_deg=540, color=QtGui.QColor(0, 0, 0))
                        ],
            label_specs=[LabelSpec(step_num=10, label_every_long=2, radius=430, start_num=0, font_size=14, bold=False, color=QtGui.QColor(0, 0, 0)),
                         LabelSpec(step_num=10, label_every_long=2, radius=380, start_num=0, font_size=11, bold=False, color=QtGui.QColor(0, 0, 0))],
            circle_specs=[CircleSpec(radius=500, pen_width=2.0, color=QtGui.QColor(0, 0, 0)),
                          CircleSpec(radius=410, pen_width=2.0, color=QtGui.QColor(0, 0, 0))],
            z=z,
            draggable=True,
            ring_brush=QtGui.QBrush(QtGui.QColor(200, 195, 170)),
        )

    def paint(self, painter: QtGui.QPainter, option, widget=None) -> None:
        super().paint(painter, option, widget)

#
# class SpeedArcRing(RotatableLayer):
#     """
#     A ring that draws red/green arc segments like the speed scale.
#     """
#     def __init__(self, radius: float, thickness: float, z: float, draggable: bool = True, parent=None):
#         super().__init__(radius=radius + thickness, z=z, draggable=draggable, parent=parent)
#         self.radius = radius
#         self.thickness = thickness
#
#     def boundingRect(self) -> QtCore.QRectF:
#         r = self.radius + self.thickness + 2
#         return QtCore.QRectF(-r, -r, 2 * r, 2 * r)
#
#     def paint(self, painter: QtGui.QPainter, option, widget=None) -> None:
#         painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
#
#         rect = QtCore.QRectF(
#             -(self.radius + self.thickness / 2),
#             -(self.radius + self.thickness / 2),
#             2 * (self.radius + self.thickness / 2),
#             2 * (self.radius + self.thickness / 2),
#         )
#
#         # In Qt, angles are in 1/16 degrees, 0 at 3 o'clock, CCW positive.
#         # We'll define arcs by bearings and convert.
#         def bearing_to_qt16(bearing_deg: float) -> int:
#             # bearing: 0 up cw+ -> qt: 0 right ccw+
#             qt_deg = 90 - bearing_deg
#             return int(qt_deg * 16)
#
#         pen = QtGui.QPen(QtGui.QColor(30, 200, 80))
#         pen.setWidthF(self.thickness)
#         pen.setCapStyle(QtCore.Qt.RoundCap)
#         painter.setPen(pen)
#         # green arc segment (example)
#         painter.drawArc(rect, bearing_to_qt16(210), int(-120 * 16))
#
#         pen.setColor(QtGui.QColor(220, 60, 60))
#         painter.setPen(pen)
#         # red arc segment (example)
#         painter.drawArc(rect, bearing_to_qt16(30), int(-120 * 16))


class AngleOnBowDisc(TickRing):
    """
    A disc with ticks every 10 degrees and labels every 30 degrees, used for angle-on-bow display.
    """
    def __init__(self, z: float, parent=None):
        super().__init__(
            outer_radius=330,
            inner_radius=100,
            tick_specs=[TickSpec(step_deg=1, long_every=5, long_len=16, radial_offset=0,
                                 short_len=7, pen_width=1.5, reverse=True,
                                 start_deg=0, end_deg=180,
                                 color=QtGui.QColor(200, 0, 0)),
                        TickSpec(step_deg=1, long_every=5, long_len=16, radial_offset=0,
                                 short_len=7, pen_width=1.5, reverse=True,
                                 start_deg=180, end_deg=360,
                                 color=QtGui.QColor(0, 120, 0))
                        ],
            label_specs=[LabelSpec(step_num=10, label_every_long=2, radius=300, start_num=0, font_size=11, bold=False, color=QtGui.QColor(200, 0, 0)),
                         LabelSpec(step_num=-10, label_every_long=2, radius=300, start_num=180, font_size=11, bold=False, color=QtGui.QColor(0, 120, 0))],
            # circle_specs=[CircleSpec(radius=300, pen_width=2.0, color=QtGui.QColor(0, 0, 0))],
            z=z,
            draggable=True,
            ring_brush=QtGui.QBrush(QtGui.QColor(237, 237, 237)),
            parent=parent
        )

    def _pointer_path(self) -> QtGui.QPainterPath:
        path = QtGui.QPainterPath()
        W = 100
        L = 230
        poly = QtGui.QPolygonF([
            QtCore.QPointF(-W / 2, -self.outer_radius+5),
            QtCore.QPointF(W / 2, -self.outer_radius+5),
            QtCore.QPointF(W / 2 - 25, -(self.outer_radius + L)),
            QtCore.QPointF(-W/2 + 25, -(self.outer_radius + L)),
            QtCore.QPointF(-W / 2, -self.outer_radius+5),
        ])
        path.addPolygon(poly)
        return path

    def paint(self, painter: QtGui.QPainter, option, widget=None) -> None:
        # draw a long rectangle from center to outward (pointing "up" at rotation=0)
        path = self._pointer_path()
        painter.fillPath(path, QtGui.QColor(0, 0, 0, 50))
        painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0, 180), 1.5))
        painter.drawPath(path)

        # Add decoration: arrowhead
        radial_offset = -175
        arrowhead = QtGui.QPolygonF([
            QtCore.QPointF(0, -self.outer_radius + 30 + radial_offset),
            QtCore.QPointF(10, -self.outer_radius + radial_offset),
            QtCore.QPointF(-10, -self.outer_radius + radial_offset),])
        painter.setBrush(QtGui.QColor(120, 0, 0, 230))
        # painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setPen(QtGui.QPen(QtGui.QColor(190, 0, 0, 180), 1.0))
        painter.drawPolygon(arrowhead)

        # Draw the rest of the disc on top of the pointer
        super().paint(painter, option, widget)

        painter.setBrush(QtGui.QColor(204, 171, 138))
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.drawEllipse(QtCore.QPoint(0, 0), 260, 260)

        # Add decoration: ship silhouette
        scl = -2.0
        ship = QtGui.QPolygonF([
            QtCore.QPointF(0 * scl, -100 * scl),
            QtCore.QPointF(30 * scl, -100 * scl),
            QtCore.QPointF(40 * scl, 0 * scl),
            QtCore.QPointF(30 * scl, 100 * scl),
            QtCore.QPointF(0 * scl, 140 * scl),
            QtCore.QPointF(-30 * scl, 100 * scl),
            QtCore.QPointF(-40 * scl, 0 * scl),
            QtCore.QPointF(-30 * scl, -100 * scl),
            QtCore.QPointF(0 * scl, -100 * scl),
        ])
        # painter.setBrush(QtGui.QColor(120, 0, 0, 230))
        painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0), 1.5))
        painter.drawPolygon(ship)




class AttackCoursePointer(RotatableLayer):
    """
    Simple transparent ruler/arm overlay. Rotatable.
    """
    def __init__(self, length: float = 525, width: float = 42, z: float = 0, parent=None):
        super().__init__(radius=length, z=z, draggable=True, parent=parent)
        self.length = length
        self.width = width

    def boundingRect(self) -> QtCore.QRectF:
        r = self.length + 10
        return QtCore.QRectF(-r, -r, 2 * r, 2 * r)

    def _pointer_path(self) -> QtGui.QPainterPath:
        path = QtGui.QPainterPath()
        w = self.width
        L = self.length
        poly = QtGui.QPolygonF([
            QtCore.QPointF(-w/2, L),
            QtCore.QPointF(w/2, L),
            QtCore.QPointF(w, 0),
            QtCore.QPointF(w/2, -L),
            QtCore.QPointF(-w/2, -L),
            QtCore.QPointF(-w, 0),
            QtCore.QPointF(-w/2, L),
        ])
        path.addPolygon(poly)
        return path

    def shape(self) -> QtGui.QPainterPath:
        return self._pointer_path()

    def paint(self, painter: QtGui.QPainter, option, widget=None) -> None:
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

        # draw a long rectangle from center to outward (pointing "up" at rotation=0)
        path = self._pointer_path()
        painter.fillPath(path, QtGui.QColor(255, 255, 255, 40))
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 120), 1.0))
        painter.drawPath(path)

        # draw a center line with an arrowhead
        painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0, 255), 2.0))
        painter.drawLine(0, self.length, 0, -self.length)
        arrow = QtGui.QPolygonF([
            QtCore.QPointF(0, self.length),
            QtCore.QPointF(10, self.length-30),
            QtCore.QPointF(-10, self.length-30),
        ])
        path = QtGui.QPainterPath()
        path.addPolygon(arrow)
        painter.fillPath(path, QtGui.QColor(0, 0, 0, 255))

        # # center marker
        # painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 200), 2.0))
        # painter.drawEllipse(QtCore.QPointF(0, 0), 8, 8)


class AttackDiscWidget(QtWidgets.QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHint(QtGui.QPainter.Antialiasing, True)
        self.setBackgroundBrush(QtGui.QColor(90, 110, 110))

        scene = QtWidgets.QGraphicsScene(self)
        self.setScene(scene)
        self.setSceneRect(-600, -600, 1200, 1200)

        # --- Layer A: Relative Bearing Disc ---
        rel_bearing_disc = RelativeBearingDisc(z=0, parent=None)
        scene.addItem(rel_bearing_disc)

        # --- Layer B: Compass Rose Disc ---
        compass_rose_disc = CompassRoseDisc(z=5, parent=None)
        scene.addItem(compass_rose_disc)

        # --- Layer C: Angle on Bow Pointer ---
        aob_disc = AngleOnBowDisc(z=10, parent=None)
        scene.addItem(aob_disc)

        # # --- Layer D: speed arc ring (example) ---
        # speed = SpeedArcRing(radius=240, thickness=26, z=2, draggable=True)
        # scene.addItem(speed)

        # # --- Layer C: fixed index marker overlay (non-rotating) ---
        # index = QtWidgets.QGraphicsPathItem()
        # index.setZValue(3)
        # p = QtGui.QPainterPath()
        # p.moveTo(0, -405)
        # p.lineTo(-18, -375)
        # p.lineTo(18, -375)
        # p.closeSubpath()
        # index.setPath(p)
        # index.setBrush(QtGui.QBrush(QtGui.QColor(235, 235, 235)))
        # index.setPen(QtGui.QPen(QtCore.Qt.NoPen))
        # scene.addItem(index)

        # --- Layer C: Attack Course Pointer ---
        ring_bearing = AttackCoursePointer(z=20)
        ring_bearing.setRotation(35)  # initial pose
        scene.addItem(ring_bearing)

        # # Center hub (visual only)
        # hub = QtWidgets.QGraphicsEllipseItem(-55, -55, 110, 110)
        # hub.setZValue(10)
        # hub.setBrush(QtGui.QBrush(QtGui.QColor(20, 20, 20)))
        # hub.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0), 2))
        # scene.addItem(hub)
        #
        # knob = QtWidgets.QGraphicsEllipseItem(-18, -18, 36, 36)
        # knob.setZValue(11)
        # knob.setBrush(QtGui.QBrush(QtGui.QColor(120, 120, 120)))
        # knob.setPen(QtGui.QPen(QtGui.QColor(30, 30, 30), 1))
        # scene.addItem(knob)

        # self.rel_bearing_disc = rel_bearing_disc
        # self.ring_speed = ring_speed
        # # self.speed = speed
        # self.ring_bearing = ring_bearing

        self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
        self.setViewportUpdateMode(QtWidgets.QGraphicsView.FullViewportUpdate)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        self.fitInView(self.sceneRect(), QtCore.Qt.KeepAspectRatio)