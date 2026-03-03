"""

"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
import numpy as np

from .entity import Entity, Vec2, v2


@dataclass(slots=True)
class WorldConfig:
    """
    Configuration for the simulation world.
    """
    fixed_dt: float = 1.0 / 30.0   # seconds (used if you want fixed-step)
    max_substeps: int = 5          # protects against huge dt values
    time_scale: float = 1.0        # 1x, 5x, 20x
    paused: bool = False
    seed: int = 12345              # deterministic randomness


@dataclass(slots=True)
class World:
    """
    Simulation world. Owns entities, time, deterministic RNG, and stepping logic.
    UI should interact with this class via a thin adapter/controller.

    Design goals:
    - deterministic stepping (fixed dt option)
    - headless-friendly (no UI dependencies)
    - easy to log for ML later
    """
    config: WorldConfig = field(default_factory=WorldConfig)

    # time bookkeeping
    t: float = 0.0

    # deterministic RNG (Random Number Generator)
    rng: np.random.Generator = field(init=False)

    # entity storage
    _entities: Dict[str, Entity] = field(default_factory=dict)

    # optional callbacks (useful for logging / ML data collection)
    _tick_listeners: List = field(default_factory=list)

    def __post_init__(self) -> None:
        self.rng = np.random.default_rng(self.config.seed)

    # --- basic API ---
    def get_time(self) -> float:
        return float(self.t)

    def add(self, e: Entity) -> None:
        if e.eid in self._entities:
            raise ValueError(f"Entity id already exists: {e.eid}")
        self._entities[e.eid] = e

    def remove(self, eid: str) -> None:
        self._entities.pop(eid, None)

    def get(self, eid: str) -> Optional[Entity]:
        return self._entities.get(eid)

    def entities(self) -> Iterable[Entity]:
        return self._entities.values()

    def living_entities(self) -> List[Entity]:
        return [e for e in self._entities.values() if e.alive]

    def set_paused(self, paused: bool) -> None:
        self.config.paused = bool(paused)

    def set_time_scale(self, scale: float) -> None:
        self.config.time_scale = float(scale)

    def on_tick(self, fn) -> None:
        """
        Register a callback: fn(world, dt, entities_snapshot) -> None
        Use for logging, metrics, ML dataset collection.
        """
        self._tick_listeners.append(fn)

    # --- stepping ---
    def step(self, dt_real: float, *, use_fixed_dt: bool = True) -> None:
        """
        Advance the simulation by dt_real seconds of wall-clock time.
        If paused, does nothing.

        If use_fixed_dt=True, will subdivide dt into fixed steps for stability and determinism.
        """
        if self.config.paused:
            return

        dt_scaled = float(dt_real) * float(self.config.time_scale)
        if dt_scaled <= 0.0:
            return

        if use_fixed_dt:
            self._step_fixed(dt_scaled)
        else:
            self._step_variable(dt_scaled)

    def _step_variable(self, dt: float) -> None:
        # Single-step variable dt (less deterministic if dt varies frame-to-frame)
        self._tick(dt)

    def _step_fixed(self, dt: float) -> None:
        fixed = float(self.config.fixed_dt)
        # Cap substeps so a hitch doesn't explode CPU
        max_dt = fixed * float(self.config.max_substeps)
        if dt > max_dt:
            dt = max_dt

        # Substep loop
        n = int(np.floor(dt / fixed))
        rem = dt - n * fixed

        for _ in range(n):
            self._tick(fixed)
        if rem > 1e-12:
            self._tick(rem)

    def _tick(self, dt: float) -> None:
        # 1) pre-step hooks (compute vel, AI, control laws later)
        for e in self._entities.values():
            if e.alive:
                e.pre_step(self, dt)

        # 2) integrate entities
        for e in self._entities.values():
            if e.alive:
                e.step(self, dt)

        # 3) post-step hooks (collisions, intercept checks later)
        for e in self._entities.values():
            if e.alive:
                e.post_step(self, dt)

        # 4) time update
        self.t = float(self.t + dt)

        # 5) listeners (useful for logging / ML)
        if self._tick_listeners:
            snapshot = self.snapshot()
            for fn in self._tick_listeners:
                fn(self, dt, snapshot)

    # --- utilities helpful for UI tools / ML ---
    def snapshot(self) -> Dict[str, Dict]:
        """
        Return a cheap, JSON-serializable snapshot of world state.
        Useful for logging, replays, ML dataset generation.
        """
        out: Dict[str, Dict] = {}
        for eid, e in self._entities.items():
            k = e.kin
            out[eid] = {
                "kind": e.kind,
                "alive": e.alive,
                "x": float(k.pos[0]),
                "y": float(k.pos[1]),
                "vx": float(k.vel[0]),
                "vy": float(k.vel[1]),
                "heading": float(k.heading),
                "speed": float(k.speed),
                "turn_rate": float(k.turn_rate),
                "radius": float(e.radius),
                "team": e.team,
            }
        return out

    def positions_array(self, *, living_only: bool = True) -> Tuple[np.ndarray, List[str]]:
        """
        Return Nx2 positions array plus matching entity id list.
        This is handy for fast range/bearing computations in NumPy.
        """
        ents = self.living_entities() if living_only else list(self._entities.values())
        ids = [e.eid for e in ents]
        pos = np.vstack([e.kin.pos for e in ents]) if ents else np.zeros((0, 2), dtype=np.float64)
        return pos, ids

    def find_nearest(self, point: Vec2, *, kind: Optional[str] = None) -> Optional[Entity]:
        """
        Simple nearest-neighbor query (O(N)). Good enough initially.
        Later you can add spatial hashing / k-d tree if needed.
        """
        best_e: Optional[Entity] = None
        best_d2: float = float("inf")
        for e in self._entities.values():
            if not e.alive:
                continue
            if kind is not None and e.kind != kind:
                continue
            d = e.kin.pos - point
            d2 = float(d[0] * d[0] + d[1] * d[1])
            if d2 < best_d2:
                best_d2 = d2
                best_e = e
        return best_e