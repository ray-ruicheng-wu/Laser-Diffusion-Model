# Phase 4 Multi-Shot V1 Summary

## Goal

Phase 4 Multi-Shot V1 is the first pulse-to-pulse extension of the current PSG/Si laser-doping model.

Its purpose is not to solve the full pulse-train thermal problem yet. Instead, it answers a narrower and more useful first question:

- if each pulse sees roughly the same single-pulse thermal history,
- but the silicon chemistry and PSG source inventory are inherited from the previous pulse,
- what redistribution trend do we predict shot by shot?

This matches the recent single-cycle cooling check, which showed that at `500 kHz` the modeled `2000 ns` cycle-end residual heating is only on the order of `10-40 K` for the scout range, and about `18 K` for the fine-step `60 W` confirmation.

Current documentation positioning:

- read this file for the chemistry-inheritance-only multi-shot path
- read `phase4-thermal-history-v2-summary.md` for the shot-to-shot thermal-memory path
- for long benchmark or calibration scans, `run_phase4_multishot.py --fast-output` is now the preferred output mode

## Main Assumptions

Phase 4 V1 keeps these assumptions:

- `1D` depth-direction model
- same single-pulse thermal history reused for every shot
- no explicit interpulse thermal accumulation
- same local PSG source cell depletes shot to shot by default
- phosphorus origin is tracked in three pools:
  - initial active-origin P
  - initial inactive-origin P
  - PSG injected-origin P

## Implementation

New main files:

- `src/laser_doping_sim/phase4_multishot.py`
- `run_phase4_multishot.py`

Supporting extension:

- `src/laser_doping_sim/phase2_diffusion.py`

Operational note:

- `run_phase4_multishot.py` now also supports `--fast-output`
- this does not change the modeled chemistry
- it only skips plot generation and uses faster `npz` writing for long runs

The key Phase 2 upgrade is that the diffusion kernel can now accept an inherited state:

- `initial_active_p_cm3`
- `initial_inactive_p_cm3`
- `initial_injected_p_cm3`
- `initial_source_inventory_atoms_m2`

This makes it possible to chain shots without rebuilding the initial condition from scratch every time.

## How One Shot Is Updated

For each shot:

1. reuse the same single-pulse thermal field `T(z,t)` and `f_l(z,t)`
2. solve the total phosphorus profile with the existing finite-source boundary model
3. solve active-origin and inactive-origin redistribution with zero external boundary flux
4. define injected-origin phosphorus as:

`C_inj = C_total - C_active_origin - C_inactive_origin`

5. pass the final three-component state and the remaining source inventory to the next shot

This preserves the current single-pulse total solution while preventing artificial transfer of pre-existing silicon phosphorus into the injected-origin pool.

## Current Validation

Smoke-test run:

- `outputs/phase4/multishot_v1_smoke_60w_3shots_balanced`

Current checks that pass:

- component sheet-dose balance closes to numerical precision
- injected-origin sheet dose matches cumulative source depletion to numerical precision
- shot-by-shot junction depth grows smoothly in the smoke test
- remaining source inventory decreases monotonically when `source_replenishment_mode = carry`

For the `60 W`, `3-shot` smoke test:

- Shot 1 cumulative injected dose: about `1.08e14 cm^-2`
- Shot 2 cumulative injected dose: about `2.86e14 cm^-2`
- Shot 3 cumulative injected dose: about `4.86e14 cm^-2`
- Shot 3 final junction depth: about `382.8 nm`

## Multi-Shot Activation Bootstrap

New supporting files:

- `run_build_multishot_activation_bootstrap.py`
- `run_phase4_multishot_sheet_resistance.py`

New parameter-table format:

- `power_w`
- `eta_inactive_shot1`
- `eta_inactive_inf`
- `n0_inactive_shots`
- `eta_injected_shot1`
- `eta_injected_inf`
- `qref_injected_cm2`
- `q0_injected_cm2`

Interpretation:

- `eta_inactive_shot1` and `eta_injected_shot1` are inherited from the old single-shot table
- `eta_inactive_inf` is the large-shot-count saturation value for initial inactive re-activation
- `n0_inactive_shots` is the characteristic shot count for that saturation
- `qref_injected_cm2` is the single-shot injected-dose reference point
- `q0_injected_cm2` is the injected-dose scale that controls how quickly the injected-P activation approaches saturation

Current bootstrap output:

- `outputs/phase4/multishot_activation_bootstrap_trial/multishot_dual_channel_params.csv`

Current trial Rsh application:

- `outputs/phase4/multishot_v1_smoke_60w_3shots_balanced/multishot_rsh_bootstrap_trial`

For the current `60 W`, `3-shot` smoke test with the bootstrap table:

- `Rsh init ≈ 169.89 ohm/sq`
- Shot 1 `Rsh ≈ 69.00 ohm/sq`
- Shot 2 `Rsh ≈ 61.52 ohm/sq`
- Shot 3 `Rsh ≈ 55.94 ohm/sq`

This bootstrap table is intentionally a new table and does not modify the old single-shot activation CSV or the old Phase 3 Rsh pipeline.

## What V1 Can And Cannot Mean

V1 is already useful for:

- repeated redistribution trend checks
- source depletion trend checks
- seeing whether repeated shots broaden the phosphorus profile even without explicit heat accumulation

V1 is not yet a full pulse-train model because it does not include:

- residual temperature carried into the next pulse
- temperature-dependent activation history across multiple pulses
- pulse-to-pulse optical changes
- moving-interface segregation / trapping during repeated remelting

So the current interpretation is:

- use V1 when the main question is chemistry inheritance and source depletion
- use the Phase 4 thermal-history V2 path when explicit pulse-to-pulse heat carry-over matters

## Recommended Next Step

The most stable next step is not full thermal accumulation yet.

It is:

- use this V1 model to scan `shot_count`
- compare predicted chemical redistribution against measured trend
- then decide whether the activation model should be upgraded to depend on:
  - `power`
  - `shot_count`
  - cumulative injected dose
  - cumulative liquid-time proxy

If later measured data shows stronger shot-count sensitivity than V1 can explain, then upgrade to a Phase 4 V2 with explicit interpulse thermal carry-over.
