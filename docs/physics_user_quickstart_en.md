# Physics User Quickstart

This guide is for users who understand the physics of laser doping, but may not be familiar with the structure of a Python simulation project.

It answers three practical questions:

1. What does this project compute?
2. In what order should I run the scripts?
3. Which output files should I inspect after a run?

## 1. What this codebase does

The project currently splits the laser-doping problem into four layers:

1. Thermal model
   - The laser heats either bare `Si` or a `PSG/Si` stack
   - The model outputs the temperature field `T(z,t)` and liquid fraction `f_l(z,t)`
2. Diffusion model
   - The thermal history drives phosphorus diffusion in silicon
   - The model outputs the total phosphorus concentration profile `C_P(z,t)`
3. Electrical post-processing
   - The total phosphorus is separated into active / inactive / injected components
   - A sheet-resistance estimate `Rsh` is produced
4. Multi-shot extension
   - Repeated-pulse accumulation can be studied on top of the single-shot result

The central modeling chain is:

```text
laser input -> temperature field -> liquid fraction -> effective diffusivity -> phosphorus profile -> junction depth / Rsh
```

## 2. Before you run anything

### 2.1 Python environment

`Python 3.11+` is recommended.

Install dependencies with:

```powershell
pip install -r requirements.txt
```

### 2.2 The most important project locations

- [src/laser_doping_sim](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim)
  - Core solvers and physics modules
- [inputs](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/inputs)
  - Input files, measured profiles, empirical activation tables
- [outputs](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs)
  - Simulation outputs
- [run_phase1.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_phase1.py)
  - Single-layer thermal entry point
- [run_phase2.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_phase2.py)
  - Single-layer thermal + diffusion entry point
- [run_phase3.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_phase3.py)
  - Main `PSG/Si` thermal + diffusion entry point
- [run_phase3_power_scan.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_phase3_power_scan.py)
  - Power-scan entry point
- [run_sheet_resistance_cases.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_sheet_resistance_cases.py)
  - `Rsh` post-processing entry point

## 3. Recommended full test sequence

If this is your first time using the project, the recommended order is:

1. Run `Phase 1` first and confirm that the thermal model behaves sensibly
2. Run `Phase 2` next and confirm that single-layer diffusion behaves sensibly
3. Run `Phase 3` for the main `PSG/Si` workflow
4. Run a power scan if you want trends across laser power
5. Run `Rsh` post-processing if you want comparison against sheet-resistance measurements

The rest of this document follows that order.

## 4. Step 1: Run the single-layer thermal baseline

Command:

```powershell
python .\run_phase1.py
```

What this does physically:

- Treats the laser pulse as a time-varying volumetric heat source with exponential depth absorption
- Solves the 1D heat conduction equation
- Uses an apparent-heat-capacity formulation for phase change

Default output location:

- [outputs/phase1/default_run](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase1/default_run)

Files worth checking first:

- `summary.json`
- `surface_temperature_vs_time.png`
- `melt_depth_vs_time.png`
- `temperature_heatmap.png`
- `liquid_fraction_heatmap.png`

Quantities to inspect first:

1. Peak surface temperature
2. Whether melting occurs at all
3. Melt duration
4. Melt-depth scale

## 5. Step 2: Run thermal-history-driven diffusion

Command:

```powershell
python .\run_phase2.py
```

What this does physically:

- First runs `Phase 1` to obtain the thermal history
- Builds `D_eff(T, f_l)` from temperature and liquid fraction
- Solves the 1D phosphorus diffusion equation

Default output location:

- [outputs/phase2/default_run](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase2/default_run)

Files worth checking first:

- `summary.json`
- `final_p_profile.png`
- `junction_depth_vs_time.png`
- `source_inventory_vs_time.png`
- `p_concentration_heatmap.png`

Quantities to inspect first:

1. Final peak phosphorus concentration
2. Final and maximum junction depth
3. Whether the surface source is depleted too quickly
4. Whether the mass-balance error is acceptably small

## 6. Step 3: Run the full PSG/Si stacked model

Command:

```powershell
python .\run_phase3.py
```

This is the main workflow in the current project.

What it does physically:

1. Solves the coupled `PSG/Si` optical-thermal problem
2. Crops the thermal history down to the silicon subdomain
3. Re-runs phosphorus diffusion in silicon using that thermal history
4. Writes both thermal and diffusion outputs

Default output location:

- [outputs/phase3/default_run](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/default_run)

The default case contains two main subfolders:

- `thermal/`
- `diffusion/`

Files worth checking first:

- [summary.json](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/default_run/summary.json)
- [thermal/summary.json](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/default_run/thermal/summary.json)
- [diffusion/summary.json](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/default_run/diffusion/summary.json)

Why `Phase 3` matters:

- The `PSG` layer is included explicitly in the thermal model
- The measured `500 kHz`, `95 um` flat-top spot is converted into fluence through spot area
- The model includes `surface_reflectance`, `interface_transmission`, and separate absorption depths in the stack

## 7. Step 4: Run a power scan

If you care about thresholds and trends instead of a single case, run:

```powershell
python .\run_phase3_power_scan.py
```

This scans over a range of laser powers and repeats:

- `Phase 3 thermal`
- `Phase 2 diffusion`

Default output location:

