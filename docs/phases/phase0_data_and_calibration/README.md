# Phase 0

## Title

Data Preparation And Electrical Calibration Inputs

## What This Phase Does

This phase prepares measured inputs and electrical calibration data for the later thermal, diffusion, and sheet-resistance workflows.

It mainly answers:

- how `SIMS + ECV` become the measured initial phosphorus profile
- where single-shot activation calibration data comes from
- where multi-shot activation bootstrap tables come from

## Main Entry Scripts

- `prepare_measured_initial_profile.py`
- `run_dual_channel_activation_calibration.py`
- `run_dual_channel_high_power_refit.py`
- `run_dual_channel_monotonic_segment_refit.py`
- `run_sheet_resistance_cases.py`

## Core Modules

- `src/laser_doping_sim/measured_profiles.py`
- `src/laser_doping_sim/activation_models.py`
- `src/laser_doping_sim/sheet_resistance.py`

## Main Inputs

- `inputs/raw_measurements/CTV-ECV-RAW.csv`
- `inputs/raw_measurements/CTV-SIMS-RAW.xlsx`
- `inputs/activation_models/measured_rsh_24_60w.csv`

## Main Outputs

- `inputs/measured_profiles/ctv_measured_initial_profile.csv`
- `inputs/measured_profiles/ctv_measured_initial_profile_summary.json`
- `outputs/phase3/.../dual_channel_activation_model.csv`
- `outputs/phase4/.../multishot_dual_channel_params.csv`

## Related Docs

- `docs/phases/phase0_data_and_calibration/dual-channel-activation-method.md`
- `docs/phases/phase0_data_and_calibration/laser-activation-literature-notes.md`
- `docs/modeling_tutorial_for_materials_undergrads.md`
- `docs/python_code_teaching_for_beginners.md`

