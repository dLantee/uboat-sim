"""

"""
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import QGraphicsView
from uboatsim.ui.tools.abstractdisc import (CircleOverlay,
                                            LabelRadialOverlay,
                                            TickRadialOverlay,
                                            ShapeObjet,
                                            Disc)
from uboatsim.ui.tools.utils import polar_to_vec


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