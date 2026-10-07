"""Engineering plots for the calculation pipeline."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def plot_cycle(result, output_path: str | Path | None = None) -> None:
    """Построить график давления и температуры во время цикла."""
    plt.close("all")
    fig, axes = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
    angles = np.degrees(result.crank_angle)
    axes[0].plot(angles, result.pressure / 1e5, color="#1f77b4", linewidth=1.3, label="Давление")
    axes[0].set_ylabel("бар")
    axes[0].set_title("Давление и температура в цилиндре")
    axes[0].grid(True, alpha=0.3)
    axes[1].plot(angles, result.temperature - 273.15, color="#d62728", linewidth=1.3, label="Температура")
    axes[1].set_xlabel("Угол turned (°)")
    axes[1].set_ylabel("°C")
    axes[1].grid(True, alpha=0.3)
    fig.tight_layout()
    if output_path:
        fig.savefig(output_path, dpi=150)
    plt.show()
    plt.close(fig)


def plot_forces(result) -> None:
    """Построить графики газовых, инерционных и суммарных сил."""
    plt.close("all")
    fig, axis = plt.subplots(figsize=(9, 4))
    angle = np.degrees(result.crank_angle)
    axis.plot(angle, result.gas_force / 1000.0, label="Газовая сила", linewidth=1.2)
    axis.plot(angle, result.inertial_force / 1000.0, label="Инерционная сила", linewidth=1.2)
    axis.plot(angle, result.total_force / 1000.0, label="Суммарная сила", linewidth=1.4)
    axis.set_xlabel("Угол turned (°)")
    axis.set_ylabel("Сила (кН)")
    axis.set_title("Равновес сил")
    axis.grid(True, alpha=0.3)
    axis.legend()
    fig.tight_layout()
    plt.show()


def plot_stress(result) -> None:
    """Построить график напряжения поршня."""
    plt.close("all")
    fig, axis = plt.subplots(figsize=(9, 4))
    axis.plot(np.degrees(result.crank_angle), result.stress / 1e6, linewidth=1.3)
    axis.set_xlabel("Угол turned (°)")
    axis.set_ylabel("Напряжение (МПа)")
    axis.set_title("Напряжение поршня")
    axis.grid(True, alpha=0.3)
    fig.tight_layout()
    plt.show()


def plot_piston_motion(result) -> None:
    """Построить зависимости положения, скорости и ускорения поршня."""
    plt.close("all")
    fig, axes = plt.subplots(3, 1, figsize=(9, 8), sharex=True)
    angle = np.degrees(result.crank_angle)
    axes[0].plot(angle, result.piston_position * 1000.0, label="Положение", linewidth=1.2)
    axes[0].set_ylabel("Положение (мм)")
    axes[0].set_title("Движение поршня")
    axes[0].grid(True, alpha=0.3)
    axes[1].plot(angle, result.piston_velocity, label="Скорость", linewidth=1.2)
    axes[1].set_ylabel("Скорость (м/с)")
    axes[1].grid(True, alpha=0.3)
    axes[2].plot(angle, result.piston_acceleration / 1000.0, label="Ускорение", linewidth=1.2)
    axes[2].set_xlabel("Угол turned (°)")
    axes[2].set_ylabel("Ускорение (м/с²)")
    axes[2].grid(True, alpha=0.3)
    for axis in axes:
        axis.legend(loc="best")
    fig.tight_layout()
    plt.show()
    plt.close(fig)
