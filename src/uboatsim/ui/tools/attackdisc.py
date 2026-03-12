"""

"""
import math
from typing import Tuple, Iterable

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
    def __init__(self, *, start_num:int=0, num_increase:int=1, custom_labels:Iterable | None = None, **kwargs):
        super().__init__(**kwargs)
        self.start_num = start_num
        self.num_increase = num_increase

        # optional custom labels for each step,
        # overrides default numbering if provided
        self.custom_labels = custom_labels or []

    def paint(self, painter: QtGui.QPainter, option, widget=None) -> None:
        super().paint(painter, option, widget)

        for i, deg in enumerate(self.step_values):
            pt = polar_to_vec(self.radius, deg)
            txt = str(int(self.start_num + i * self.num_increase))

            # if self.custom_labels:
            #     if len(self.custom_labels) != self.step_num:
            #         raise ValueError(f"Length of custom_labels ({len(self.custom_labels)}) must match number of steps ({self.step_num})")
            # txt = self.custom_labels[i] if self.custom_labels else def_txt

            if self.custom_labels:
                if isinstance(self.custom_labels, str):
                    txt = self.custom_labels

            metrics = QtGui.QFontMetrics(self.font)
            w = metrics.horizontalAdvance(txt)
            h = metrics.height()
            pivot = QtCore.QPoint(int(-w / 2), int(h / 3))
            painter.save()
            painter.translate(pt)  # move the coordinate system to the label position
            painter.rotate(deg)
            painter.drawStaticText(pivot, QtGui.QStaticText(txt))
            painter.restore()


