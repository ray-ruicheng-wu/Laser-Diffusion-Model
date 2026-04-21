---
tags:
  - laser-doping
  - psg
  - phosphorus
  - silicon
  - modeling
  - tutorial
  - english
---

# Laser PSG Phosphorus Doping Project Walkthrough (English)

## 1. Purpose of This Document

This document merges the old `project_total_walkthrough_obsidian` and `current-model-summary` into one unified project walkthrough.

It serves two roles:

- the main technical overview of the current modeling workflow
- the primary onboarding document for future development

It answers five questions:

1. What exactly are we modeling?
2. How was the model built step by step?
3. Which governing equations are used, and why?
4. How is the code organized?
5. What are the current results, limitations, and next steps?

## 2. One-Sentence Summary of the Current Model

The current workflow can be summarized as a **1D, measurement-driven laser phosphorus redistribution / injection mainline**:

- the single-shot baseline is centered on the `Phase 3` `PSG/Si` workflow
- the multi-shot extension is carried by the `Phase 4` shot-to-shot model

Its physical chain is:

`laser -> heating -> phase change -> phosphorus transport -> profile / junction / sheet dose`

On top of that physical core, we add an **empirical electrical activation layer** so that the simulated phosphorus profile can be converted into sheet resistance `Rsh` and compared directly with experiment.

## 3. What Process We Are Modeling

The target process is:

- `532 nm` laser irradiation
- `PSG` as the surface phosphorus source
- a pre-existing phosphorus profile before laser processing
- post-laser phosphorus redistribution and, at higher energy, additional phosphorus injection

Current main assumptions:

- single-pulse equivalent excitation
- `1D` depth-only geometry
- `PSG` approximated first as a phosphorus-rich `SiO2`-like layer
- measured front-surface reflectance fixed at `9%`
- initial profile driven directly by `SIMS + ECV`

## 4. How the Model Was Built Step by Step

### 4.1 Phase 1: Build the Thermal History First

The first step was purely thermal.

The reason is fundamental: laser doping is not “diffusion first.” It is “energy absorption, rapid heating, possible melting, then much faster transport.” If the thermal history is wrong, everything downstream becomes questionable.

The governing equation is:

\[
\rho c_{\mathrm{eff}}(T)\frac{\partial T}{\partial t}
=
\frac{\partial}{\partial z}\left(k(T)\frac{\partial T}{\partial z}\right)
+ Q_{\mathrm{laser}}(z,t)
\]

where:

- `rho` is density
- `c_eff(T)` is the effective heat capacity including latent heat
- `k(T)` is thermal conductivity
- `Q_laser(z,t)` is the laser heat source

Main outputs of this stage:

- peak surface temperature
- liquid fraction
- melt depth
- melt time window

Main code:

- `src/laser_doping_sim/phase1_thermal.py`
- `run_phase1.py`

### 4.2 Phase 2: Add Total Phosphorus Transport on Top of the Thermal Field

Once the temperature history exists, phosphorus transport is added.

The diffusion equation currently solves for total phosphorus concentration:

\[
\frac{\partial C}{\partial t}
=
\frac{\partial}{\partial z}
\left(
D_{\mathrm{eff}}(T,f_l)\frac{\partial C}{\partial z}
\right)
\]

with the effective diffusivity written as:

\[
D_{\mathrm{eff}}(T,f_l)=(1-f_l)D_s(T)+f_lD_l(T)
\]

where:

- `D_s(T)` is the solid-state phosphorus diffusivity in silicon
- `D_l(T)` is the liquid-state phosphorus diffusivity
- `f_l` is liquid fraction

Why this form was chosen:

- it keeps solid-state diffusion available under non-melting conditions
- it captures the strong increase in transport near or above melting
- it is numerically stable for threshold-region studies

The surface boundary is not a fixed surface concentration. Instead, the current model uses a finite source-cell exchange model. Under the current mainline settings, significant `PSG -> Si` injection is primarily enabled in the melt window.

Main code:

- `src/laser_doping_sim/phase2_diffusion.py`
- `run_phase2.py`

### 4.3 Phase 3: Add PSG and Real Process Conditions

The third step brings the actual process conditions into the model:

- `PSG` as the surface source
- `532 nm`
- square flat-top spot
- measured `9%` surface reflectance
- measured initial profile

Current PSG treatment:

- chemically interpreted as `P2O5-SiO2` glass
- thermally and optically approximated first as a phosphorus-rich `SiO2`-like layer
- laser absorption still handled with a Beer-Lambert-style source in the first implementation

Main code:

- `src/laser_doping_sim/phase3_stack_thermal.py`
- `run_phase3.py`
- `run_phase3_power_scan.py`

### 4.4 Initial Conditions Upgraded from Assumed Profiles to Measured Profiles

Early in the project, parameterized profiles were useful for demonstration. The current mainline no longer relies on that as the authoritative input.

The current measured-profile definitions are:

\[
P_{\mathrm{total,init}}(z)=P_{\mathrm{SIMS}}(z)
\]

