# Laser Silicon Doping Simulation

This workspace now includes the Phase 1 thermal model, the corrected Phase 2/3 phosphorus diffusion model, and the Phase 4 multi-shot workflow for laser-induced silicon doping.

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

```powershell
python .\run_phase4_multishot.py `
  --output-dir outputs/phase4/example_multishot_run `
  --average-power-w 60 `
  --shots 10 `
  --thermal-history-mode accumulate `
  --cycle-end-ns 2000 `
  --dt-ns 0.05 `
  --nz 300 `
  --profile-shots 1 2 5 10
```

Default outputs are written to:

- `outputs/phase1/default_run/`
- `outputs/phase2/default_run/`
- `outputs/phase3/default_run/`
- `outputs/phase4/example_multishot_run/`

Documentation lives in:

- `docs/project_model_walkthrough_zh.md`
- `docs/project_model_walkthrough_en.md`
- `docs/current-model-summary.md`
- `docs/archive/README.md`
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
- `docs/phase4-multishot-v1-summary.md`
- `docs/phase4-thermal-history-v2-summary.md`
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

```powershell
python .\run_phase4_multishot.py `
  --output-dir outputs/phase4/example_multishot_fast `
  --average-power-w 60 `
  --shots 10 `
  --thermal-history-mode accumulate `
  --cycle-end-ns 2000 `
  --dt-ns 0.05 `
  --nz 300 `
  --profile-shots 1 10 `
  --fast-output
```

## Phase 4 run modes

- `--thermal-history-mode reuse_single_pulse`
  Reuses one single-pulse thermal history for every shot. This is the faster chemistry-focused approximation.
- `--thermal-history-mode accumulate`
  Reruns the stack thermal solve every shot and carries the cycle-end temperature field into the next shot. This is the physically richer but slower mode for pulse-train studies.
- `--fast-output`
  Keeps the core `csv/json/npz` outputs but skips figure generation and uses uncompressed `npz` saves to reduce post-processing overhead.

## Documentation map

- Use `docs/project_model_walkthrough_zh.md` or `docs/project_model_walkthrough_en.md` as the main technical walkthrough.
- Use `docs/physics_user_quickstart_zh.md` or `docs/physics_user_quickstart_en.md` for practical run order and output-reading guidance.
- Use `docs/physics_parameter_manual_zh.md` or `docs/physics_parameter_manual_en.md` when changing physics or command-line parameters.
- Use `docs/current-model-summary.md` as the short index into the active mainline documents.
- Use `docs/archive/README.md` for documents that were kept for history but are no longer the active entry points.

## Recent performance update

- The Phase 3 stack thermal solver and Phase 2 diffusion solver now use LAPACK tridiagonal solves plus vectorized matrix assembly.
- The integrated Phase 4 thermal-history path is much faster on the current CPU workflow without changing the model equations.
- The `--fast-output` switch is useful when we want long multi-shot scans for calibration or benchmarking and do not need plots for every run.

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

## Current mainline focus

The current mainline now supports both single-shot and multi-shot studies. The next modeling steps are mainly:

- tighter multi-shot calibration against measured activation / `Rsh`
- deciding when `reuse_single_pulse` is sufficient and when `accumulate` is required
- later optical and moving-interface refinements on top of the stabilized Phase 3 / Phase 4 baseline
