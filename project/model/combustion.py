"""A compact Wiebe-function combustion model."""

from __future__ import annotations

import math

import numpy as np


def wiebe_fraction(theta: float | np.ndarray, start_angle: float, duration: float, a: float, m: float) -> float | np.ndarray:
    """Calculate the Wiebe progress fraction with boundary-safe handling."""
    if duration <= 0.0 or a <= 0.0 or m <= -1.0:
        raise ValueError("Combustion duration and shape parameters are invalid")
    angles = np.asarray(theta, dtype=float)
    normalized = (angles - start_angle) / duration
    progress = np.where(angles < start_angle, 0.0, normalized)
    progress = np.where(progress > 1.0, 1.0, progress)
    exponent = m + 1.0
    value = 1.0 - np.exp(-a * np.power(np.clip(progress, 0.0, 1.0), exponent))
    value = np.where(angles > start_angle + duration, 1.0, value)
    value = np.where(angles < start_angle, 0.0, value)
    return value.item() if np.ndim(theta) == 0 else value


def heat_release_rate(theta: float | np.ndarray, total_energy: float, start_angle: float, duration: float, a: float, m: float) -> float | np.ndarray:
    """Return dQ_comb/dtheta in J/rad, including explicit derivative of Wiebe."""
    angles = np.asarray(theta, dtype=float)
    normalized = (angles - start_angle) / duration
    active = (angles >= start_angle) & (angles <= start_angle + duration)
    exponent = m + 1.0
    derivative = np.zeros_like(angles, dtype=float)
    active_indices = np.flatnonzero(active)
    clipped = np.clip(normalized[active_indices], 0.0, 1.0)
    intermediate = np.power(clipped, m)
    derivative[active_indices] = (
        total_energy
        * a
        * exponent
        / duration
        * intermediate
        * np.exp(-a * np.power(clipped, exponent))
    )
    return derivative.item() if np.ndim(theta) == 0 else derivative


def total_heat_release(theta: float | np.ndarray, total_energy: float, start_angle: float, duration: float, a: float, m: float) -> float | np.ndarray:
    """Return the cumulative heat release Q(theta)."""
    return total_energy * wiebe_fraction(theta, start_angle, duration, a, m)
