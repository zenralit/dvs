"""Geometry of a simplified single-cylinder crankshaft mechanism."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


@dataclass
class Geometry:
    """Dimensions in metres; the model assumes a single-cylinder engine."""

    diameter: float
    stroke: float
    rod_length: float
    compression_ratio: float

    def __post_init__(self) -> None:
        if self.diameter <= 0.0 or self.stroke <= 0.0:
            raise ValueError("Diameter and stroke must be positive")
        if self.compression_ratio <= 1.0:
            raise ValueError("Compression ratio must be greater than one")
        if self.rod_length <= self.stroke / 2.0:
            raise ValueError("Rod length must be greater than crank radius")

    @property
    def crank_radius(self) -> float:
        return self.stroke / 2.0

    @property
    def displacement(self) -> float:
        return math.pi * self.diameter**2 / 4.0 * self.stroke

    @property
    def cylinder_clearance(self) -> float:
        return self.displacement / (self.compression_ratio - 1.0)

    @property
    def area(self) -> float:
        return math.pi * self.diameter**2 / 4.0

    def piston_position(self, theta: float | np.ndarray) -> float | np.ndarray:
        """Return piston displacement from TDC in metres.

        The displacement is measured from the TDC position at theta = 0.
        """
        theta = np.asarray(theta, dtype=float)
        crank_radius = self.crank_radius
        rod_length = self.rod_length
        position = (
            crank_radius
            + rod_length
            - crank_radius * np.cos(theta)
            - np.sqrt(rod_length**2 - crank_radius**2 * np.sin(theta) ** 2)
        )
        return position.item() if np.ndim(theta) == 0 else position

    def volume(self, theta: float | np.ndarray) -> float | np.ndarray:
        """Cylinder volume in m^3 using V_c + A_p*s(theta)."""
        return self.cylinder_clearance + self.area * self.piston_position(theta)

    def piston_velocity(self, theta: float, rpm: float) -> float:
        """Analytical piston velocity using d s / d t."""
        omega = 2.0 * math.pi * rpm / 60.0
        sin_theta = math.sin(theta)
        sqrt_term = math.sqrt(self.rod_length**2 - self.crank_radius**2 * sin_theta**2)
        derivative = self.crank_radius * sin_theta + (
            self.crank_radius**2 * sin_theta * math.cos(theta) / sqrt_term
        )
        return derivative * omega

    def piston_acceleration(self, theta: float, rpm: float) -> float:
        """Analytical piston acceleration using d^2 s / d t^2."""
        omega = 2.0 * math.pi * rpm / 60.0
        sin_theta = math.sin(theta)
        cos_theta = math.cos(theta)
        sqrt_term = math.sqrt(self.rod_length**2 - self.crank_radius**2 * sin_theta**2)
        second_derivative = (
            self.crank_radius * cos_theta
            + self.crank_radius**2
            * (
                cos_theta**2
                - sin_theta**2
                + (self.crank_radius**2 * sin_theta**2 / sqrt_term**2)
            )
            / sqrt_term
        )
        return second_derivative * omega**2
