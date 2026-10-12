"""Minimal PySide6 main window for the engine prototype."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGroupBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from model.calculator import CalculationInput, calculate
from model.data import load_fuels, load_materials
from model.geometry import Geometry
class MainWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("моё тп отменено")
        self.resize(1500, 900)
        self.fuels = load_fuels()
        self.materials = load_materials()
        self.fields: dict[str, QLineEdit] = {}
        self._last_output = None
        self._build_ui()
        self._load_defaults()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        header = QHBoxLayout()
        header.addWidget(QLabel("Прототип расчёта двигателя"))
        header.addStretch()
        self.status = QLabel("Готово")
        header.addWidget(self.status)
        root.addLayout(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        main_layout = QGridLayout(content)
        main_layout.setColumnStretch(0, 2)
        main_layout.setColumnStretch(1, 1)
        main_layout.setColumnStretch(2, 1)

        control_layout = QVBoxLayout()
        for group_name, fields in (
            ("Параметры двигателя", [
                ("diameter", "D, мм", 80.0),
                ("stroke", "S, мм", 80.0),
                ("rod_length", "L, мм", 150.0),
                ("compression_ratio", "ε", 10.0),
                ("rpm", "n, об/мин", 4000.0),
                ("piston_mass", "m_поршня, кг", 0.4),
                ("pin_mass", "m_shuttle, кг", 0.1),
                ("rod_mass", "m_шатуна, кг", 0.3),
                ("rod_factor", "k_шатуна", 0.25),
            ]),
            ("Параметры работы", [
                ("initial_pressure", "Начальное давление, бар", 1.0),
                ("initial_temperature", "Начальная температура, °C", 300.0),
                ("volumetric_efficiency", "ηv", 0.9),
                ("lambda_value", "λ", 1.0),
                ("combustion_efficiency", "ηc", 0.9),
                ("combustion_start", "Начало сгорания, °", 350.0),
                ("combustion_duration", "Длительность, °", 32.0),
                ("wiebe_a", "Wiebe a", 5.0),
                ("wiebe_m", "Wiebe m", 2.0),
                ("wall_heat_loss", "Тепловые потери", 0.0),
            ]),
        ):
            group = QGroupBox(group_name)
            group_layout = QGridLayout(group)
            group_layout.setColumnStretch(0, 1)
            group_layout.setColumnStretch(1, 1)
            for row, (key, label, default) in enumerate(fields):
                field_label = QLabel(label)
                line = QLineEdit(str(default))
                line.setObjectName(key)
                self.fields[key] = line
                group_layout.addWidget(field_label, row, 0)
                group_layout.addWidget(line, row, 1)
            control_layout.addWidget(group)
        main_layout.addLayout(control_layout, 0, 0)

        fuel_group = QGroupBox("Топливо")
        fuel_layout = QHBoxLayout(fuel_group)
        self.fuel_combo = self._make_combo("fuel_combo", self.fuels)
        self.custom_fuel = QGroupBox("Параметры топлива")
        custom_layout = QHBoxLayout(self.custom_fuel)
        self.custom_fields = {}
        for key, label, default in (
            ("LHV", "LHV, Дж/кг", 43e6),
            ("density", "Плотность, кг/м³", 740.0),
            ("AFR_st", "AFR_st", 14.7),
            ("gamma", "Коэффициент γ", 1.35),
            ("R", "R, Дж/кг·К", 287.0),
        ):
            item = QVBoxLayout()
            item.addWidget(QLabel(label))
            line = QLineEdit(str(default))
            line.setEnabled(False)
            item.addWidget(line)
            self.custom_fields[key] = line
            custom_layout.addLayout(item)
        fuel_layout.addWidget(self.fuel_combo, 1)
        fuel_layout.addWidget(self.custom_fuel, 2)
        main_layout.addWidget(fuel_group, 1, 0)

        material_group = QGroupBox("Материал поршня")
        material_layout = QHBoxLayout(material_group)
        self.material_combo = self._make_combo("material_combo", self.materials)
        material_layout.addWidget(self.material_combo)
        main_layout.addWidget(material_group, 2, 1)

        results_group = QGroupBox("Результаты расчёта")
        results_layout = QGridLayout(results_group)
        results_layout.setColumnStretch(0, 1)
        results_layout.setColumnStretch(1, 1)
        self.result_labels = [
            ("Давление", "—"),
            ("Температура", "—"),
            ("Сила шатуна", "—"),
            ("Напряжение", "—"),
            ("Ресурс, циклов", "—"),
            ("Энергия топлива за цикл", "—"),
            ("Время работы при заданных оборотах", "—"),
            ("Состояние", "—"),
            ("Средние обороты", "—"),
        ]
        self.results_layout = results_layout
        for row, (label, value) in enumerate(self.result_labels):
            results_layout.addWidget(QLabel(label), row, 0)
            results_layout.addWidget(QLabel(value), row, 1)
        main_layout.addWidget(results_group, 1, 2)

        graph_group = QGroupBox("Графики работы двигателя")
        graph_layout = QVBoxLayout(graph_group)
        self.figure = Figure(figsize=(10, 6), tight_layout=True)
        self.graph_canvas = FigureCanvasQTAgg(self.figure)
        self.graph_canvas.setMinimumHeight(460)
        self.graph_axes = self.figure.subplots(2, 2)
        self._secondary_graph_axes = []
        self._fatigue_annotation = None
        self._draw_empty_graphs()
        graph_layout.addWidget(self.graph_canvas)
        main_layout.addWidget(graph_group, 0, 1, 1, 2)
        fatigue_group = QGroupBox("Усталость материала и ресурс двигателя")
        fatigue_layout = QVBoxLayout(fatigue_group)
        self.fatigue_figure = Figure(figsize=(5, 3), tight_layout=True)
        self.fatigue_canvas = FigureCanvasQTAgg(self.fatigue_figure)
        self.fatigue_canvas.setMinimumHeight(260)
        self.fatigue_axis = self.fatigue_figure.subplots()
        self._draw_empty_fatigue_graph()
        fatigue_layout.addWidget(self.fatigue_canvas)
        main_layout.addWidget(fatigue_group, 1, 1)

        buttons = QHBoxLayout()
        calculate_button = QPushButton("Рассчитать")
        calculate_button.clicked.connect(self.calculate)
        buttons.addWidget(calculate_button)
        export_button = QPushButton("Сохранить результат")
        export_button.clicked.connect(lambda: self._save_result(self._last_output))
        buttons.addWidget(export_button)
        main_layout.addLayout(buttons, 3, 0, 1, 3)
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

    def _make_combo(self, name: str, data: dict) -> object:
        from PySide6.QtWidgets import QComboBox
        combo = QComboBox()
        combo.setObjectName(name)
        for key, value in data.items():
            combo.addItem(value.get("name", key), key)
        combo.currentIndexChanged.connect(self._on_combo_changed)
        return combo

    def _on_combo_changed(self) -> None:
        fuel_key = self.fuel_combo.currentData()
        custom_enabled = fuel_key == "custom"
        for line in self.custom_fields.values():
            line.setEnabled(custom_enabled)

    def _load_defaults(self) -> None:
        self.fuel_combo.setCurrentIndex(self.fuel_combo.findData("gasoline"))
        self.material_combo.setCurrentIndex(self.material_combo.findData("aluminium"))
        self._on_combo_changed()

    def calculate(self) -> None:
        try:
            geometry = Geometry(
                diameter=float(self.fields["diameter"].text()) / 1000.0,
                stroke=float(self.fields["stroke"].text()) / 1000.0,
                rod_length=float(self.fields["rod_length"].text()) / 1000.0,
                compression_ratio=float(self.fields["compression_ratio"].text()),
            )
            fuel_key = self.fuel_combo.currentData()
            fuel = self.fuels[fuel_key].copy()
            if fuel_key == "custom":
                fuel.update({key: float(line.text()) for key, line in self.custom_fields.items()})
            material_key = self.material_combo.currentData()
            material = self.materials[material_key].copy()
            input_data = CalculationInput(
                geometry=geometry,
                rpm=float(self.fields["rpm"].text()),
                initial_pressure=float(self.fields["initial_pressure"].text()) * 1e5,
                initial_temperature=float(self.fields["initial_temperature"].text()) + 273.15,
                volumetric_efficiency=float(self.fields["volumetric_efficiency"].text()),
                lambda_value=float(self.fields["lambda_value"].text()),
                fuel=fuel,
                material=material,
                piston_mass=float(self.fields["piston_mass"].text()),
                pin_mass=float(self.fields["pin_mass"].text()),
                rod_mass=float(self.fields["rod_mass"].text()),
                rod_factor=float(self.fields["rod_factor"].text()),
                combustion_start=float(self.fields["combustion_start"].text()),
                combustion_duration=float(self.fields["combustion_duration"].text()),
                wiebe_a=float(self.fields["wiebe_a"].text()),
                wiebe_m=float(self.fields["wiebe_m"].text()),
                wall_heat_loss=float(self.fields["wall_heat_loss"].text()),
            )
            output = calculate(input_data)
            self._last_output = output
            self.status.setText(
                f"Рассчитано: {output.pressure_max / 1e5:.2f} бар, "
                f"{output.temperature_max - 273.15:.1f} °C"
            )
            self._update_graphs(output, material, input_data.rpm)
            for index, (label, _) in enumerate(self.result_labels):
                values = [
                    f"{output.pressure_max / 1e5:.2f} бар",
                    f"{output.temperature_max - 273.15:.1f} °C",
                    f"{output.rod_force_max / 1000:.2f} кН",
                    f"{output.stress_max / 1e6:.2f} МПа",
                    self._format_scientific(output.fatigue_life, "цикла"),
                    f"{output.released_energy / 1000:.3f} кДж",
                    f"{self._format_scientific(output.operating_time_seconds / 3600, 'ч')} "
                    f"при {input_data.rpm:.0f} об/мин",
                    "сломался(((((" if output.fatigue_life <= 1e5 else "Нормально",
                    f"{input_data.rpm:.0f}",
                ]
                self.result_labels[index] = (label, values[index])
                self.results_layout.itemAtPosition(index, 1).widget().setText(values[index])
            self._save_result(output)
        except (ValueError, KeyError, RuntimeError, ZeroDivisionError) as error:
            self.status.setText(f"Ошибка: {error}")

    @staticmethod
    def _format_scientific(value: float, unit: str) -> str:
        if math.isinf(value):
            return f"Бесконечно {unit}"
        if value == 0.0:
            return f"0 {unit}"
        mantissa, exponent = f"{value:.2e}".split("e")
        superscript = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")
        exponent_text = str(int(exponent)).translate(superscript)
        return f"{mantissa.replace('.', ',')} × 10{exponent_text} {unit}"

    def _draw_empty_graphs(self) -> None:
        titles = (
            "Давление и температура",
            "Силы в механизме",
            "Напряжение поршня",
            "Движение поршня",
        )
        for axis, title in zip(self.graph_axes.flat, titles):
            axis.set_title(title)
            axis.set_xlabel("Угол коленвала (°)")
            axis.grid(True, alpha=0.3)
        self.graph_canvas.draw_idle()

    def _draw_empty_fatigue_graph(self) -> None:
        self.fatigue_axis.set_title("Кривая усталости материала (S–N)")
        self.fatigue_axis.set_xlabel("Число циклов до разрушения")
        self.fatigue_axis.set_ylabel("Амплитуда напряжения (МПа)")
        self.fatigue_axis.set_xscale("log")
        self.fatigue_axis.set_yscale("log")
        self.fatigue_axis.grid(True, which="both", alpha=0.3)
        self.fatigue_canvas.draw_idle()

    def _update_graphs(self, output, material: dict, rpm: float) -> None:
        result = output.result
        angle = np.degrees(result.crank_angle)
        pressure_axis, force_axis, stress_axis, motion_axis = self.graph_axes.flat
        for axis in self._secondary_graph_axes:
            axis.remove()
        self._secondary_graph_axes.clear()
        for axis in self.graph_axes.flat:
            axis.clear()
            axis.grid(True, alpha=0.3)

        pressure_axis.plot(angle, result.pressure / 1e5, color="#1976d2", label="Давление, бар")
        pressure_axis.set_xlabel("Угол коленвала (°)")
        pressure_axis.set_ylabel("Давление (бар)")
        pressure_axis.set_title("Давление и температура")
        temperature_axis = pressure_axis.twinx()
        self._secondary_graph_axes.append(temperature_axis)
        temperature_axis.plot(angle, result.temperature - 273.15, color="#e4572e", label="Температура, °C")
        temperature_axis.set_ylabel("Температура (°C)")
        handles, labels = pressure_axis.get_legend_handles_labels()
        other_handles, other_labels = temperature_axis.get_legend_handles_labels()
        pressure_axis.legend(handles + other_handles, labels + other_labels, loc="best", fontsize=8)

        force_axis.plot(angle, result.gas_force / 1000, label="Газовая", linewidth=1.0)
        force_axis.plot(angle, result.inertial_force / 1000, label="Инерционная", linewidth=1.0)
        force_axis.plot(angle, result.total_force / 1000, label="Суммарная", linewidth=1.2)
        force_axis.set_xlabel("Угол коленвала (°)")
        force_axis.set_ylabel("Сила (кН)")
        force_axis.set_title("Силы в механизме")
        force_axis.legend(fontsize=8)

        stress_axis.plot(angle, result.stress / 1e6, color="#7b2cbf", linewidth=1.1)
        stress_axis.set_xlabel("Угол коленвала (°)")
        stress_axis.set_ylabel("Напряжение (МПа)")
        stress_axis.set_title("Напряжение поршня")

        motion_axis.plot(angle, result.piston_position * 1000, label="Положение, мм")
        motion_axis.set_xlabel("Угол коленвала (°)")
        motion_axis.set_ylabel("Положение (мм)")
        motion_axis.set_title("Движение поршня")
        speed_axis = motion_axis.twinx()
        self._secondary_graph_axes.append(speed_axis)
        speed_axis.plot(angle, result.piston_velocity, color="#e4572e", label="Скорость, м/с")
        speed_axis.set_ylabel("Скорость (м/с)")
        handles, labels = motion_axis.get_legend_handles_labels()
        other_handles, other_labels = speed_axis.get_legend_handles_labels()
        motion_axis.legend(handles + other_handles, labels + other_labels, loc="best", fontsize=8)
        self.figure.tight_layout()
        self.graph_canvas.draw_idle()

        self.fatigue_axis.clear()
        cycles = np.geomspace(1.0, 1e12, 300)
        sn_stress = material["sigma_f_prime"] * (2.0 * cycles) ** material["b"]
        self.fatigue_axis.loglog(cycles, sn_stress / 1e6, label="Кривая материала")
        self.fatigue_axis.set_xlabel("Число полных циклов до разрушения")
        self.fatigue_axis.set_ylabel("Амплитуда напряжения (МПа)")
        self.fatigue_axis.set_title("Усталость материала и расчётный ресурс")
        self.fatigue_axis.grid(True, which="both", alpha=0.3)

        mechanical_stress = result.stress - result.thermal_stress
        mean_stress = 0.5 * (float(np.max(mechanical_stress)) + float(np.min(mechanical_stress)))
        alternating_stress = 0.5 * (float(np.max(mechanical_stress)) - float(np.min(mechanical_stress)))
        goodman_factor = 1.0 - mean_stress / material["ultimate_strength"]
        corrected_stress = alternating_stress / goodman_factor if goodman_factor > 0.0 else math.inf
        life_cycles = output.fatigue_life
        life_hours = output.operating_time_seconds / 3600.0
        if math.isfinite(life_cycles) and life_cycles > 0.0 and math.isfinite(corrected_stress):
            self.fatigue_axis.scatter(
                [life_cycles], [corrected_stress / 1e6], color="#e4572e", zorder=4,
                label="Расчётная нагрузка",
            )
            self.fatigue_axis.axvline(life_cycles, color="#e4572e", linestyle="--", alpha=0.65)
        resource_text = (
            f"Ресурс: {self._format_scientific(life_cycles, 'циклов')}\n"
            f"{self._format_scientific(life_hours, 'ч')} при {rpm:.0f} об/мин"
        )
        if goodman_factor <= 0.0:
            resource_text = "Среднее напряжение выше предела прочности\nРазрушение ожидается до 1 цикла"
        self.fatigue_axis.text(
            0.03, 0.04, resource_text, transform=self.fatigue_axis.transAxes,
            ha="left", va="bottom", fontsize=8,
            bbox={"facecolor": "white", "alpha": 0.8, "edgecolor": "#cccccc"},
        )
        self.fatigue_axis.legend(loc="upper right", fontsize=8)
        self.fatigue_figure.tight_layout()
        self.fatigue_canvas.draw_idle()

    def _save_result(self, output) -> None:
        if output is None:
            self.status.setText("Сначала нажмите «Рассчитать».")
            return
        path = Path(__file__).resolve().parents[1] / "engine_result.json"
        data = {
            "fuel_mass": output.fuel_mass,
            "released_energy": output.released_energy,
            "pressure_max_bar": output.pressure_max / 1e5,
            "temperature_max_C": output.temperature_max - 273.15,
            "gas_force_max_N": output.gas_force_max,
            "rod_force_max_N": output.rod_force_max,
            "stress_max_MPa": output.stress_max / 1e6,
            "fatigue_life_cycles": output.fatigue_life,
            "operating_time_hours": output.operating_time_seconds / 3600.0,
            "fatigue_state": "фрик" if output.fatigue_life <= 1e5 else "нормально",
        }
        Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    application = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.show()
    application.exec()


if __name__ == "__main__":
    main()
