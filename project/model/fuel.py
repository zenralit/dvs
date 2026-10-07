"""Fuel and air mass calculations for the simplified combustion model."""

from __future__ import annotations

import math


def calculate_fuel_mass(
    air_mass: float,
    afr_stoichiometric: float,
    lambda_value: float,
    lower_heating_value: float,
) -> float:
    """Calculate fuel mass from air mass, AFR and excess-air coefficient."""
    if air_mass < 0.0 or afr_stoichiometric <= 0.0 or lambda_value <= 0.0:
        raise ValueError("Air mass and thermodynamic ratios must be positive")
    if lower_heating_value <= 0.0:
        raise ValueError("Lower heating value must be positive")
    return air_mass / (lambda_value * afr_stoichiometric)


def calculate_released_energy(
    fuel_mass: float,
    combustion_efficiency: float,
    lower_heating_value: float = 43e6,
) -> float:
    """Calculate useful combustion energy from fuel mass and efficiency."""
    if fuel_mass < 0.0 or not 0.0 <= combustion_efficiency <= 1.0:
        raise ValueError("Fuel mass must be nonnegative and efficiency must be between 0 and 1")
    if lower_heating_value <= 0.0:
        raise ValueError("Lower heating value must be positive")
    return fuel_mass * lower_heating_value * combustion_efficiency


def fuel_energy(fuel_mass: float, lower_heating_value: float, combustion_efficiency: float) -> float:
    """Calculate Q_comb = eta_c*m_f*H_u."""
    return calculate_released_energy(fuel_mass, combustion_efficiency, lower_heating_value)
