import numpy as np


Vec2 = np.ndarray  # shape (2,), dtype float64 recommended
Vec3 = np.ndarray  # shape (2,), dtype float64 recommended


def v2(x: float = 0.0, y: float = 0.0) -> Vec2:
    """Create a 2D float vector."""
    return np.array([x, y], dtype=np.float64)


def v3(x: float = 0.0, y: float = 0.0, z: float = 0.0) -> Vec3:
    """Create a 3D float vector."""
    return np.array([x, y, z], dtype=np.float64)