\[
P_{\mathrm{active,init}}(z)=P_{\mathrm{ECV}}(z)
\]

\[
P_{\mathrm{inactive,init}}(z)=\max(P_{\mathrm{SIMS}}(z)-P_{\mathrm{ECV}}(z),0)
\]

This separation matters because:

- `SIMS` provides the chemical total
- `ECV` provides the electrically active part
- their difference provides the initial inactive phosphorus inventory

Current processed measured-profile files:

- `inputs/measured_profiles/ctv_measured_initial_profile.csv`
- `inputs/measured_profiles/ctv_measured_initial_profile_summary.json`

Current surface values are approximately:

- `surface total P = 4.59e21 cm^-3`
- `surface active P = 7.30e20 cm^-3`
- `surface inactive P = 3.86e21 cm^-3`

## 5. Why We Still Need an Empirical Electrical Layer

The thermal and diffusion models produce total phosphorus concentration, but the experiment reports electrical sheet resistance.

So the `Rsh` workflow has two parts:

### 5.1 Convert Concentration into Conductivity

\[
\sigma(z)=q\mu_n(z)n(z)
\]

\[
R_{\mathrm{sh}}=\frac{1}{\int \sigma(z)\,dz}
\]

The mobility model currently used is:

- `Masetti @ 300 K`

Main code:

- `src/laser_doping_sim/sheet_resistance.py`

### 5.2 Decide Which Phosphorus Counts as Electrically Active

This is the least first-principles part of the current workflow.

The current mainline uses a **segmented empirical non-active pool activation model**.

For the initial state:

\[
N_{D,\mathrm{act,init}}
=
N_{D,\mathrm{active,init}}
+ f_{\mathrm{init}}N_{D,\mathrm{inactive,init}}
\]

Current calibrated value:

- `f_init = 0.06447924522684517`

For the post-laser state:

\[
N_{D,\mathrm{pool,final}}
=
N_{D,\mathrm{inactive,final}}
+ N_{D,\mathrm{injected,final}}
\]

\[
N_{D,\mathrm{act,final}}
=
N_{D,\mathrm{active,final}}
+ f_{\mathrm{pool}}(P_{\mathrm{laser}})\,N_{D,\mathrm{pool,final}}
\]

So the current workflow merges the post-laser “not obviously active” part into one `non-active pool`, then assigns a power-dependent activation fraction fitted from experimental `Rsh` data.

Parameter table:

- `inputs/activation_models/segmented_nonactive_pool_empirical_24_60w.csv`

Main code:

- `src/laser_doping_sim/activation_models.py`
- `run_sheet_resistance_cases.py`

This layer must be read as:

- an **empirical electrical calibration layer**

not as:

- a complete first-principles activation model

The latest update extends this into a **dual-channel activation bookkeeping model**:

\[
N_{D,\mathrm{act,final}}
=
N_{D,\mathrm{active,component}}
+ \eta_{\mathrm{inactive}}(P)\,N_{D,\mathrm{inactive,component}}
+ \eta_{\mathrm{inj}}(P)\,N_{D,\mathrm{inj,component}}
\]

This separates:

- re-activation of initially inactive phosphorus
- electrical activation of phosphorus injected from `PSG`

The implementation and method notes are now in:

- `run_dual_channel_activation_calibration.py`
- `docs/phases/phase0_data_and_calibration/dual-channel-activation-method.md`

The current modeling conclusion is:

- `24–48 W` can be explained mainly by `initial inactive re-activation`
- but directly carrying that low-power `eta_inactive(P)` curve into `54/60 W` predicts an `Rsh` that is too low
- which means the high-power regime has already entered a different electrical closure

## 6. Current Mainline Parameters

Important current measured-mainline parameters:

- wavelength: `532 nm`
- repetition rate: `500 kHz`
- spot: `95 um` square flat-top
- reflectance: `9%`
- `PSG` phosphorus concentration: set equal to measured surface `SIMS`, i.e. `4.5913166904198945e21 cm^-3`
- background doping: `Ga = 1e16 cm^-3`
- `PSG` thickness: `150 nm`
- `source effective thickness`: `100 nm`
- `interfacial transport length`: `100 nm`

## 7. Current Results

### 7.1 Main Thermal / Diffusion Results

Current mainline scan directory:

- `outputs/phase3/power_scan_24_60w_step6_measured_ctv_psg_eq_sims`

Representative points:

#### 24 W

- peak silicon surface temperature: `1151.08 K`
- `max_liquid_fraction = 0`
- melt depth: `0 nm`
- injected dose: `0`
- junction depth: `372.79 nm`

#### 30 W

- peak silicon surface temperature: `1363.85 K`
- `max_liquid_fraction = 0`
- melt depth: `0 nm`
- injected dose: `0`
- junction depth: `372.79 nm`

#### 54 W

- peak silicon surface temperature: `1682.31 K`
- `max_liquid_fraction = 0.502`
- maximum melt depth: `81.11 nm`
- injected dose: `3.01e14 cm^-2`

