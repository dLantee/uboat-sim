"""

"""
import math
from typing import List, Tuple

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import QGraphicsView


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


def polar_to_vec(r: float, deg: float) -> QtCore.QPointF:
    # bearing deg: 0 up, cw positive
    rad = math.radians(deg)
    x = r * math.sin(rad)
    y = -r * math.cos(rad)
    return QtCore.QPointF(x, y)


def vec_to_polar(p: QtCore.QPointF) -> Tuple[float, float]:
    x, y = p.x(), p.y()
    r = math.hypot(x, y)
    deg = (math.degrees(math.atan2(x, -y))) % 360.0
    return r, deg


class OverLay(QtWidgets.QGraphicsItem):
    """
    Base class for simple overlays that can be added to discs or other items.
    Provides common styling options like color, pen width, font, and antialiasing.
    Subclasses should implement boundingRect() and paint().
    """
    def __init__(self, *, color:QtGui.QColor=QtGui.QColor(0, 0, 0),
                 pen_width:float=1.0,
                 font=QtGui.QFont("Arial", 12),
                 antialiasing:bool=False,
                 parent=None):
        super().__init__(parent)
        self.color = color
        self.pen_width = pen_width
        self.font = font
        self.antialiasing = antialiasing

    def paint(self, painter, option, /, widget = ...):
        """Set up common pen, font, and antialiasing for all overlays.

        Use super().paint(painter, option, widget) in subclasses to apply these settings before drawing.
        """
        painter.setRenderHint(QtGui.QPainter.Antialiasing, self.antialiasing)
        pen = QtGui.QPen(self.color)
        pen.setWidthF(self.pen_width)
        painter.setFont(self.font)
        painter.setPen(pen)


class RadialOverlay(OverLay):
    """
    Base class for overlays that draw radial patterns (e.g. ticks, arcs, labels).
    0° is "up" state screen, positive angles clockwise.
    Angles can be outside [0, 360) and will be handled correctly.
    """
    def __init__(self, radius, step_deg=1, start_deg=0,
                 span_deg=360, include_end=False, **kwargs):
        super().__init__(**kwargs)
        self.radius = radius
        self.step_deg = step_deg        # degrees between steps (e.g. 1 for every degree)
        self.start_deg = start_deg      # starting angle for first step (default: 0, i.e. 0° at "up" state screen)
        self.span_deg = span_deg        # positive cw
        self.include_end = include_end  # whether to include a step at end_deg if it falls on a step

    def boundingRect(self):
        r = self.radius + 2
        return QtCore.QRectF(-r, -r, 2 * r, 2 * r)

    @property
    def step_num(self):
        return int(self.span_deg / self.step_deg) + int(self.include_end)

    @property
    def step_values(self):
        return [self.start_deg + i * self.step_deg for i in range(self.step_num)]


class OrthogonalOverlay(OverLay):
    """
    Simple orthogonal lines (e.g. crosshairs, grids).
    """
    def __init__(self, length: float, **kwargs):
        super().__init__(**kwargs)
        self.length = length

    def boundingRect(self):
        l = self.length + 20
        return QtCore.QRectF(-l, -l, 2 * l, 2 * l)

    def paint(self, painter: QtGui.QPainter, option, widget=None) -> None:
        super().paint(painter, option, widget)
        painter.drawLine(QtCore.QPointF(0, -self.length), QtCore.QPointF(0, self.length))
        painter.drawLine(QtCore.QPointF(-self.length, 0), QtCore.QPointF(self.length, 0))


class CircleOverlay(RadialOverlay):
    """
    Simple circle overlay at specified radius.
    """
    def paint(self, painter: QtGui.QPainter, option, widget=None) -> None:
        super().paint(painter, option, widget)
        painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QtCore.QPointF(0, 0), self.radius, self.radius)