- [outputs/phase3/power_scan_60_90w](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/power_scan_60_90w)

This is the most useful tool for answering questions such as:

- At what power does melting start?
- How does melt depth vary with power?
- How does junction depth vary with power?
- At what power does strong injection become important?

## 8. Step 5: Build a measured initial profile from ECV and SIMS

If you already have raw `ECV` and `SIMS` data, run:

```powershell
python .\prepare_measured_initial_profile.py
```

Default inputs:

- [inputs/raw_measurements/CTV-ECV-RAW.csv](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/inputs/raw_measurements/CTV-ECV-RAW.csv)
- [inputs/raw_measurements/CTV-SIMS-RAW.xlsx](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/inputs/raw_measurements/CTV-SIMS-RAW.xlsx)

Default outputs:

- [inputs/measured_profiles/ctv_measured_initial_profile.csv](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/inputs/measured_profiles/ctv_measured_initial_profile.csv)
- [inputs/measured_profiles/ctv_measured_initial_profile.png](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/inputs/measured_profiles/ctv_measured_initial_profile.png)

Then use that profile in `Phase 3` like this:

```powershell
python .\run_phase3.py `
  --initial-profile-kind measured `
  --initial-profile-csv inputs/measured_profiles/ctv_measured_initial_profile.csv
```

In that mode, the initial phosphorus profile is no longer an idealized `erfc emitter`; it comes directly from measured data.

## 9. Step 6: Estimate sheet resistance

After running one or more `Phase 3` cases, you can do `Rsh` post-processing.

Example:

```powershell
python .\run_sheet_resistance_cases.py `
  --case-dirs outputs/phase3/default_run `
  --output-dir outputs/phase3/sheet_resistance_default
```

This does not re-run the main thermal model. Instead, it:

1. Reads an existing case
2. Reconstructs active / inactive / injected contributions
3. Applies an activation assumption to obtain electrically active donors
4. Uses the Masetti mobility model to estimate `Rsh`

This step is useful for questions such as:

- How much of the total phosphorus should be treated as electrically active?
- Under a given activation assumption, what sheet resistance should I expect?

## 10. A recommended full workflow test

If you want one practical end-to-end test covering thermal response, diffusion, and `Rsh`, this is a good starting point.

### 10.1 Build the measured profile

```powershell
python .\prepare_measured_initial_profile.py
```

### 10.2 Run one measured-profile Phase 3 case

```powershell
python .\run_phase3.py `
  --output-dir outputs/phase3/tutorial_measured_case `
  --average-power-w 60 `
  --repetition-rate-hz 500000 `
  --square-side-um 95 `
  --pulse-fwhm-ns 10 `
  --surface-reflectance 0.09 `
  --interface-transmission 0.68 `
  --psg-absorption-depth-um 50 `
  --si-absorption-depth-nm 1274 `
  --initial-profile-kind measured `
  --initial-profile-csv inputs/measured_profiles/ctv_measured_initial_profile.csv `
  --boundary-model finite_source_cell `
  --source-exchange-mode all_states
```

### 10.3 Run `Rsh` post-processing

```powershell
python .\run_sheet_resistance_cases.py `
  --case-dirs outputs/phase3/tutorial_measured_case `
  --output-dir outputs/phase3/tutorial_measured_case_rsh `
  --inactive-activation-fraction 0.05 `
  --final-inactive-activation-fraction 0.05 `
  --injected-activation-fraction 1.0
```

### 10.4 What to read in the outputs

From the thermal output:

- Peak surface temperature
- Maximum liquid fraction
- Maximum melt depth
- Melt window

From the diffusion output:

- Final peak phosphorus concentration
- Final junction depth
- Cumulative injected dose
- Source depletion fraction

From the `Rsh` output:

- `Rsh init`
- `Rsh af`
- Whether the active / inactive / injected split looks physically reasonable

## 11. Common parameter directions

If the model never melts, check first:

- `average_power_w`
- `pulse_fwhm_ns`
- `surface_reflectance`
- `si_absorption_depth_nm`
- `fluence_j_cm2`

If it melts but the junction remains shallow, check first:

- `source_dopant_concentration_cm3`
- `source_effective_thickness_nm`
- `interfacial_transport_length_nm`
- `source_exchange_mode`
- `liquid_prefactor_cm2_s`

If total phosphorus is high but `Rsh` does not decrease, check first:

- `inactive_activation_fraction`
- `final_inactive_activation_fraction`
- `injected_activation_fraction`
- The measured-profile active / inactive split

## 12. Common mistakes for new users

1. Using the old single-layer `Phase 1` absorption parameters as if they were the formal `Phase 3 PSG/Si` optical parameters
2. Confusing total phosphorus with electrically active donor concentration
3. Treating `final_net_donor_upper_bound` as if it were the true active donor profile
4. Interpreting `Rsh` post-processing parameters as if the main diffusion PDE already solved electrical activation explicitly
5. Judging a run from plots alone before reading `summary.json`

## 13. What to read next

If you can already run the workflow, the next document to read is:

- [physics_parameter_manual_en.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/physics_parameter_manual_en.md)

That manual explains:

- What each parameter in `src` means
- Which physical quantity each parameter represents
- Why each parameter affects the result
- What usually happens when you increase or decrease each `run_*.py` parameter

in a more systematic way.
