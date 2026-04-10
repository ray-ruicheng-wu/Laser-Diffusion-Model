# Phase 3 Physics Validation

## Scope

This validation checks whether the current Phase 3 power-scan results obey basic physical and logical trends before adding texture enhancement.

- Main scan: [power_scan_60_90w_dt01](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/power_scan_60_90w_dt01)
- Fine time-step cross-check: [power_scan_60_65w_dt005](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/power_scan_60_65w_dt005)
- Validation outputs: [physics_validation_60_90w](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/physics_validation_60_90w)
- Main report: [physics_validation_report.md](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/physics_validation_60_90w/physics_validation_report.md)

## Verdict

The current model passes a basic trend-level physics validation with one explicit caveat:

1. The `60W -> 65W` segment in the official `dt = 0.1 ns` scan is threshold-sensitive and should not be over-interpreted.
2. The finer `dt = 0.05 ns` cross-check restores monotonic behavior in that low-power region.
3. The broader `70-90W` trends are physically self-consistent.

## What Passed

The following trends are consistent with a power scan:

1. Fluence increases monotonically with power.
2. Peak stack-surface temperature increases monotonically.
3. Peak silicon-surface temperature is monotonic within the configured tolerance.
4. Maximum liquid fraction increases monotonically.
5. Maximum melt depth is nondecreasing.
6. Junction depth is nondecreasing.
7. Mass balance error remains at floating-point-noise scale.

Relevant files:

- [physics_validation_summary.json](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/physics_validation_60_90w/physics_validation_summary.json)
- [physics_validation_table.csv](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/physics_validation_60_90w/physics_validation_table.csv)

## What Needed Interpretation

Two low-power metrics in the coarse scan show a local inversion between `60W` and `65W`:

1. `final chemical net donor sheet dose`
2. `final source inventory`

These are not treated as final physical reversals because the finer `dt = 0.05 ns` cross-check removes that inversion.

## Why Peak P Can Drop While Dose And Junction Rise

`final_peak_p_concentration_cm3` is the maximum of the final profile, not the total amount of phosphorus in silicon.

In the current scan:

1. `peak P` is nonmonotonic.
2. `junction depth` rises from about `302 nm` to `371 nm`.
3. `net donor sheet dose` rises from about `3.58e15 cm^-2` to `6.30e15 cm^-2`.
4. `P(30 nm)`, `P(100 nm)`, `P(300 nm)`, and the near-surface profile center-of-mass all move upward from `70W` onward.

That combination is consistent with profile broadening and deeper redistribution, not with a loss of incorporated dopant.

Relevant plots:

- [power_vs_p_selected_depths.png](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/physics_validation_60_90w/power_vs_p_selected_depths.png)
- [power_vs_near_surface_dose.png](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/physics_validation_60_90w/power_vs_near_surface_dose.png)
- [power_vs_near_surface_profile_com.png](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/physics_validation_60_90w/power_vs_near_surface_profile_com.png)

## Review-Line Conclusion

Review line conclusion: pass with annotation.

The current scan is acceptable as the working baseline, but the `60-65W` region should be flagged as time-step sensitive near the melt threshold.

## Research-Line Conclusion

Research line conclusion: basically credible.

Literature-level interpretation supports the idea that:

1. Near-threshold behavior is highly sensitive to small thermal-budget changes.
2. Nonmonotonic `peak P` can coexist with rising dose and junction depth when the profile broadens.
3. The remaining model risk is not the broad trend itself, but the current threshold-gating definition around `melt_only`.

## Next Step

The next model-development step should be texture enhancement, built on this validated baseline.

The safest first texture terms are:

1. effective optical enhancement through lower escape reflectance / higher absorbed fraction
2. increased PSG/Si interface area per projected wafer area

The model should not begin by applying a large melting-point reduction.