class LabelRadialOverlay(RadialOverlay):
    """
    Simple labels at specified angles. Not a full ring, just individual labels.
    """
    def __init__(self, *, start_num:int=0, num_increase:int=1, **kwargs):
        super().__init__(**kwargs)
        self.start_num = start_num
        self.num_increase = num_increase

        # optional custom labels for each step,
        # overrides default numbering if provided
        self.custom_labels = []

    def paint(self, painter: QtGui.QPainter, option, widget=None) -> None:
        super().paint(painter, option, widget)

        for i, deg in enumerate(self.step_values):
            pt = polar_to_vec(self.radius, deg)
            txt = str(int(self.start_num + i * self.num_increase))

            # if self.custom_labels:
            #     if len(self.custom_labels) != self.step_num:
            #         raise ValueError(f"Length of custom_labels ({len(self.custom_labels)}) must match number of steps ({self.step_num()})")

            # txt = self.custom_labels[i] if self.custom_labels else def_txt

            metrics = QtGui.QFontMetrics(self.font)
            w = metrics.horizontalAdvance(txt)
            h = metrics.height()
            pivot = QtCore.QPoint(int(-w / 2), int(h / 3))
            painter.save()
            painter.translate(pt)  # move the coordinate system to the label position
            painter.rotate(deg)
            painter.drawText(pivot, txt)
            painter.restore()


class TickRadialOverlay(RadialOverlay):
    """
    Simple tick marks at specified angles. Not a full ring, just individual ticks.
    """
    def __init__(self, *, long_len: float, short_len: float,
                 long_every: int, reversed:bool=False,
                 **kwargs):
        super().__init__(**kwargs)
        self.long_len = long_len
        self.short_len = short_len
        self.long_every = long_every
        self.reversed = reversed
        # self.log_scale = False  # TODO: Add option for logarithmic tick spacing

    def paint(self, painter: QtGui.QPainter, option, widget=None) -> None:
        super().paint(painter, option, widget)
        # painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

        # vmin = min(values)
        # vmax = max(values)
        # degrees = np.degree(2 * np.pi * (np.log(values) - np.log(vmin)) / (np.log(vmax) - np.log(vmin)))

        for i, deg in enumerate(self.step_values):
            is_long = (i % self.long_every) == 0
            length = self.long_len if is_long else self.short_len

            p0 = polar_to_vec(self.radius , deg)
            p1 = polar_to_vec(self.radius + length , deg)
            if self.reversed:
                p1 = polar_to_vec(self.radius - length , deg)
            painter.drawLine(p0, p1)


class RotatableObjet(QtWidgets.QGraphicsObject):
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


class ShapeObjet(RotatableObjet):
    """
    Base class for rotatable layers with custom shapes.
    Subclasses should implement shape() to return a QPainterPath, and paint() to draw it.
    """
    def __init__(self,
                 pen:QtGui.QPen | None = None,
                 brush:QtGui.QBrush | None = None,
                 **kwargs) -> None:
        super().__init__(**kwargs)
        self.overlays = []
        self.pen = pen
        self.brush = brush

    def add_overlay(self, overlay: OverLay):
        self.overlays.append(overlay)
        overlay.setParentItem(self)

    def shape(self) -> QtGui.QPainterPath:
        raise NotImplementedError("Subclasses must implement shape()")

    def paint(self, painter, option, widget = ...):
        path = self.shape()
        if self.brush is None:
            painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        else:
            painter.setBrush(self.brush)
            painter.fillPath(path, self.brush)
        if self.pen is None:
            painter.setPen(QtCore.Qt.PenStyle.NoPen)
        else:
            painter.setPen(self.pen)
            painter.drawPath(path)


class Disc(ShapeObjet):
    def __init__(self,
                 outer_radius: float,
                 inner_radius: float = 0.0,
                 start_angle: float = 0.0,
                 span_angle: float = 360.0,
                 z: float = 0.0,
                 draggable: bool = False,
                 pen: QtGui.QPen | None = None,
                 brush: QtGui.QBrush | None = None,
                 parent=None
    ) -> None:
        super().__init__(
            radius=outer_radius,
            z=z,
            draggable=draggable,
            pen=pen,
            brush=brush,
            parent=parent
        )
        self.outer_radius = outer_radius
        self.inner_radius = inner_radius
        self.start_angle = start_angle
        self.span_angle = span_angle

    @staticmethod
    def _create_pie_path(inner_radius, outer_radius, start_angle, span_angle):
        r0 = float(inner_radius)
        r1 = float(outer_radius)
        a0 = float(start_angle) + 90
        sa = float(span_angle)

        path = QtGui.QPainterPath()

        outer = QtCore.QRectF(-r1, -r1, 2 * r1, 2 * r1)

        if r0 <= 0.0:
            # simple pie wedge
            path.moveTo(0.0, 0.0)
            path.arcTo(outer, a0, sa)
            path.closeSubpath()
            return path

        inner = QtCore.QRectF(-r0, -r0, 2 * r0, 2 * r0)

        # Start point on outer arc
        path.arcMoveTo(outer, a0)
        # Outer arc (CCW if sa>0)
        path.arcTo(outer, a0, sa)
        # Connect to inner arc end
        path.arcTo(inner, a0 + sa, -sa)  # reverse direction on inner
        path.closeSubpath()
        return path

    @staticmethod
    def _create_ring_path(outer_radius, inner_radius):
        path = QtGui.QPainterPath()
        path.addEllipse(QtCore.QPointF(0, 0), outer_radius, outer_radius)
        if inner_radius > 0.0:
            inner_path = QtGui.QPainterPath()
            inner_path.addEllipse(QtCore.QPointF(0, 0), inner_radius, inner_radius)
            path = path.subtracted(inner_path)
        return path

    def shape(self) -> QtGui.QPainterPath:
        # TODO: Optimize shape creation by caching paths for common cases
        #  (full ring, simple pie wedge) and only creating custom paths for partial pies.
        if self.span_angle >= 360.0 or self.span_angle <= -360.0:
            return self._create_ring_path(self.outer_radius, self.inner_radius)
        else:
            return self._create_pie_path(self.inner_radius,
                                         self.outer_radius,
                                         self.start_angle,
                                         self.span_angle)


