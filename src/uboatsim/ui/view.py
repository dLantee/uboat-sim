from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets


class RadarView(QtWidgets.QGraphicsView):
    """
    Camera/view controls: pan (middle mouse) + zoom (wheel).
    """

    def __init__(self, scene: QtWidgets.QGraphicsScene, parent=None) -> None:
        super().__init__(scene, parent)

        self.setRenderHints(
            QtGui.QPainter.RenderHint.Antialiasing
            | QtGui.QPainter.RenderHint.TextAntialiasing
            | QtGui.QPainter.RenderHint.SmoothPixmapTransform
        )

        self.setViewportUpdateMode(QtWidgets.QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.ViewportAnchor.AnchorViewCenter)


        # Panning state
        self._panning = False
        self._pan_start = QtCore.QPoint()

        # Zoom limits
        self._min_scale = 0.02
        self._max_scale = 20.0

    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
        # Standard zoom factor
        delta = event.angleDelta().y()
        if delta == 0:
            return

        zoom_in = 1.15
        zoom_out = 1.0 / zoom_in
        factor = zoom_in if delta > 0 else zoom_out

        # Enforce limits
        current = self.transform().m11()
        new = current * factor
        if new < self._min_scale:
            factor = self._min_scale / current
        elif new > self._max_scale:
            factor = self._max_scale / current

        self.scale(factor, factor)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == QtCore.Qt.MouseButton.MiddleButton:
            self._panning = True
            self._pan_start = event.pos()
            self.setCursor(QtCore.Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        if self._panning:
            delta = event.pos() - self._pan_start
            self._pan_start = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == QtCore.Qt.MouseButton.MiddleButton and self._panning:
            self._panning = False
            self.setCursor(QtCore.Qt.CursorShape.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)