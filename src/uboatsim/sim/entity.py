"""

"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Protocol, runtime_checkable
import numpy as np


Vec2 = np.ndarray  # shape (2,), dtype float64 recommended
Vec3 = np.ndarray  # shape (2,), dtype float64 recommended


def v2(x: float = 0.0, y: float = 0.0) -> Vec2:
    """Create a 2D float vector."""
    return np.array([x, y], dtype=np.float64)

def v3(x: float = 0.0, y: float = 0.0, z: float = 0.0) -> Vec3:
    """Create a 3D float vector."""
    return np.array([x, y, z], dtype=np.float64)


# TODO: maybe add a math utils module later if we need more vector/angle helpers, but for now this is enough
def unit_from_heading(heading_rad: float) -> Vec2:
    """
    Nautical convention: 0 rad = North (+Y), pi/2 = East (+X).
    Returns a unit direction vector.
    """
    return np.array([np.sin(heading_rad), np.cos(heading_rad)], dtype=np.float64)


@dataclass(slots=True)
class Kinematics3D:
    """
    Basic kinematics state for an entity.
    All values are in SI units (m, s, rad).
    """
    pos: Vec3 = field(default_factory=v3)          # meters
    vel: Vec3 = field(default_factory=v3)          # m/s
    heading: float = 0.0                           # radians (0 = North)
    speed: float = 0.0                             # m/s (scalar along heading)
    turn_rate: float = 0.0                         # rad/s (positive = turn right / clockwise)

    def sync_vel_from_heading(self) -> None:
        """Set velocity vector from heading and speed."""
        self.vel = unit_from_heading(self.heading) * float(self.speed)

    def sync_heading_from_vel(self) -> None:
        """Set heading/speed from velocity vector (if vel is non-zero)."""
        spd = float(np.linalg.norm(self.vel))
        self.speed = spd
        if spd > 1e-12:
            # Invert unit_from_heading: vx = sin(h), vy = cos(h)
            vx, vy = float(self.vel[0]), float(self.vel[1])
            self.heading = float(np.arctan2(vx, vy))


@runtime_checkable
class WorldLike(Protocol):
    """Light protocol to avoid circular imports in type hints."""
    def get_time(self) -> float: ...


@dataclass(slots=True)
class Entity:
    """
    Base simulation entity. UI should never subclass this; keep sim pure.
    """
    eid: str
    kind: str = "entity"
    alive: bool = True
    kin: Kinematics3D = field(default_factory=Kinematics3D)

    # Optional bookkeeping
    team: Optional[str] = None
    radius: float = 1.0  # meters (useful for collisions later)

    def pre_step(self, world: WorldLike, dt: float) -> None:
        """Hook: called before integration each tick."""
        # Default: keep vel aligned with heading/speed
        self.kin.sync_vel_from_heading()

    def step(self, world: WorldLike, dt: float) -> None:
        """
        Integrate motion for dt seconds.
        This is a simple Euler integrator by default.
        """
        if not self.alive:
            return

        # Heading update from turn_rate (if you want turning circles later)
        if self.kin.turn_rate != 0.0:
            self.kin.heading = float(self.kin.heading + self.kin.turn_rate * dt)

        # Velocity derived from heading/speed
        self.kin.sync_vel_from_heading()

        # Position integrate
        self.kin.pos = self.kin.pos + self.kin.vel * dt

    def post_step(self, world: WorldLike, dt: float) -> None:
        """Hook: called after integration each tick."""
        pass

    # Convenience API (keeps UI code clean)
    @property
    def x(self) -> float:
        return float(self.kin.pos[0])

    @property
    def y(self) -> float:
        return float(self.kin.pos[1])

    @property
    def z(self):
        return float(self.kin.pos[2])

    def pos(self):
        return self.kin.pos

    def set_pos(self, x: float, y: float) -> None:
        self.kin.pos = v2(x, y)

    def set_course(self, heading_rad: float) -> None:
        self.kin.heading = float(heading_rad)
        self.kin.sync_vel_from_heading()

    def set_speed(self, speed_mps: float) -> None:
        self.kin.speed = float(speed_mps)
        self.kin.sync_vel_from_heading()


@dataclass(slots=True)
class Ship(Entity):
    kind: str = "ship"


@dataclass(slots=True)
class Submarine(Entity):
    kind: str = "submarine"