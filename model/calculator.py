"""High-level calculation pipeline for the engine prototype."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from model.fatigue import basquin_life, goodman_amplitude, operating_time
from model.geometry import Geometry
from model.stress import estimate_stress, thermal_stress
from model.thermodynamics import calculate_cycle


@dataclass
class CalculationInput:
    geometry: Geometry
    rpm: float
    initial_pressure: float
    initial_temperature: float
    volumetric_efficiency: float
    lambda_value: float
    fuel: dict
    material: dict
    piston_mass: float
    pin_mass: float
    rod_mass: float
    rod_factor: float
    combustion_start: float
    combustion_duration: float
    wiebe_a: float
    wiebe_m: float
    wall_heat_loss: float
    crankcase_pressure: float = 101325.0


@dataclass
class CalculationResult:
    result: object
    fuel_mass: float
    released_energy: float
    displacement: float
    pressure_max: float
    temperature_max: float
    gas_force_max: float
    inertial_force_max: float
    rod_force_max: float
    side_force_max: float
    stress_max: float
    thermal_stress_max: float
    fatigue_amplitude: float
    fatigue_life: float
    operating_time_seconds: float


def calculate(input_data: CalculationInput) -> CalculationResult:
    """Run the complete geometry-to-fatigue pipeline in SI units."""
    geometry = input_data.geometry
    fuel = input_data.fuel
    material = input_data.material
    air_mass = 1.225 * geometry.displacement * input_data.volumetric_efficiency
    fuel_mass = air_mass / (input_data.lambda_value * fuel["AFR_st"])
    released_energy = fuel_mass * fuel["LHV"] * 0.9
    cycle = calculate_cycle(
        geometry=geometry,
        rpm=input_data.rpm,
        initial_pressure=input_data.initial_pressure,
        initial_temperature=input_data.initial_temperature,
        fuel_mass=fuel_mass,
        fuel_lhv=fuel["LHV"],
        air_density=1.225,
        volumetric_efficiency=input_data.volumetric_efficiency,
        lambda_value=input_data.lambda_value,
        afr_st=fuel["AFR_st"],
        gamma=fuel["gamma"],
        gas_constant=fuel["R"],
        combustion_efficiency=0.9,
        start_angle=input_data.combustion_start,
        burn_duration=input_data.combustion_duration,
        wiebe_a=input_data.wiebe_a,
        wiebe_m=input_data.wiebe_m,
        wall_heat_loss=input_data.wall_heat_loss,
        crankcase_pressure=input_data.crankcase_pressure,
        mass_rec=input_data.piston_mass + input_data.pin_mass + input_data.rod_factor * input_data.rod_mass,
    )

    temperature_delta = np.max(cycle.temperature) - input_data.initial_temperature
    thermal = thermal_stress(
        temperature_delta,
        material["E"],
        material["alpha"],
        0.5,
    )
    effective_section_area = math.pi * geometry.diameter * 0.004
    stress, _ = estimate_stress(
        cycle.rod_force,
        effective_section_area,
        2.0,
        np.full_like(cycle.rod_force, thermal),
    )
    cycle.stress = stress
    cycle.thermal_stress = np.full_like(cycle.rod_force, thermal)

    mean_stress, amplitude, _ = goodman_amplitude(
        float(np.max(stress - thermal)),
        float(np.min(stress - thermal)),
        material["fatigue_strength"],
        material["ultimate_strength"],
    )
    goodman_factor = 1.0 - mean_stress / material["ultimate_strength"]
    if goodman_factor <= 0.0:
        fatigue_life = 0.0
    else:
        corrected_amplitude = amplitude / goodman_factor
        fatigue_life = basquin_life(
            corrected_amplitude,
            material["sigma_f_prime"],
            material["b"],
        )

    return CalculationResult(
        result=cycle,
        fuel_mass=fuel_mass,
        released_energy=released_energy,
        displacement=geometry.displacement,
        pressure_max=float(np.max(cycle.pressure)),
        temperature_max=float(np.max(cycle.temperature)),
        gas_force_max=float(np.max(np.abs(cycle.gas_force))),
        inertial_force_max=float(np.max(np.abs(cycle.inertial_force))),
        rod_force_max=float(np.max(np.abs(cycle.rod_force))),
        side_force_max=float(np.max(np.abs(cycle.side_force))),
        stress_max=float(np.max(np.abs(stress))),
        thermal_stress_max=float(thermal),
        fatigue_amplitude=float(amplitude),
        fatigue_life=float(fatigue_life),
        operating_time_seconds=operating_time(fatigue_life, input_data.rpm),
    )
