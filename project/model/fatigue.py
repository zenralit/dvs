"""Simplified fatigue criteria and life estimate."""

from __future__ import annotations

import math


def goodman_amplitude(
    stress_max: float,
    stress_min: float,
    fatigue_strength: float,
    ultimate_strength: float,
) -> tuple[float, float]:
    """Return mean stress, amplitude and Goodman allowable amplitude."""
    mean_stress = 0.5 * (stress_max + stress_min)
    amplitude = 0.5 * (stress_max - stress_min)
    allowable = fatigue_strength * (1.0 - mean_stress / ultimate_strength)
    return mean_stress, amplitude, allowable


def basquin_life(amplitude: float, fatigue_strength: float, exponent: float) -> float:
    """Estimate cycles to failure with a Basquin relation."""
    if amplitude <= 0.0 or fatigue_strength <= 0.0 or exponent == 0.0:
        return math.inf
    return 0.5 * (amplitude / fatigue_strength) ** (1.0 / exponent)


def operating_time(cycles: float, rpm: float) -> float:
    """Return operating time in seconds for full four-stroke engine cycles."""
    if rpm <= 0.0:
        raise ValueError("Engine speed must be positive")
    return 120.0 * cycles / rpm
