# Phase 3

## Title

PSG/Si Single-Shot Mainline And Experiment Comparison

## What This Phase Does

This is the main single-shot workflow in the current project.

It upgrades the model to:

- a `PSG/Si` stack thermal solve
- measured initial phosphorus profiles
- single-shot power scans
- physics validation
- single-shot sheet-resistance comparison

## Main Entry Scripts

- `run_phase3.py`
- `run_phase3_power_scan.py`
- `run_phase3_physics_validation.py`
- `run_sheet_resistance_cases.py`

## Core Modules

- `src/laser_doping_sim/phase3_stack_thermal.py`
- `src/laser_doping_sim/phase2_diffusion.py`
- `src/laser_doping_sim/measured_profiles.py`
- `src/laser_doping_sim/activation_models.py`
- `src/laser_doping_sim/sheet_resistance.py`

## Main Inputs

- `inputs/measured_profiles/ctv_measured_initial_profile.csv`
- `inputs/activation_models/measured_rsh_24_60w.csv`

## Main Outputs

- `outputs/phase3/default_run/thermal/`
- `outputs/phase3/default_run/diffusion/`
- `outputs/phase3/power_scan_.../`
- `outputs/phase3/sheet_resistance_.../`
- `outputs/phase3/dual_channel_activation_.../`

## Related Docs

- `docs/phases/phase3_psg_si_single_shot_mainline/phase3-analysis.md`
- `docs/phases/phase3_psg_si_single_shot_mainline/phase3-code-explained.md`
- `docs/phases/phase3_psg_si_single_shot_mainline/phase3-physics-validation.md`
- `docs/phases/phase3_psg_si_single_shot_mainline/phase3-physics-validation-work-report.md`
- `docs/phases/phase3_psg_si_single_shot_mainline/phase3-work-report.md`
- `docs/phases/phase3_psg_si_single_shot_mainline/literature-gap-analysis.md`
- `docs/phases/phase3_psg_si_single_shot_mainline/power-scan-60-90w-report.md`
- `docs/phases/phase3_psg_si_single_shot_mainline/reproducible-paper-report-90w.md`
- `docs/phases/phase0_data_and_calibration/dual-channel-activation-method.md`

