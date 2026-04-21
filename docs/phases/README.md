# Phase Folders

This directory is the non-destructive phase-based workspace map for the current `main` branch.

The root scripts and modules remain in their existing locations so that current commands do not break.
These folders are here to make the project easier to navigate phase by phase.

## Phase Folders

- `phase0_data_and_calibration`
  measured inputs and electrical calibration preparation
- `phase1_single_layer_thermal`
  single-layer Si thermal baseline
- `phase2_single_shot_diffusion`
  single-shot phosphorus diffusion on top of the thermal history
- `phase3_psg_si_single_shot_mainline`
  `PSG/Si` single-shot mainline and experiment comparison
- `phase4_multishot_mainline`
  multi-shot thermal-history and multi-shot electrical extension

## Suggested Use

1. Open the phase folder you care about first
2. Read its `README.md`
3. Then jump to the linked root scripts, core modules, outputs, and docs

For the full narrative map, also read:

- `docs/mainline-phase-map.md`

## What Is Inside Each Phase Folder

- `phase0_data_and_calibration`
  - measured-profile preparation and activation-calibration docs
- `phase1_single_layer_thermal`
  - Phase 1 analysis and code explanation
- `phase2_single_shot_diffusion`
  - Phase 2 analysis, code explanation, and interface / boundary-condition notes
- `phase3_psg_si_single_shot_mainline`
  - Phase 3 mainline analysis, physics validation, work reports, and scan / paper reports
- `phase4_multishot_mainline`
  - Phase 4 multi-shot and thermal-history summaries