class RelativeBearingDisc(Disc):
    """
    Outer ring with bearing ticks every 1 degree and labels every 10 degrees.
    """
    def __init__(self, radius_in: float, radius_out: float, z: float, parent=None):
        super().__init__(
            outer_radius=radius_out,
            inner_radius=radius_in,
            z=z,
            draggable=False,
            pen=QtGui.QPen(QtGui.QColor(65, 45, 45), 2.0),
            brush=QtGui.QBrush(QtGui.QColor(70, 45, 50)),
            parent=parent
        )
        disc_width = radius_out - radius_in

        tick_overlay = TickRadialOverlay(
            radius=radius_in + disc_width * 0.1,
            step_deg=1,
            start_deg=0,
            span_deg=360,
            long_every=5,
            long_len=50,
            short_len=30,
            include_end=False,
            pen_width=3.5,
            # radial_offset=15,
            reversed=False,
            color=QtGui.QColor(188, 183, 183),
            antialiasing=True,
        )
        label_overlay = LabelRadialOverlay(
            radius=radius_in + disc_width * 0.85,
            step_deg=10,
            start_deg=180,
            span_deg=360,
            start_num=0,
            num_increase=10,
            include_end=False,
            font=QtGui.QFont("Arial", 15, QtGui.QFont.Bold),
            color=QtGui.QColor(188, 183, 183),
            antialiasing=False,
        )
        self.add_overlay(tick_overlay)
        self.add_overlay(label_overlay)

    def paint(self, painter: QtGui.QPainter, option, widget=None) -> None:
        super().paint(painter, option, widget)

        # Add decoration: North arrowhead
        arrow_north = QtGui.QPolygonF([
            QtCore.QPointF(0, -self.inner_radius - 1),
            QtCore.QPointF(10, -self.inner_radius - 15),
            QtCore.QPointF(-10, -self.inner_radius - 15)])
        # c.setAlpha(255)  # same alpha as ticks
        painter.setBrush(self.overlays[0].color)  # same color as ticks
        painter.setPen(QtGui.QColor("black"))
        painter.setPen(QtCore.Qt.PenStyle.SolidLine)
        painter.drawPolygon(arrow_north)


