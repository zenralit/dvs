"""Simplified piston stress evaluation, not a finite-element model."""

from __future__ import annotations

import math

import numpy as np


def estimate_stress(
    rod_force: np.ndarray,
    area_eff: float,
    concentration_factor: float,
    temperature_stress: np.ndarray,
    mechanical_offset: float = 0.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Estimate local stress in a critical piston zone using nominal load."""
    nominal = rod_force / max(area_eff, np.finfo(float).eps)
    local = concentration_factor * nominal
    stress = local + temperature_stress + mechanical_offset
    return stress, nominal


def piston_temperature_distribution(crown_temperature: float, skirt_temperature: float, height: float) -> np.ndarray:
    """Return a simple linear crown-to-skirt temperature profile."""
    if height <= 0.0:
        raise ValueError("Piston height must be positive")
    return skirt_temperature + (crown_temperature - skirt_temperature) * (1.0 - np.linspace(0.0, 1.0, 101))


def thermal_stress(temperature_delta: float, young_modulus: float, alpha: float, constraint_factor: float) -> float:
    """Calculate an upper-bound thermal stress estimate."""
    return constraint_factor * young_modulus * alpha * temperature_delta
