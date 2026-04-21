# Phase 2

## Title

Single-Shot Thermal-Driven Phosphorus Diffusion

## What This Phase Does

This phase takes the thermal history from Phase 1 and solves the total phosphorus transport problem in silicon.

It adds:

- effective diffusivity from temperature and liquid fraction
- finite source-exchange behavior
- source inventory bookkeeping
- junction-depth extraction

## Main Entry Script

- `run_phase2.py`

## Core Modules

- `src/laser_doping_sim/phase2_diffusion.py`
- `src/laser_doping_sim/phase1_thermal.py`

## Main Outputs

- `outputs/phase2/default_run/final_p_profile.png`
- `outputs/phase2/default_run/junction_depth_vs_time.png`
- `outputs/phase2/default_run/source_inventory_vs_time.png`
- `outputs/phase2/default_run/p_concentration_heatmap.png`

## Related Docs

- `docs/phases/phase2_single_shot_diffusion/phase2-analysis.md`
- `docs/phases/phase2_single_shot_diffusion/phase2-code-explained.md`
- `docs/phases/phase2_single_shot_diffusion/boundary-condition-review.md`
- `docs/phases/phase2_single_shot_diffusion/interface-model-literature-notes.md`