class CompassRoseDisc(Disc):

    def __init__(self, radius_in:float, radius_out:float, z: float, parent=None):
        super().__init__(
            inner_radius=radius_in,
            outer_radius=radius_out,
            z=z,
            draggable=True,
            brush=QtGui.QBrush(QtGui.QColor(200, 195, 170)),
            parent=parent
        )
        disc_width = radius_out - radius_in

        tick_out_overlay = TickRadialOverlay(
            radius=radius_out - disc_width * 0.0,
            step_deg=1,
            start_deg=0,
            span_deg=360,
            long_every=5,
            long_len=55,
            short_len=35,
            include_end=False,
            pen_width=2.0,
            reversed=True,
            color=QtGui.QColor(0, 0, 0),
            antialiasing=True,
        )
        label_out_overlay = LabelRadialOverlay(
            radius=radius_out - disc_width * 0.5,
            step_deg=10,
            start_deg=0,
            span_deg=360,
            start_num=0,
            num_increase=10,
            include_end=False,
            font=QtGui.QFont("Arial", 14),
            color=QtGui.QColor(0, 0, 0),
            antialiasing=True,
        )

        tick_in_overlay = TickRadialOverlay(
            radius=radius_out - disc_width * 0.7,
            step_deg=1,
            start_deg=0,
            span_deg=360,
            long_every=5,
            long_len=20,
            short_len=7,
            include_end=False,
            pen_width=2.0,
            reversed=True,
            color=QtGui.QColor(0, 0, 0),
            antialiasing=True,
        )
        label_in_overlay = LabelRadialOverlay(
            radius=radius_out - disc_width * 0.93,
            step_deg=10,
            start_deg=180,
            span_deg=360,
            start_num=0,
            num_increase=10,
            include_end=False,
            font=QtGui.QFont("Arial", 13),
            color=QtGui.QColor(0, 0, 0),
            antialiasing=True,
        )
        circle = CircleOverlay(
            radius=radius_out - disc_width * 0.7 + 1,
            pen_width=2.0,
            color=QtGui.QColor(0, 0, 0),
            antialiasing=True,
        )

        self.add_overlay(tick_out_overlay)
        self.add_overlay(label_out_overlay)
        self.add_overlay(tick_in_overlay)
        self.add_overlay(label_in_overlay)
        self.add_overlay(circle)

    def paint(self, painter: QtGui.QPainter, option, widget=None) -> None:
        super().paint(painter, option, widget)

        # Add decoration: North arrowhead
        y = self.outer_radius
        arrow_north = QtGui.QPolygonF([
            QtCore.QPointF(0, -y),
            QtCore.QPointF(20, -(y - 30)),
            QtCore.QPointF(-20, -(y - 30)),
            QtCore.QPointF(0, -y)])
        pen = QtGui.QPen(QtGui.QColor(0, 0, 0))
        pen.setWidthF(4.0)
        painter.setPen(pen)
        path = QtGui.QPainterPath()
        path.addPolygon(arrow_north)
        painter.drawPath(path)


class SpeedArcRing(RotatableObjet):
    """
    A ring that draws red/green arc segments like the speed scale.
    """
    def __init__(self, radius: float, thickness: float, z: float, draggable: bool = True, parent=None):
        super().__init__(radius=radius + thickness, z=z, draggable=draggable, parent=parent)
        self.radius = radius
        self.thickness = thickness

    def boundingRect(self) -> QtCore.QRectF:
        r = self.radius + self.thickness + 2
        return QtCore.QRectF(-r, -r, 2 * r, 2 * r)

    def paint(self, painter: QtGui.QPainter, option, widget=None) -> None:
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

        rect = QtCore.QRectF(
            -(self.radius + self.thickness / 2),
            -(self.radius + self.thickness / 2),
            2 * (self.radius + self.thickness / 2),
            2 * (self.radius + self.thickness / 2),
        )

        # In Qt, angles are in 1/16 degrees, 0 at 3 o'clock, CCW positive.
        # We'll define arcs by bearings and convert.
        def bearing_to_qt16(bearing_deg: float) -> int:
            # bearing: 0 up cw+ -> qt: 0 right ccw+
            qt_deg = 90 - bearing_deg
            return int(qt_deg * 16)

        pen = QtGui.QPen(QtGui.QColor(30, 200, 80))
        pen.setWidthF(self.thickness)
        pen.setCapStyle(QtCore.Qt.RoundCap)
        painter.setPen(pen)
        # green arc segment (example)
        painter.drawArc(rect, bearing_to_qt16(210), int(-120 * 16))

        pen.setColor(QtGui.QColor(220, 60, 60))
        painter.setPen(pen)
        # red arc segment (example)
        painter.drawArc(rect, bearing_to_qt16(30), int(-120 * 16))


