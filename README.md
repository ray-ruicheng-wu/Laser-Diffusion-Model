# Laser Silicon Doping Simulation

This workspace now includes the Phase 1 thermal model and the corrected Phase 2/3 phosphorus diffusion model for laser-induced silicon doping.

## What is implemented

- 1D transient heat conduction in depth
- Gaussian laser pulse with Beer-Lambert absorption
- Apparent heat capacity / enthalpy-style phase change treatment
- Melt-depth extraction over time
- Basic plots for temperature, liquid fraction, melt depth, and surface temperature
- PSG/P surface source metadata recorded in the outputs for Phase 2
- A literature-aligned finite source-cell boundary option for precursor-driven laser doping

## Run

```powershell
python .\run_phase1.py
```

```powershell
python .\run_phase2.py
```

```powershell
python .\run_phase3.py
```

Default outputs are written to:

- `outputs/phase1/default_run/`
- `outputs/phase2/default_run/`
- `outputs/phase3/default_run/`

Documentation lives in:

- `docs/project_model_walkthrough_zh.md`
- `docs/project_model_walkthrough_en.md`
- `docs/current-model-summary.md`
- `docs/physics_user_quickstart_zh.md`
- `docs/physics_user_quickstart_en.md`
- `docs/physics_parameter_manual_zh.md`
- `docs/physics_parameter_manual_en.md`
- `docs/workspace-file-classification.md`
- `docs/phase1-code-explained.md`
- `docs/phase1-analysis.md`
- `docs/phase2-code-explained.md`
- `docs/phase2-analysis.md`
- `docs/phase3-code-explained.md`
- `docs/phase3-analysis.md`
- `docs/dual-channel-activation-method.md`
- `docs/formula-reference-register.md`
- `docs/reproducible-paper-report-90w.md`

Raw measured inputs and cached references now live in:

- `inputs/raw_measurements/`
- `docs/references/`

## Useful parameter overrides

```powershell
python .\run_phase1.py --fluence-j-cm2 0.70 --pulse-fwhm-ns 15 --t-end-ns 120
```

```powershell
python .\run_phase1.py `
  --source-dopant-concentration-cm3 2.0e21 `
  --substrate-dopant Ga `
  --substrate-dopant-concentration-cm3 1.0e16
```

```powershell
python .\run_phase2.py `
  --source-dopant-concentration-cm3 2.0e21 `
  --substrate-dopant-concentration-cm3 1.0e16 `
  --source-effective-thickness-nm 100 `
  --interfacial-transport-length-nm 100
```

## Current modeling assumptions

- Depth-only model, no lateral heat spreading yet
- No surface evaporation, recoil pressure, or liquid flow
- Phase 1 is thermal only; Phase 2 adds one-way P diffusion on top of the thermal history
- Phase 2/3 now default to a finite source-cell boundary with all-state interfacial source exchange, while keeping the `melt_only` gate and the older Robin-reservoir option available for comparison
- Phase 2 now enforces source/silicon mass conservation through total inventory bookkeeping
- Phase 2/3 now keep a solid-state P diffusion path active for the pre-existing emitter under non-melting conditions
- PSG is still treated as a finite reservoir approximation rather than an explicit glass layer
- In Phase 3, PSG is interpreted as phosphosilicate glass (`P2O5-SiO2`) and approximated as a phosphorus-rich `SiO2` layer with silica-like thermal properties
- PSG `P` concentration and Si substrate `Ga` concentration are already coupled into Phase 2, but not yet back-coupled into the thermal solve
- Phase 3 now defaults to a surface reflectance of `9%`
- Bottom boundary defaults to fixed ambient temperature
- Material properties are simplified but structured for later refinement

## Phase 2 outputs

Phase 2 now writes:

- `p_concentration_heatmap.png`
- `final_p_profile.png`
- `junction_depth_vs_time.png`
- `source_inventory_vs_time.png`

## Next step

The current next step is to refine the `PSG/SiO2/Si` optical stack using the measured `500 kHz` / `95 um square flat-top` input, then add moving-interface doping physics and any needed scan-overlap corrections.
