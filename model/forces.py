"""Force conversion and connecting-rod force calculations."""

from __future__ import annotations

import math

import numpy as np

from model.geometry import Geometry


def force_from_pressure(pressure: np.ndarray, area: float, crankcase_pressure: float = 101325.0) -> np.ndarray:
    """Calculate gas force from pressure difference and piston area."""
    return (pressure - crankcase_pressure) * area


def rod_and_side_forces(
    total_force: np.ndarray,
    geometry: Geometry,
    crank_angle: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Calculate rod force and lateral force using connecting-rod geometry."""
    rod_angle = np.arcsin(
        (geometry.crank_radius / geometry.rod_length) * np.sin(crank_angle)
    )
    rod_force = total_force / np.cos(rod_angle)
    side_force = rod_force * np.sin(rod_angle)
    return rod_force, side_force


def inertial_force(acceleration: np.ndarray, mass: float) -> np.ndarray:
    """Calculate F_i = -m*a with a mass-reduced model."""
    return -mass * acceleration
