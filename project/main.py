"""Entry point for the engine calculation prototype."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from model.calculator import CalculationInput, calculate
from model.data import load_fuels, load_materials
from model.geometry import Geometry


def smoke_test() -> None:
    """Run a deterministic calculation without opening a GUI."""
    fuel = load_fuels()["gasoline"]
    material = load_materials()["aluminium"]
    geometry = Geometry(0.08, 0.08, 0.15, 10.0)
    output = calculate(
        CalculationInput(
            geometry=geometry,
            rpm=4000.0,
            initial_pressure=1.0e5,
            initial_temperature=300.0 + 273.15,
            volumetric_efficiency=0.9,
            lambda_value=1.0,
            fuel=fuel,
            material=material,
            piston_mass=0.4,
            pin_mass=0.1,
            rod_mass=0.3,
            rod_factor=0.25,
            combustion_start=350.0,
            combustion_duration=32.0,
            wiebe_a=5.0,
            wiebe_m=2.0,
            wall_heat_loss=0.0,
        )
    )
    print(f"максимальное давление, бар={output.pressure_max / 1e5:.3f}")
    print(f"максимальная температура, °C={output.temperature_max - 273.15:.2f}")
    print(f"максимальная сила шатуна, Н={output.rod_force_max:.2f}")
    print(f"максимальное напряжение, МПа={output.stress_max / 1e6:.3f}")
    print(f"энергия топлива за цикл, кДж={output.released_energy / 1000:.6g}")
    print(f"ресурс, циклов={output.fatigue_life:.6g}")
    print(f"время работы при {4000:g} об/мин, ч={output.operating_time_seconds / 3600:.6g}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the engine prototype")
    parser.add_argument("--smoke-test", action="store_true", help="Run one calculation and exit")
    args = parser.parse_args()
    if args.smoke_test:
        smoke_test()
        return

    from gui.main_window import MainWindow
    from PySide6.QtWidgets import QApplication

    application = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.show()
    application.exec()


if __name__ == "__main__":
    main()
