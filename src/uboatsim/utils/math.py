import numpy as np

from typing import Tuple


Vec2 = np.ndarray  # shape (2,), dtype float64 recommended
Vec3 = np.ndarray  # shape (2,), dtype float64 recommended

def v2(x: float = 0.0, y: float = 0.0) -> Vec2:
    """Create a 2D float vector."""
    return np.array([x, y], dtype=np.float64)


def v3(x: float = 0.0, y: float = 0.0, z: float = 0.0) -> Vec3:
    """Create a 3D float vector."""
    return np.array([x, y, z], dtype=np.float64)


def polar_to_vector(r: float, deg: float) -> Tuple[float, float]:
    # bearing deg: 0 up, cw positive
    rad = np.radians(deg)
    x = r * np.sin(rad)
    y = -r * np.cos(rad)
    return x, y


def vector_to_polar(x: float, y: float) -> Tuple[float, float]:
    r = np.hypot(x, y)
    deg = (np.degrees(np.atan2(x, -y))) % 360.0
    return r, deg