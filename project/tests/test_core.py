import unittest

import numpy as np

from model.geometry import Geometry
from model.fatigue import basquin_life, operating_time
from model.kinematics import piston_position, piston_velocity, piston_acceleration
from model.fuel import calculate_fuel_mass, calculate_released_energy
from model.thermodynamics import calculate_cycle
from model.stress import estimate_stress


class GeometryTests(unittest.TestCase):
    def setUp(self):
        self.geometry = Geometry(diameter=80.0, stroke=80.0, rod_length=150.0, compression_ratio=10.0)

    def test_volume_at_top_dead_center(self):
        volume = self.geometry.volume(0.0)
        self.assertAlmostEqual(volume, self.geometry.cylinder_clearance, places=9)

    def test_volume_at_bottom_dead_center(self):
        volume = self.geometry.volume(np.pi)
        self.assertAlmostEqual(volume, self.geometry.cylinder_clearance + self.geometry.displacement, places=9)

    def test_geometry_requires_rod_longer_than_crank_radius(self):
        with self.assertRaises(ValueError):
            Geometry(diameter=80.0, stroke=80.0, rod_length=20.0, compression_ratio=10.0)


class KinematicsTests(unittest.TestCase):
    def test_acceleration_scales_with_rpm_squared(self):
        geometry = Geometry(diameter=80.0, stroke=80.0, rod_length=150.0, compression_ratio=10.0)
        rpm_1 = 4000.0
        rpm_2 = 8000.0
        acceleration_1 = piston_acceleration(0.5, geometry, rpm_1)
        acceleration_2 = piston_acceleration(0.5, geometry, rpm_2)
        self.assertAlmostEqual(abs(acceleration_2 / acceleration_1), 4.0, delta=0.05)


class FuelTests(unittest.TestCase):
    def test_fuel_energy_increases_with_fuel_mass(self):
        base = calculate_fuel_mass(0.001, 14.7, 1.0, 43e6)
        doubled = calculate_fuel_mass(0.002, 14.7, 1.0, 43e6)
        self.assertGreater(calculate_released_energy(doubled, 0.9), calculate_released_energy(base, 0.9))


class FatigueTests(unittest.TestCase):
    def test_basquin_life_is_half_cycle_at_fatigue_strength(self):
        self.assertAlmostEqual(basquin_life(120e6, 120e6, -0.12), 0.5)

    def test_four_stroke_operating_time_matches_cycles_per_hour(self):
        cycles = 10_000_000
        rpm = 3000
        seconds = operating_time(cycles, rpm)
        hours = seconds / 3600.0
        self.assertAlmostEqual(hours, 111.111111, places=5)
        self.assertAlmostEqual(hours, cycles / (30.0 * rpm), places=10)

    def test_mechanical_stress_preserves_load_reversal(self):
        stress, _ = estimate_stress(
            np.array([-10.0, 10.0]),
            area_eff=2.0,
            concentration_factor=2.0,
            temperature_stress=np.zeros(2),
        )
        np.testing.assert_allclose(stress, [-10.0, 10.0])


class ThermodynamicsTests(unittest.TestCase):
    def test_cycle_has_positive_pressure_and_temperature(self):
        geometry = Geometry(diameter=80.0, stroke=80.0, rod_length=150.0, compression_ratio=10.0)
        result = calculate_cycle(
            geometry=geometry,
            rpm=4000.0,
            initial_pressure=1.0e5,
            initial_temperature=300.0,
            fuel_mass=0.0007,
            fuel_lhv=43e6,
            air_density=1.225,
            volumetric_efficiency=0.9,
            lambda_value=1.0,
            afr_st=14.7,
            gamma=1.35,
            gas_constant=287.0,
            combustion_efficiency=0.9,
            start_angle=350.0,
            burn_duration=32.0,
            wiebe_a=5.0,
            wiebe_m=2.0,
            wall_heat_loss=0.0,
        )
        self.assertTrue(np.all(result.pressure > 0.0))
        self.assertTrue(np.all(result.temperature > 0.0))
        self.assertTrue(np.all(np.isfinite(result.pressure)))


if __name__ == "__main__":
    unittest.main()
