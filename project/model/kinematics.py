"""Kinematic functions exposed for calculations and tests."""

from __future__ import annotations

import math

import numpy as np

from model.geometry import Geometry


def piston_position(theta: float | np.ndarray, geometry: Geometry) -> float | np.ndarray:
    """Return piston displacement from TDC for scalar or array angles."""
    return geometry.piston_position(theta)


def piston_velocity(theta: float, geometry: Geometry, rpm: float) -> float:
    """Return piston velocity in m/s."""
    return geometry.piston_velocity(theta, rpm)


def piston_acceleration(theta: float, geometry: Geometry, rpm: float) -> float:
    """Return piston acceleration in m/s^2."""
    return geometry.piston_acceleration(theta, rpm)


def rod_angle(theta: float, geometry: Geometry) -> float:
    """Return the connecting-rod angle in radians."""
    ratio = geometry.crank_radius / geometry.rod_length
    return math.asin(ratio * math.sin(theta))


def converted_velocity(theta: float, geometry: Geometry, rpm: float) -> float:
    """Compatibility wrapper around the SI piston velocity calculation."""
    return piston_velocity(theta, geometry, rpm)
