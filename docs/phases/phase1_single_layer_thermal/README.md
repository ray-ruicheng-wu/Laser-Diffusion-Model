# Phase 1

## Title

Single-Layer Si Thermal Baseline

## What This Phase Does

This phase solves the depth-only transient thermal problem for silicon under laser heating.

It is the first thermal baseline for:

- surface temperature
- liquid fraction
- melt window
- melt depth

No phosphorus diffusion is solved here.

## Main Entry Script

- `run_phase1.py`

## Core Module

- `src/laser_doping_sim/phase1_thermal.py`

## Main Outputs

- `outputs/phase1/default_run/summary.json`
- `outputs/phase1/default_run/temperature_heatmap.png`
- `outputs/phase1/default_run/liquid_fraction_heatmap.png`
- `outputs/phase1/default_run/melt_depth_vs_time.png`

## Related Docs

- `docs/phases/phase1_single_layer_thermal/phase1-analysis.md`
- `docs/phases/phase1_single_layer_thermal/phase1-code-explained.md`

