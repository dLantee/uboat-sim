"""
Units conversion utilities.

Simulation MUST use SI internally:
- distance: meters
- time: seconds
- velocity: m/s
- angle: radians

UI layer may convert to nautical miles, knots, degrees, etc.
"""

from __future__ import annotations
import numpy as np
from typing import Union
from uboatsim.utils.math import Vec2

Number = Union[float, np.ndarray]


# -----------------------------------------------------------------------------
# Constants (exact or internationally accepted values)
# -----------------------------------------------------------------------------

M_PER_NM: float = 1852.0                 # meters in one nautical mile
M_PER_KM: float = 1000.0
S_PER_HOUR: float = 3600.0
KNOT_TO_MPS: float = 0.514444            # 1 knot in m/s (exact defined via NM/hour)
MPS_TO_KNOT: float = 1.0 / KNOT_TO_MPS

DEG_TO_RAD: float = np.pi / 180.0
RAD_TO_DEG: float = 180.0 / np.pi


# -----------------------------------------------------------------------------
# Distance
# -----------------------------------------------------------------------------

def meters_to_nm(m: Number) -> Number:
    return m / M_PER_NM


def nm_to_meters(nm: Number) -> Number:
    return nm * M_PER_NM


def meters_to_km(m: Number) -> Number:
    return m / M_PER_KM


def km_to_meters(km: Number) -> Number:
    return km * M_PER_KM


# -----------------------------------------------------------------------------
# Speed
# -----------------------------------------------------------------------------

def mps_to_knots(mps: Number) -> Number:
    return mps * MPS_TO_KNOT


def knots_to_mps(knots: Number) -> Number:
    return knots * KNOT_TO_MPS


def mps_to_kmh(mps: Number) -> Number:
    return mps * (S_PER_HOUR / M_PER_KM)


def kmh_to_mps(kmh: Number) -> Number:
    return kmh * (M_PER_KM / S_PER_HOUR)


# -----------------------------------------------------------------------------
# Angle
# -----------------------------------------------------------------------------

def deg_to_rad(deg: Number) -> Number:
    return deg * DEG_TO_RAD


def rad_to_deg(rad: Number) -> Number:
    return rad * RAD_TO_DEG


def normalize_rad(angle_rad: Number) -> Number:
    """
    Normalize angle to [0, 2π)
    Works with scalars or numpy arrays.
    """
    return np.mod(angle_rad, 2.0 * np.pi)


def normalize_deg(angle_deg: Number) -> Number:
    """
    Normalize angle to [0, 360)
    """
    return np.mod(angle_deg, 360.0)


def vector_to_rad(vec: Vec2) -> float:
    """
    Convert a 2D vector to a heading angle in radians.
    Nautical convention: 0 rad = North (+Y), π/2 = East (+X).
    """
    vx, vy = float(vec[0]), float(vec[1])
    return float(np.arctan2(vx, vy))

def rad_to_vector(angle_rad: Number) -> Vec2:
    """
    Convert a heading angle in radians to a 2D unit vector.
    Nautical convention: 0 rad = North (+Y), π/2 = East (+X).
    """
    return np.array([np.sin(angle_rad), np.cos(angle_rad)], dtype=np.float64)


# -----------------------------------------------------------------------------
# Bearing Conventions
# -----------------------------------------------------------------------------

def heading_rad_from_nautical_deg(deg: Number) -> Number:
    """
    Convert nautical heading degrees to radians.

    Nautical convention:
    - 0° = North
    - 90° = East
    - 180° = South
    - 270° = West

    Internal sim uses radians with same orientation:
    0 rad = North (+Y)
    π/2 = East (+X)
    """
    return deg_to_rad(deg)


def nautical_deg_from_heading_rad(rad: Number) -> Number:
    return normalize_deg(rad_to_deg(rad))


# -----------------------------------------------------------------------------
# Utility scaling (useful for ML normalization later)
# -----------------------------------------------------------------------------

def scale_linear(value: Number, min_val: float, max_val: float) -> Number:
    """
    Linearly scale value into [0, 1].
    Useful for ML input normalization.
    """
    return (value - min_val) / (max_val - min_val)


def unscale_linear(norm_value: Number, min_val: float, max_val: float) -> Number:
    """
    Reverse of scale_linear.
    """
    return norm_value * (max_val - min_val) + min_val