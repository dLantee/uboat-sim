"""

"""
import math
from typing import Tuple
from PySide6 import QtCore


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