class TickRadialOverlay(RadialOverlay):
    """
    Simple tick marks at specified angles. Not a full ring, just individual ticks.
    """
    def __init__(self, *, long_len: float, short_len: float, long_width_mult: float = 1.0,
                 long_every: int, reversed:bool=False,
                 **kwargs):
        super().__init__(**kwargs)
        self.long_len = long_len
        self.short_len = short_len
        self.long_every = long_every
        self.long_width_mult = long_width_mult

        self.reversed = reversed
        # self.log_scale = False  # TODO: Add option for logarithmic tick spacing

        # Cached geometry for fast draw
        self._cache_valid = False
        self._short_lines: list[QtCore.QLineF] = []
        self._long_lines: list[QtCore.QLineF] = []
        # self.setCacheMode(QtWidgets.QGraphicsItem.CacheMode.ItemCoordinateCache)

    def _invalidate_cache(self) -> None:
        """Call this whenever parameters change that affect the geometry of the ticks."""
        self._cache_valid = False
        self.update()

    def _rebuild_cache(self) -> None:
        self._short_lines.clear()
        self._long_lines.clear()

        for i, deg in enumerate(self.step_values):
            is_long = (i % self.long_every) == 0
            length = self.long_len if is_long else self.short_len

            p0 = polar_to_vec(self.radius, deg)
            if self.reversed:
                p1 = polar_to_vec(self.radius - length, deg)
            else:
                p1 = polar_to_vec(self.radius + length, deg)

            line = QtCore.QLineF(p0, p1)
            if is_long:
                self._long_lines.append(line)
            else:
                self._short_lines.append(line)

        self._cache_valid = True

    def paint(self, painter: QtGui.QPainter, option, widget=None) -> None:
        super().paint(painter, option, widget)

        if not self._cache_valid:
            self._rebuild_cache()

        pen = painter.pen()
        pw = pen.widthF()

        if self._short_lines:
            painter.drawLines(self._short_lines)

        if self._long_lines:
            pen.setWidthF(pw * self.long_width_mult)
            painter.setPen(pen)
            painter.drawLines(self._long_lines)

        pen.setWidthF(pw)
        painter.setPen(pen)


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

        self._debug = False

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

    def paint(self, painter, option, widget = ...):
        if self._debug:
            painter.setPen(QtGui.QPen(QtGui.QColor(255, 0, 0), 2.0))
            painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            rect = self.boundingRect()
            painter.drawRect(rect)


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

    def path(self) -> QtGui.QPainterPath:
        """Return the path to be drawn for this item."""
        raise NotImplementedError("Subclasses must implement path()")

    def shape(self) -> QtGui.QPainterPath:
        """Return the shape of the item for mouse interaction (e.g. clicks, drags)."""
        # raise NotImplementedError("Subclasses must implement shape()")
        return self.path()

    def paint(self, painter, option, widget = ...):
        super().paint(painter, option, widget)
        path = self.path()
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

    def path(self) -> QtGui.QPainterPath:
        if self.span_angle >= 360.0 or self.span_angle <= -360.0:
            return self._create_ring_path(self.outer_radius, self.inner_radius)
        else:
            return self._create_pie_path(self.inner_radius,
                                         self.outer_radius,
                                         self.start_angle,
                                         self.span_angle)

    # def shape(self) -> QtGui.QPainterPath:
    #     # TODO: Optimize shape creation by caching paths for common cases
    #     #  (full ring, simple pie wedge) and only creating custom paths for partial pies.
    #     return self.path()


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
            radius=radius_in + disc_width * 0.15,
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
            radius=radius_in + disc_width*1.05,
            step_deg=10,
            start_deg=180,
            span_deg=360,
            start_num=0,
            num_increase=10,
            include_end=False,
            font=QtGui.QFont("Arial", 18, QtGui.QFont.Bold),
            color=QtGui.QColor(188, 183, 183),
            antialiasing=True,
        )
        self.add_overlay(tick_overlay)
        self.add_overlay(label_overlay)

    def paint(self, painter: QtGui.QPainter, option, widget=None) -> None:
        super().paint(painter, option, widget)

        # Add decoration: North arrowhead
        arrow_north = QtGui.QPolygonF([
            QtCore.QPointF(0, -self.inner_radius - 1),
            QtCore.QPointF(15, -self.inner_radius - 20),
            QtCore.QPointF(-15, -self.inner_radius - 20)])
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
            long_width_mult=1.5,
            short_len=35,
            include_end=False,
            pen_width=2.0,
            reversed=True,
            color=QtGui.QColor(0, 0, 0),
            antialiasing=True,
        )
        label_out_overlay = LabelRadialOverlay(
            radius=radius_out - disc_width * 0.35,
            step_deg=10,
            start_deg=0,
            span_deg=360,
            start_num=0,
            num_increase=10,
            include_end=False,
            font=QtGui.QFont("Arial", 17),
            color=QtGui.QColor(0, 0, 0),
            antialiasing=True,
        )

        tick_in_overlay = TickRadialOverlay(
            radius=radius_out - disc_width * 0.6,
            step_deg=1,
            start_deg=0,
            span_deg=360,
            long_every=5,
            long_len=20,
            long_width_mult=1.5,
            short_len=7,
            include_end=False,
            pen_width=2.0,
            reversed=True,
            color=QtGui.QColor(0, 0, 0),
            antialiasing=True,
        )
        label_in_overlay = LabelRadialOverlay(
            radius=radius_out - disc_width * 0.73,
            step_deg=10,
            start_deg=180,
            span_deg=360,
            start_num=0,
            num_increase=10,
            include_end=False,
            font=QtGui.QFont("Arial", 15),
            color=QtGui.QColor(0, 0, 0),
            antialiasing=True,
        )
        circle = CircleOverlay(
            radius=radius_out - disc_width * 0.6 + 1,
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
            parent=parent,
        )
        self.contour_pen = QtGui.QPen(QtGui.QColor(0, 0, 0, 180), 1.5)

        tick_R_overlay = TickRadialOverlay(
            radius=radius_out,
            step_deg=1,
            start_deg=0,
            span_deg=180,
            long_every=5,
            long_len=16,
            long_width_mult=1.5,
            short_len=7,
            include_end=False,
            pen_width=2.0,
            reversed=True,
            color=QtGui.QColor(0, 120, 0),
            antialiasing=True,
        )
        label_R_overlay = LabelRadialOverlay(
            radius=radius_out - 15,
            step_deg=10,
            start_deg=0,
            span_deg=180,
            start_num=0,
            num_increase=10,
            include_end=False,
            font=QtGui.QFont("Arial", 16),
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
            long_width_mult=1.5,
            short_len=7,
            include_end=False,
            pen_width=2.0,
            reversed=True,
            color=QtGui.QColor(200, 0, 0),
            antialiasing=True,
        )
        label_L_overlay = LabelRadialOverlay(
            radius=radius_out - 15,
            step_deg=10,
            start_deg=180,
            span_deg=180,
            start_num=180,
            num_increase=-10,
            include_end=False,
            font=QtGui.QFont("Arial", 16),
            color=QtGui.QColor(200, 0, 0),
            antialiasing=True,
        )
        self.add_overlay(tick_L_overlay)
        self.add_overlay(label_L_overlay)
        self.add_overlay(tick_R_overlay)
        self.add_overlay(label_R_overlay)

    def boundingRect(self) -> QtCore.QRectF:
        r = self.outer_radius + 5
        path = self._pointer_path()
        h = path.boundingRect().height()
        return QtCore.QRectF(-r, -(r+h), 2 * r, 2 * r + h)

    def _pointer_path(self) -> QtGui.QPainterPath:
        W = 100
        L = 230
        path = QtGui.QPainterPath()
        poly = QtGui.QPolygonF([
            QtCore.QPointF(-W / 2, -self.outer_radius+5),
            QtCore.QPointF(W / 2, -self.outer_radius+5),
            QtCore.QPointF(W / 2 - 25, -(self.outer_radius + L)),
            QtCore.QPointF(-W/2 + 25, -(self.outer_radius + L)),
            QtCore.QPointF(-W / 2, -self.outer_radius+5),
        ])
        path.addPolygon(poly)
        return path

    def shape(self) -> QtGui.QPainterPath:
        base_path = super().shape()
        path = base_path.united(self._pointer_path())
        return path

    def paint(self, painter: QtGui.QPainter, option, widget=None) -> None:
        # draw a long rectangle from center to outward (pointing "up" at rotation=0)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        path = self._pointer_path()
        painter.fillPath(path, QtGui.QColor(0, 0, 0, 50))
        painter.setPen(self.contour_pen)
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
        painter.setPen(self.contour_pen)
        painter.drawPolygon(arrowhead)

        # # Draw the rest of the disc on top of the pointer
        super().paint(painter, option, widget)

        # Add decoration: inner circle
        painter.setBrush(QtGui.QColor(204, 171, 138))
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.drawEllipse(QtCore.QPoint(0, 0), 300, 300)

        # Add decoration: perpendicular line
        pen = QtGui.QPen()
        pen.setWidth(2)
        pen.setColor(self.overlays[2].color)
        painter.setPen(pen)
        painter.drawLine(0, 0, int(self.outer_radius), 0)
        pen.setColor(self.overlays[0].color)
        painter.setPen(pen)
        painter.drawLine(0, 0, -int(self.outer_radius), 0)

        # Add decoration: ship silhouette
        scl = -1.8
        points = [
            QtCore.QPointF(0, -120) * scl ,
            QtCore.QPointF(30, -120) * scl,
            QtCore.QPointF(40, 0) * scl,
            QtCore.QPointF(30, 80) * scl,
            QtCore.QPointF(0 , 120) * scl,
            QtCore.QPointF(-30 , 80) * scl,
            QtCore.QPointF(-40 , 0) * scl,
            QtCore.QPointF(-30 , -120) * scl,
            QtCore.QPointF(0 , -120) * scl,
        ]
        painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0, 100), 3))

        path = QtGui.QPainterPath()
        path.moveTo(points[0])
        path.quadTo(points[1], points[2])
        path.quadTo(points[3], points[4])
        path.quadTo(points[5], points[6])
        path.quadTo(points[7], points[0])
        path.closeSubpath()
        painter.fillPath(path, QtGui.QColor(70, 75, 90))
        painter.drawPath(path)