class AngleOnBowDisc(Disc):
    """
    A disc with ticks every 10 degrees and labels every 30 degrees, used for angle-on-bow display.
    """
    def __init__(self, radius_in:float, radius_out:float, z: float, parent=None):
        super().__init__(
            outer_radius=radius_out,
            inner_radius=radius_in,
            z=z,
            draggable=True,
            brush=QtGui.QBrush(QtGui.QColor(237, 237, 237)),
            parent=parent
        )
        tick_R_overlay = TickRadialOverlay(
            radius=radius_out,
            step_deg=1,
            start_deg=0,
            span_deg=180,
            long_every=5,
            long_len=16,
            short_len=7,
            include_end=False,
            pen_width=2.0,
            reversed=True,
            color=QtGui.QColor(0, 120, 0),
            antialiasing=True,
        )
        label_R_overlay = LabelRadialOverlay(
            radius=radius_out-30,
            step_deg=10,
            start_deg=0,
            span_deg=180,
            start_num=0,
            num_increase=10,
            include_end=False,
            font=QtGui.QFont("Arial", 14),
            color=QtGui.QColor(0, 120, 0),
            antialiasing=True,
        )
        tick_L_overlay = TickRadialOverlay(
            radius=radius_out,
            step_deg=1,
            start_deg=180,
            span_deg=180,
            long_every=5,
            long_len=16,
            short_len=7,
            include_end=False,
            pen_width=2.0,
            reversed=True,
            color=QtGui.QColor(200, 0, 0),
            antialiasing=True,
        )
        label_L_overlay = LabelRadialOverlay(
            radius=radius_out - 30,
            step_deg=10,
            start_deg=180,
            span_deg=180,
            start_num=180,
            num_increase=-10,
            include_end=False,
            font=QtGui.QFont("Arial", 14),
            color=QtGui.QColor(200, 0, 0),
            antialiasing=True,
        )
        self.add_overlay(tick_L_overlay)
        self.add_overlay(label_L_overlay)
        self.add_overlay(tick_R_overlay)
        self.add_overlay(label_R_overlay)


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
            QtCore.QPointF(7, -self.outer_radius + radial_offset),
            QtCore.QPointF(0, -self.outer_radius - 30 + radial_offset),
            QtCore.QPointF(-7, -self.outer_radius + radial_offset),
        ])
        painter.setBrush(QtGui.QColor(120, 0, 0, 230))
        # painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setPen(QtGui.QPen(QtGui.QColor(190, 0, 0, 180), 1.0))
        painter.drawPolygon(arrowhead)

        # Draw the rest of the disc on top of the pointer
        super().paint(painter, option, widget)

        painter.setBrush(QtGui.QColor(204, 171, 138))
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.drawEllipse(QtCore.QPoint(0, 0), 300, 300)

        # Add decoration: ship silhouette
        scl = -1.8
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


class AttackCoursePointer(ShapeObjet):
    """
    Simple transparent ruler/arm overlay. Rotatable.
    """
    def __init__(self, length: float, width: float, z: float = 0, parent=None):
        super().__init__(radius=length, z=z, draggable=True, parent=parent)
        self.length = length
        self.width = width

    def boundingRect(self) -> QtCore.QRectF:
        r = self.length + 10
        return QtCore.QRectF(-r, -r, 2 * r, 2 * r)

    def shape(self) -> QtGui.QPainterPath:
        path = QtGui.QPainterPath()
        w = self.width
        L = self.length
        poly = QtGui.QPolygonF([
            QtCore.QPointF(-w / 2, L),
            QtCore.QPointF(w / 2, L),
            QtCore.QPointF(w, 0),
            QtCore.QPointF(w / 2, -L),
            QtCore.QPointF(-w / 2, -L),
            QtCore.QPointF(-w, 0),
            QtCore.QPointF(-w / 2, L),
        ])
        path.addPolygon(poly)
        return path

    def paint(self, painter: QtGui.QPainter, option, widget=None) -> None:
        super().paint(painter, option, widget)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

        # draw a long rectangle from center to outward (pointing "up" at rotation=0)
        path = self.shape()
        painter.fillPath(path, QtGui.QColor(255, 255, 255, 40))
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 120), 1.0))
        painter.drawPath(path)

        # draw a center line with an arrowhead
        painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0, 255), 2.0))
        painter.drawLine(0, int(self.length), 0, int(-self.length))
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


