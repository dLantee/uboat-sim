"""

"""
from typing import Iterable

from PySide6 import QtCore, QtGui, QtWidgets

from uboatsim.ui.tools.utils import polar_to_vec, scene_pos_to_angle_deg
from uboatsim import LOG



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
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, self.antialiasing)
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
                 span_deg=360, include_end=False, logarithmic=False, **kwargs):
        super().__init__(**kwargs)
        self.radius = radius
        self.step_deg = step_deg        # degrees between steps (e.g. 1 for every degree)
        self.start_deg = start_deg      # starting angle for first step (default: 0, i.e. 0° at "up" state screen)
        self.span_deg = span_deg        # positive cw
        self.include_end = include_end  # whether to include a step at end_deg if it falls on a step
        self.logarithmic = logarithmic

    def boundingRect(self):
        r = self.radius + 2
        return QtCore.QRectF(-r, -r, 2 * r, 2 * r)

    @property
    def step_num(self):
        return int(self.span_deg / self.step_deg) + int(self.include_end)

    @property
    def step_values(self) -> list[float]:
        values = [self.start_deg + i * self.step_deg for i in range(self.step_num)]
        LOG.debug(values)
        # if not self.logarithmic:
        return values

        # TODO: Add logarithmic scaling option for step values.
        #  This is a bit tricky since we need to handle the case where start_deg can be 0 or negative,
        #  and we want to avoid log(0) issues. One approach could be to apply logarithmic scaling
        #  to the step indices rather than the angles themselves,
        #  which would give a non-linear distribution of steps while still covering the same angular range.
        # def log(v, base=2):
        #     # Avoid log(0) by treating 0 as a small positive number
        #     return math.log(v, base) if v > 0 else math.log(1e-6)
        #
        # # values = [1.1, 1.2, 1.5, 2.0, 2.5, 3.0, 3.5, 4, 5, 6, 7, 8,
        # #           9, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90]
        #
        # # values = [1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6, 7, 8, 9, 10, 20, 30, 40, 50, 90]
        # vmin = min(values) if min(values) > 0 else 1.0
        # vmax = max(values)
        # LOG.debug(f"Logarithmic scaling: vmin={vmin}, vmax={vmax}")
        # # log_values = [int(360 * ((log(v) - log(vmin)) / (log(vmax) - log(vmin)))) % 360 for v in values]
        # log_values = [int(360 * (log(v) / log(vmax))) % 360 for v in values]
        #
        # LOG.debug(f"Linear values {values}")
        # LOG.debug(f"Logarithmic values {log_values}")
        #
        # return log_values


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
        self.setAcceptedMouseButtons(QtCore.Qt.MouseButton.LeftButton)
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