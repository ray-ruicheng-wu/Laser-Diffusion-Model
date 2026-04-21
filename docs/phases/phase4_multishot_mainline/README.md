# Phase 4

## Title

Multi-Shot Thermal-History And Multi-Shot Electrical Extension

## What This Phase Does

This phase extends the single-shot mainline into repeated laser shots.

The current mainline supports:

- `reuse_single_pulse`
- `accumulate`

This phase also includes:

- shot-to-shot chemistry inheritance
- source inventory inheritance
- multi-shot activation bootstrap
- multi-shot sheet-resistance post-processing

## Main Entry Scripts

- `run_phase4_multishot.py`
- `run_single_cycle_cooling_check.py`
- `run_build_multishot_activation_bootstrap.py`
- `run_phase4_multishot_sheet_resistance.py`

## Core Modules

- `src/laser_doping_sim/phase4_multishot.py`
- `src/laser_doping_sim/phase3_stack_thermal.py`
- `src/laser_doping_sim/activation_models.py`
- `src/laser_doping_sim/sheet_resistance.py`

## Main Outputs

- `outputs/phase4/.../multishot/`
- `outputs/phase4/.../thermal/`
- `outputs/phase4/.../thermal_last_shot/`
- `outputs/phase4/.../multishot_rsh/`

## Related Docs

- `docs/phases/phase4_multishot_mainline/phase4-multishot-v1-summary.md`
- `docs/phases/phase4_multishot_mainline/phase4-thermal-history-v2-summary.md`

