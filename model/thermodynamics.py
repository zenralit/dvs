"""One-zone thermodynamic calculation with a simplified first-law balance."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy.integrate import solve_ivp

from model.combustion import heat_release_rate
from model.forces import force_from_pressure, rod_and_side_forces
from model.geometry import Geometry


@dataclass
class CycleResult:
    crank_angle: np.ndarray
    volume: np.ndarray
    piston_position: np.ndarray
    piston_velocity: np.ndarray
    piston_acceleration: np.ndarray
    pressure: np.ndarray
    temperature: np.ndarray
    heat_release: np.ndarray
    heat_release_rate: np.ndarray
    gas_force: np.ndarray
    inertial_force: np.ndarray
    total_force: np.ndarray
    rod_force: np.ndarray
    side_force: np.ndarray
    stress: np.ndarray
    thermal_stress: np.ndarray
    fatigue_amplitude: float
    fatigue_life: float


def calculate_cycle(
    geometry: Geometry,
    rpm: float,
    initial_pressure: float,
    initial_temperature: float,
    fuel_mass: float,
    fuel_lhv: float,
    air_density: float,
    volumetric_efficiency: float,
    lambda_value: float,
    afr_st: float,
    gamma: float,
    gas_constant: float,
    combustion_efficiency: float,
    start_angle: float,
    burn_duration: float,
    wiebe_a: float,
    wiebe_m: float,
    wall_heat_loss: float,
    crankcase_pressure: float = 101325.0,
    mass_rec: float = 0.6,
    piston_mass: float = 0.4,
    pin_mass: float = 0.1,
    rod_mass: float = 0.3,
    rod_factor: float = 0.25,
) -> CycleResult:
    """Calculate a one-zone cycle in radians, with all internal values in SI."""
    if not 0.0 <= volumetric_efficiency <= 1.0 or not 0.0 <= combustion_efficiency <= 1.0:
        raise ValueError("Efficiency values must be between zero and one")
    if initial_pressure <= 0.0 or initial_temperature <= 0.0 or fuel_mass < 0.0:
        raise ValueError("Pressure and temperature must be positive and fuel mass nonnegative")
    if gamma <= 1.0 or gas_constant <= 0.0:
        raise ValueError("gamma must exceed one and gas constant must be positive")

    angles = np.linspace(0.0, 2.0 * math.pi, 721)
    volumes = np.asarray(geometry.volume(angles), dtype=float)
    if np.any(volumes <= 0.0):
        raise ValueError("Cylinder volume became non-positive")

    air_mass = air_density * geometry.displacement * volumetric_efficiency
    fuel_mass_total = fuel_mass
    total_energy = combustion_efficiency * fuel_mass_total * fuel_lhv
    combustion_start = math.radians(start_angle)
    combustion_duration = math.radians(burn_duration)
    heat_rate = heat_release_rate(
        angles, total_energy, combustion_start, combustion_duration, wiebe_a, wiebe_m
    )
    cumulative_heat = np.cumsum(heat_rate) * (angles[1] - angles[0])
    cumulative_heat = np.concatenate(([0.0], cumulative_heat))

    cv = gas_constant / (gamma - 1.0)
    temperature_initial = initial_temperature
    pressure_initial = initial_pressure
    volume_derivative = np.gradient(volumes, angles)

    def temperature_derivative(theta: float, temperature: float) -> float:
        """Integrated first-law balance: m cv dT/dtheta = dQ - p dV - dQ_wall."""
        volume_index = int(np.argmin(np.abs(angles - theta)))
        pressure = air_mass * gas_constant * temperature / volumes[volume_index]
        heat_input = float(np.interp(theta, angles, heat_rate))
        heat_loss = wall_heat_loss * (temperature - initial_temperature) / 360.0
        volume_rate = volume_derivative[volume_index]
        return (heat_input - pressure * volume_rate - heat_loss) / (air_mass * cv)

    solution = solve_ivp(
        lambda theta, state: [temperature_derivative(theta, float(state[0]))],
        (angles[0], angles[-1]),
        [temperature_initial],
        t_eval=angles,
        method="RK45",
        max_step=0.01,
    )
    if not solution.success:
        raise RuntimeError(f"Thermodynamic integration failed: {solution.message}")
    temperature_out = np.maximum(solution.y[0], 1.0)
    pressure_out = air_mass * gas_constant * temperature_out / volumes

    omega = 2.0 * math.pi * rpm / 60.0
    acceleration = np.array([
        geometry.piston_acceleration(theta, rpm) for theta in angles
    ])
    piston_position = np.asarray(geometry.piston_position(angles), dtype=float)
    piston_velocity = np.asarray(
        [geometry.piston_velocity(theta, rpm) for theta in angles], dtype=float
    )
    inertial_force = -mass_rec * acceleration
    gas_force = force_from_pressure(pressure_out, geometry.area, crankcase_pressure)
    total_force = gas_force + inertial_force
    rod_force, side_force = rod_and_side_forces(total_force, geometry, angles)

    result = CycleResult(
        crank_angle=angles,
        volume=volumes,
        piston_position=piston_position,
        piston_velocity=piston_velocity,
        piston_acceleration=acceleration,
        pressure=pressure_out,
        temperature=temperature_out,
        heat_release=cumulative_heat,
        heat_release_rate=heat_rate,
        gas_force=gas_force,
        inertial_force=inertial_force,
        total_force=total_force,
        rod_force=rod_force,
        side_force=side_force,
        stress=np.zeros_like(angles),
        thermal_stress=np.zeros_like(angles),
        fatigue_amplitude=0.0,
        fatigue_life=0.0,
    )
    return result
