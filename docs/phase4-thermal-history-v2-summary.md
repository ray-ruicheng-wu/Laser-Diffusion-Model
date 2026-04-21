# Phase 4 Thermal-History V2 Summary

## Purpose

Phase 4 V1 reused the same single-pulse thermal history for every shot and only carried forward the chemical state.

Phase 4 V2 adds pulse-to-pulse thermal history:

- each shot reruns the 1D PSG/Si stack thermal solve
- the final stack temperature field from shot `n` becomes the initial temperature field for shot `n+1`
- the chemical state and the remaining PSG source inventory are still carried forward shot-to-shot

This makes the multi-shot model closer to a real pulse train at fixed repetition rate.

## What Changed

### Thermal solver

File:

- `src/laser_doping_sim/phase3_stack_thermal.py`

Change:

- `run_stack_simulation(...)` now accepts `initial_temperature_profile_k`
- this allows a shot to start from a non-ambient stack temperature profile

### Phase 4 multi-shot

File:

- `src/laser_doping_sim/phase4_multishot.py`

Changes:

- `MultiShotParameters` now includes `thermal_history_mode`
- added `run_multishot_diffusion_with_thermal_history(...)`
- `MultiShotResult` now stores shot-by-shot thermal metrics:
  - initial silicon surface temperature
  - peak silicon surface temperature
  - cycle-end silicon surface temperature
  - max melt depth
  - max liquid fraction

### CLI

File:

- `run_phase4_multishot.py`

Changes:

- added `--thermal-history-mode`
  - `reuse_single_pulse`
  - `accumulate`
- added `--cycle-end-ns`
  - for `accumulate`, if omitted, the code uses one full pulse period from `repetition-rate-hz`
- added `--fast-output`
  - keeps the core `csv/json/npz` outputs and skips plots for long benchmark or calibration runs

## Current Interpretation

Recommended usage:

- use `reuse_single_pulse` when we want a fast chemistry-only multi-shot approximation
- use `accumulate` when we want real pulse-to-pulse thermal memory

Important note:

- `accumulate` is computationally much more expensive because each shot now runs a full thermal cycle
- `--fast-output` reduces output overhead, but it does not change the underlying thermal or chemistry solve

## Smoke-Test Status

The new mode was smoke-tested with a lightweight case:

- `60 W`
- `2 shots`
- `dt = 0.5 ns`
- `nz = 250`
- `500 kHz`
- full cycle end at `2000 ns`

Output:

- `outputs/phase4/tmp_multishot_accumulate_60w_2shots_smoke_fast`

Observed shot-to-shot thermal carryover:

- Shot 1 initial silicon surface temperature: `300.0 K`
- Shot 1 cycle-end silicon surface temperature: `328.17 K`
- Shot 2 initial silicon surface temperature: `328.17 K`

This confirms that pulse-to-pulse thermal memory is now being propagated correctly through the solver chain.

## Next Recommended Step

Run a production-style comparison at the same power:

- `reuse_single_pulse`
- `accumulate`

and compare:

- junction depth vs shot
- injected dose vs shot
- cycle-end temperature vs shot
- sheet resistance vs shot

This will tell us whether thermal accumulation is a small correction or a first-order effect under the current 500 kHz process conditions.