class AttackCoursePointer(ShapeObjet):
    """
    Simple transparent ruler/arm overlay. Rotatable.
    """
    def __init__(self, length: float, width: float, z: float = 0, parent=None):
        super().__init__(radius=length, z=z, draggable=True, parent=parent,
                         pen=QtGui.QPen(QtGui.QColor(0, 0, 0, 120), 1.0),
                         brush=QtGui.QBrush(QtGui.QColor(0, 0, 0, 20)))
        self.length = length
        self.width = width

    def boundingRect(self) -> QtCore.QRectF:
        r = self.length + 5
        return QtCore.QRectF(-self.width, -r, 2*self.width, 2*r)

    def _pointer_path(self) -> QtGui.QPainterPath:
        w = self.width
        L = self.length
        path = QtGui.QPainterPath()
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

    def path(self) -> QtGui.QPainterPath:
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

    def paint(self, painter: QtGui.QPainter, option, widget=None) -> None:
        super().paint(painter, option, widget)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)

        # # draw a long rectangle from center to outward (pointing "up" at rotation=0)
        # path = self.path()
        # painter.fillPath(path, QtGui.QColor(255, 255, 255, 40))
        # painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 120), 1.0))
        # painter.drawPath(path)

        # draw a center line with an arrowhead
        painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0, 255), 2.0))
        painter.drawLine(0, int(self.length/3), 0, int(self.length))
        painter.drawLine(0, -int(self.length/3), 0, -int(self.length))
        arrow = QtGui.QPolygonF([
            QtCore.QPointF(0, self.length),
            QtCore.QPointF(10, self.length-30),
            QtCore.QPointF(-10, self.length-30),
        ])
        path = QtGui.QPainterPath()
        path.addPolygon(arrow)
        painter.fillPath(path, QtGui.QColor(0, 0, 0, 255))

        # draw text
        txt0 = "Attack"
        txt1 = "Course"
        font = QtGui.QFont("Arial", 20)
        metrics = QtGui.QFontMetrics(font)
        w0 = metrics.horizontalAdvance(txt0)
        w1 = metrics.horizontalAdvance(txt1)
        h = metrics.height()
        pivot0 = QtCore.QPointF(-2*w0, -h/2)
        pivot1 = QtCore.QPointF(w1, -h/2)
        painter.setPen(QtGui.QColor(0, 0, 0, 200))
        painter.setFont(font)
        painter.save()
        painter.translate(0, 0)
        painter.rotate(90)
        # painter.scale(10, 10)
        painter.drawStaticText(pivot0, QtGui.QStaticText(txt0))
        painter.drawStaticText(pivot1, QtGui.QStaticText(txt1))
        painter.restore()


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
            brush=QtGui.QBrush(QtGui.QColor(0, 0, 0, 20)),
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
            include_end=True,
            pen_width=2.0,
            reversed=True,
            color=QtGui.QColor(0, 120, 0),
            antialiasing=True,
        )
        label_R_overlay = LabelRadialOverlay(
            radius=radius - 15,
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
            radius=radius - 15,
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
        label_lead_angle = LabelRadialOverlay(
            radius=radius * 0.7,
            step_deg=1,
            start_deg=0,
            span_deg=1,
            include_end=False,
            font=QtGui.QFont("Arial", 16, QtGui.QFont.Bold),
            color=QtGui.QColor(0, 0, 0, 200),
            antialiasing=True,
            custom_labels="Lead Angle",
        )
        label_AoB_angle = LabelRadialOverlay(
            radius=length * 0.6,
            step_deg=1,
            start_deg=0,
            span_deg=1,
            include_end=False,
            font=QtGui.QFont("Arial", 14),
            color=QtGui.QColor(0, 0, 0, 200),
            antialiasing=True,
            custom_labels="AoB",
        )
        self.add_overlay(tick_L_overlay)
        self.add_overlay(label_L_overlay)
        self.add_overlay(tick_R_overlay)
        self.add_overlay(label_R_overlay)
        self.add_overlay(label_lead_angle)
        self.add_overlay(label_AoB_angle)

    def boundingRect(self) -> QtCore.QRectF:
        r = self.radius + 5
        return QtCore.QRectF(-r, -self.length, 2*r, self.length)

    def path(self) -> QtGui.QPainterPath:
        path = super().path()
        pointer = QtGui.QPolygonF([
            polar_to_vec(self.radius, 10),
            polar_to_vec(self.length, 2),
            polar_to_vec(self.length, -2),
            polar_to_vec(self.radius, -10),
        ])
        path.addPolygon(pointer)
        return path

    def paint(self, painter: QtGui.QPainter, option, widget=None) -> None:
        super().paint(painter, option, widget)

        # Draw a center line with an arrowhead
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        p0 = polar_to_vec(self.length * 0.6, 0)
        p1 = polar_to_vec(self.length * 0.95, 0)
        pen = QtGui.QPen(QtGui.QColor(0, 0, 0), 3.0)
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
        aob_disc = AngleOnBowDisc(0, 350, z=10)
        scene.addItem(aob_disc)

        # --- Layer D: Bearing and Lead Pointer ---
        bearing_n_lead_disc = BearingAndLeadPointer(radius=260, length=500, z=15)
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