#### 60 W

- peak silicon surface temperature: `2043.52 K`
- `max_liquid_fraction = 1.0`
- maximum melt depth: `611.30 nm`
- injected dose: `1.06e16 cm^-2`
- junction depth: `448.27 nm`

Interpretation:

- `24–48 W` is still mostly non-melting or threshold-adjacent
- `54 W` enters a partial melt / injection transition regime
- `60 W` clearly enters strong melting and significant injection

### 7.2 Main Sheet-Resistance Results

Current sheet-resistance comparison directory:

- `outputs/phase3/sheet_resistance_segmented_nonactive_pool_anchor_24_60w`

Current reproduced trend:

- `24 W`: `169.89 -> 163.13 ohm/sq`
- `27 W`: `169.89 -> 150.38`
- `30 W`: `169.89 -> 144.95`
- `33 W`: `169.89 -> 117.588`
- `36 W`: `169.89 -> 105`
- `42 W`: `169.89 -> 99`
- `48 W`: `169.89 -> 89`
- `54 W`: `169.89 -> 82`
- `60 W`: `169.89 -> 69`

This means:

- the measured initial profile plus the empirical activation layer can now reproduce the experimental `Rsh` trend reasonably well
- but the `Rsh` result is still a combination of physical transport plus empirical electrical closure

## 8. What Parts of the Model Are Most Reliable Right Now

The most reliable parts at this stage are:

- the measured `SIMS + ECV` driven initial profile
- the relative thermal and melt-depth trends from the 1D model
- the total phosphorus redistribution and injection trends
- the experimental trend matching through `Rsh` post-processing

This means the current workflow is already useful for:

- power sweeps
- before/after `P profile` comparison
- junction-depth trend analysis
- sheet-resistance trend comparison

## 9. Main Limitations

### 9.1 The activation layer is still mostly empirical

The workflow now separates:

- re-activation of pre-existing inactive phosphorus
- activation of newly injected phosphorus

at the bookkeeping level, but the high-power physical closure is still not final.

More precisely:

- the low-power `eta_inactive(P)` curve can already be calibrated empirically
- the high-power `eta_inj(P)` channel still cannot be uniquely identified from the current `Rsh` data alone
- so the dual-channel model should still be read as an electrical calibration layer, not as a fully adopted first-principles activation law

### 9.2 The model is still 1D

The current workflow does not explicitly resolve:

- lateral spot-shape effects
- pyramid sidewalls and valleys
- local texture-driven optical concentration

### 9.3 The `PSG/SiO2/Si` interface is not yet fully explicit

The current PSG treatment is much more realistic than the earliest versions, but it still does not explicitly solve a separate ultrathin interfacial `SiO2` transport barrier.

## 10. Recommended Reading Order for the Code

If someone wants to understand the implementation, the recommended order is:

1. `run_phase3.py`
2. `src/laser_doping_sim/phase3_stack_thermal.py`
3. `src/laser_doping_sim/phase2_diffusion.py`
4. `src/laser_doping_sim/measured_profiles.py`
5. `src/laser_doping_sim/sheet_resistance.py`
6. `src/laser_doping_sim/activation_models.py`
7. `run_phase3_power_scan.py`
8. `run_sheet_resistance_cases.py`

The reason is simple:

- start from the main entry point
- then understand thermal physics
- then diffusion
- then measured-input handling and electrical post-processing

## 11. Which Supporting Documents Matter Most

### Formula and literature tracking

- `docs/formula-reference-register.md`
- `docs/literature-usage-register.md`
- `docs/phases/phase0_data_and_calibration/laser-activation-literature-notes.md`

### Stage-specific analysis

- `docs/phases/phase1_single_layer_thermal/phase1-analysis.md`
- `docs/phases/phase2_single_shot_diffusion/phase2-analysis.md`
- `docs/phases/phase3_psg_si_single_shot_mainline/phase3-analysis.md`
- `docs/phases/phase3_psg_si_single_shot_mainline/phase3-physics-validation.md`

### Teaching-oriented documents

- `docs/modeling_tutorial_for_materials_undergrads.md`
- `docs/python_code_teaching_for_beginners.md`

### Workspace map

- `docs/workspace-file-classification.md`

## 12. Best Next Steps

The most valuable next upgrades are:

1. build a dedicated high-power activation closure for `54W+` instead of reusing the low-power `eta_inactive(P)` rule
2. strengthen the constraints on both `initial inactive re-activation` and `injected P activation` in the high-power regime
3. make texture enhancement an explicit geometric / effective-optical model
4. further refine the `PSG/SiO2/Si` interface

## 13. Final One-Line Conclusion

The main value of the current model is not that it already predicts every part of the process from first principles. The main value is that it already connects:

- thermal history
- phase change
- total phosphorus transport
- measured initial conditions
- sheet-resistance comparison

into one stable workflow that is ready for the next round of physics upgrades.

