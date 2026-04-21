# Current Model Summary Index

This file now acts as the short index for the unified current-model walkthrough.

## Unified Walkthroughs

- 中文主文档：
  [project_model_walkthrough_zh.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/project_model_walkthrough_zh.md)
- English master document:
  [project_model_walkthrough_en.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/project_model_walkthrough_en.md)

## Scope

The merged walkthrough now includes both:

- the step-by-step model-building story
- the current mainline model status, assumptions, and results

## Current Executable Mainline

Important note:

- the current executable `run_phase4_multishot.py` in this workspace is still the Phase 4 V1 path
- it reuses one single-pulse thermal history for all shots
- it does not currently expose the earlier experimental `thermal_history_mode=accumulate` CLI entry in the main runnable path

This means:

- some historical outputs and tutorial text may refer to an `accumulate`-style thermal-history model
- but the current checked-in mainline runner should be treated as V1 unless and until the accumulated path is re-merged

## Supporting References

- [workspace-file-classification.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/workspace-file-classification.md)
- [phase3-analysis.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/phase3-analysis.md)
- [phase4-multishot-v1-summary.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/phase4-multishot-v1-summary.md)
- [formula-reference-register.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/formula-reference-register.md)
- [session-log.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/session-log.md)