class BearingAndLeadPointer(Disc):

    def __init__(self, radius: float, length: float, z: float = 0, parent=None):
        super().__init__(
            outer_radius=radius,
            inner_radius=0,
            start_angle=295,
            span_angle=130,
            z=z,
            draggable=True,
            pen=QtGui.QPen(QtGui.QColor(0, 0, 0, 100), 1.0),
            brush=QtGui.QBrush(QtGui.QColor(237, 237, 237, 40)),
            parent=parent
        )
        self.length = length
        self.radius = radius

        tick_R_overlay = TickRadialOverlay(
            radius=radius,
            step_deg=1,
            start_deg=0,
            span_deg=60,
            long_every=5,
            long_len=16,
            short_len=7,
            include_end=False,
            pen_width=2.0,
            reversed=True,
            color=QtGui.QColor(0, 120, 0),
            antialiasing=True,
        )
        label_R_overlay = LabelRadialOverlay(
            radius=radius - 30,
            step_deg=10,
            start_deg=0,
            span_deg=60,
            start_num=0,
            num_increase=10,
            include_end=True,
            font=QtGui.QFont("Arial", 14),
            color=QtGui.QColor(0, 120, 0),
            antialiasing=True,
        )
        tick_L_overlay = TickRadialOverlay(
            radius=radius,
            step_deg=1,
            start_deg=-60,
            span_deg=60,
            long_every=5,
            long_len=16,
            short_len=7,
            include_end=True,
            pen_width=2.0,
            reversed=True,
            color=QtGui.QColor(200, 0, 0),
            antialiasing=True,
        )
        label_L_overlay = LabelRadialOverlay(
            radius=radius - 30,
            step_deg=10,
            start_deg=-60,
            span_deg=60,
            start_num=60,
            num_increase=-10,
            include_end=True,
            font=QtGui.QFont("Arial", 14),
            color=QtGui.QColor(200, 0, 0),
            antialiasing=True,
        )
        self.add_overlay(tick_L_overlay)
        self.add_overlay(label_L_overlay)
        self.add_overlay(tick_R_overlay)
        self.add_overlay(label_R_overlay)



    def shape(self) -> QtGui.QPainterPath:
        path = super().shape()

        pointer = QtGui.QPolygonF([
            polar_to_vec(self.radius, 10),
            polar_to_vec(self.length, 2),
            polar_to_vec(self.length, -2),
            polar_to_vec(self.radius, -10),
        ])
        path.addPolygon(pointer)
        path.closeSubpath()
        return path


    def paint(self, painter: QtGui.QPainter, option, widget=None) -> None:
        super().paint(painter, option, widget)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

        # Draw a center line with an arrowhead
        p0 = polar_to_vec(self.length * 0.2, 0)
        p1 = polar_to_vec(self.length * 0.9, 0)
        pen = QtGui.QPen(QtGui.QColor(0, 0, 0), 2.0)
        painter.setPen(pen)
        painter.drawLine(p0, p1)


class AttackDiscWidget(QtWidgets.QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        # self.setRenderHint(QtGui.QPainter.Antialiasing, False)
        self.setBackgroundBrush(QtGui.QColor(90, 110, 110))

        scene = QtWidgets.QGraphicsScene(self)
        self.setScene(scene)
        self.setSceneRect(-600, -600, 1200, 1200)

        # --- Layer A: Relative Bearing Disc ---
        rel_bearing_disc = RelativeBearingDisc(500, 600, z=0)
        scene.addItem(rel_bearing_disc)

        # --- Layer B: Compass Rose Disc ---
        compass_rose_disc = CompassRoseDisc(350, 500, z=5)
        scene.addItem(compass_rose_disc)

        # --- Layer C: Angle on Bow Pointer ---
        aob_disc = AngleOnBowDisc(200, 350, z=10)
        scene.addItem(aob_disc)

        # --- Layer D: speed arc ring (example) ---
        bearing_n_lead_disc = BearingAndLeadPointer(radius=260, length=525, z=15)
        scene.addItem(bearing_n_lead_disc)

        # --- Layer E: Attack Course Pointer ---
        attack_pointer = AttackCoursePointer(length=550, width=40, z=20)
        attack_pointer.setRotation(35)  # initial pose
        scene.addItem(attack_pointer)

        # Center hub (visual only)
        hub = QtWidgets.QGraphicsEllipseItem(-55, -55, 110, 110)
        hub.setZValue(50)
        hub.setBrush(QtGui.QBrush(QtGui.QColor(20, 20, 20)))
        hub.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0), 2))
        scene.addItem(hub)

        knob = QtWidgets.QGraphicsEllipseItem(-18, -18, 36, 36)
        knob.setZValue(60)
        knob.setBrush(QtGui.QBrush(QtGui.QColor(120, 120, 120)))
        knob.setPen(QtGui.QPen(QtGui.QColor(30, 30, 30), 1))
        scene.addItem(knob)

        self.rel_bearing_disc = rel_bearing_disc
        self.compass_rose_disc = compass_rose_disc
        self.aob_disc = aob_disc
        self.bearing_n_lead_disc = bearing_n_lead_disc
        self.attack_pointer = attack_pointer

        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        self.fitInView(self.sceneRect(), QtCore.Qt.KeepAspectRatio)