# Simplified engine calculation prototype

This project provides a compact, demonstrator-only Python pipeline for the effects of piston-engine parameters, fuel properties, combustion, pressure, force, stress and fatigue. It is an educational engineering model, not a certification or CFD/FEM program.

## Mathematical model

The model uses SI units internally. The geometry uses

- `r = S / 2`
- `A_p = pi D^2 / 4`
- `V_d = A_p S`
- `V_c = V_d / (epsilon - 1)`
- `V(theta) = V_c + A_p s(theta)`

The piston position is

` s(theta) = r + L - r cos(theta) - sqrt(L^2 - r^2 sin^2(theta)) `.

Air mass is `m_air = rho_air V_d eta_v`. Fuel mass is

`m_f = m_air / (lambda AFR_st)`.

A simplified Wiebe function controls combustion:

`x_b(theta) = 1-exp[-a ((theta-theta0)/Delta theta)^(m+1)]`.

The one-zone first-law balance is

`m c_v dT/dtheta = dQ_comb/dtheta - p dV/dtheta - dQ_wall/dtheta`.

The equation of state is `pV = mRT`. Pressure, gas force and piston force are then calculated from the resulting cycle. A nominal stress estimate uses `sigma_nom = F/A_eff`, with a configurable concentration factor. Thermal stress uses `sigma_T ~ E alpha Delta T` as an upper-bound estimate. Fatigue uses Goodman and Basquin relations.

## Simplifications

- one cylinder, one thermodynamic zone;
- constant gas properties;
- no real chemical kinetics;
- no turbulence, CFD or FEM;
- no full heat-transfer model;
- discretely integrated `dQ/dtheta`;
- nominal stress only; no real piston structural distribution;
- fatigue life is an indicative estimate;
- no full 720-degree complete four-stroke model, although the calculation uses one full 720-degree cycle for plotting and comparison;
- the pressure result is intentionally not used as a certified engine prediction.

## Run

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run the GUI:

```powershell
python main.py
```

Run an automatic calculation without opening the GUI:

```powershell
python main.py --smoke-test
```

The defaults use `gasoline`, `aluminium alloy`, and representative values in `data/fuels.json` and `data/materials.json`.

## Project structure

- `main.py` — command entry point and smoke-test;
- `gui/main_window.py` — PySide6 interface;
- `model/geometry.py` — piston geometry;
- `model/kinematics.py` — piston position, velocity and acceleration;
- `model/fuel.py` — fuel and air-mass logic;
- `model/combustion.py` — Wiebe combustion;
- `model/thermodynamics.py` — one-zone energy balance;
- `model/forces.py` — force and rod-angle calculations;
- `model/stress.py` — nominal and thermal stress estimates;
- `model/fatigue.py` — Goodman and Basquin estimates;
- `model/calculator.py` — complete pipeline;
- `visualization/plots.py` — plots;
- `data/fuels.json` — representative fuel presets;
- `data/materials.json` — representative material presets;
- `tests/` — unit and model smoke tests.

## Tests

```powershell
python -m unittest discover -s tests -v
```

## Expected result

A normal run should produce positive finite pressure and temperature values, positive cylinder volume, and increasing fuel energy with fuel mass. Increasing RPM should increase inertial loading approximately with `RPM^2`. Peak pressure and output values are example-dependent and must not be interpreted as a real engine performance guarantee.

## License and use

This project is intended for demonstration and scientific article use. It is not suitable for engine certification, vehicle safety assessment, or professional structural design.
