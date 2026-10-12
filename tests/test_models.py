import unittest

import numpy as np

from model.geometry import Geometry
from model.kinematics import piston_position, piston_velocity
from model.fuel import calculate_fuel_mass


class ModelSmokeTests(unittest.TestCase):
    def test_position_is_valid_over_cycle(self):
        geometry = Geometry(80.0, 80.0, 150.0, 10.0)
        angles = np.linspace(0.0, 2 * np.pi, 129)
        positions = piston_position(angles, geometry)
        self.assertTrue(np.all(positions >= 0.0))
        self.assertTrue(np.all(positions <= geometry.stroke))

    def test_velocity_is_zero_at_dead_centres(self):
        geometry = Geometry(80.0, 80.0, 150.0, 10.0)
        velocity_tdc = piston_velocity(0.0, geometry, 4000.0)
        velocity_bdc = piston_velocity(np.pi, geometry, 4000.0)
        self.assertAlmostEqual(velocity_tdc, 0.0, delta=1e-9)
        self.assertAlmostEqual(velocity_bdc, 0.0, delta=1e-9)

    def test_airflow_forces_fuel_mass(self):
        mass = calculate_fuel_mass(0.001, 14.7, 1.0, 43e6)
        self.assertGreater(mass, 0.0)
        self.assertAlmostEqual(mass, 0.00006802721088435374, delta=1e-12)


if __name__ == "__main__":
    unittest.main()
