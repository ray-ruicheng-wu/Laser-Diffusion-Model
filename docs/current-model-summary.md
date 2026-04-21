# Current Model Summary Index

This file is the short index for the current executable mainline.

## Current Mainline Status

- `Phase 3` is the current single-shot `PSG/Si` mainline.
- `Phase 4` is the current multi-shot extension.
- `run_phase4_multishot.py` now supports both:
  - `reuse_single_pulse`
  - `accumulate`
- long multi-shot runs can use `--fast-output` to keep the core `csv/json/npz` outputs while skipping plots
- the current thermal and diffusion kernels have already been CPU-optimized with vectorized tridiagonal assembly and LAPACK solves

## Main Entry Docs

- `docs/mainline-phase-map.md`
  - the best short map of what each phase does
- `docs/phases/README.md`
  - the visible phase-folder index inside the docs tree
- `docs/project_model_walkthrough_zh.md`
  - the main Chinese walkthrough
- `docs/project_model_walkthrough_en.md`
  - the main English walkthrough
- `docs/physics_user_quickstart_zh.md`
  - run order, outputs, and practical usage in Chinese
- `docs/physics_user_quickstart_en.md`
  - run order, outputs, and practical usage in English
- `docs/physics_parameter_manual_zh.md`
  - physics and CLI parameter reference in Chinese
- `docs/physics_parameter_manual_en.md`
  - physics and CLI parameter reference in English

## Phase Navigation

- `Phase 0`
  - `docs/phases/phase0_data_and_calibration/dual-channel-activation-method.md`
  - `docs/phases/phase0_data_and_calibration/laser-activation-literature-notes.md`
- `Phase 1`
  - `docs/phases/phase1_single_layer_thermal/phase1-analysis.md`
  - `docs/phases/phase1_single_layer_thermal/phase1-code-explained.md`
- `Phase 2`
  - `docs/phases/phase2_single_shot_diffusion/phase2-analysis.md`
  - `docs/phases/phase2_single_shot_diffusion/phase2-code-explained.md`
- `Phase 3`
  - `docs/phases/phase3_psg_si_single_shot_mainline/phase3-analysis.md`
  - `docs/phases/phase3_psg_si_single_shot_mainline/phase3-code-explained.md`
  - `docs/phases/phase3_psg_si_single_shot_mainline/phase3-physics-validation.md`
  - `docs/phases/phase3_psg_si_single_shot_mainline/phase3-physics-validation-work-report.md`
- `Phase 4`
  - `docs/phases/phase4_multishot_mainline/phase4-multishot-v1-summary.md`
  - `docs/phases/phase4_multishot_mainline/phase4-thermal-history-v2-summary.md`

## Calibration, References, and Logs

- `docs/phases/phase0_data_and_calibration/dual-channel-activation-method.md`
- `docs/phases/phase0_data_and_calibration/laser-activation-literature-notes.md`
- `docs/formula-reference-register.md`
- `docs/literature-usage-register.md`
- `docs/workspace-file-classification.md`
- `docs/session-log.md`
- `docs/archive/README.md`

