# Literature Usage Register

## Purpose

This document records references in a step-by-step way for the current
laser-induced phosphorus doping model (`PSG -> Si`, 1D thermal + 1D diffusion).
Each step should state:

1. Which paper/book is used.
2. Which modeling step it supports.
3. Which assumption/formula/parameter is adopted from it.
4. Evidence status:
   - `direct`: directly supported by cited literature.
   - `inference`: reasonable inference based on cited literature.
   - `pending`: still needs targeted verification.

This file is meant to complement:
- [formula-reference-register.md](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/formula-reference-register.md)
- [wenshu-laoge-memory.md](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/wenshu-laoge-memory.md)

---

## Step Template

Use the following template for each new model step:

| Step-ID | Model Step | Reference | How It Is Used | Adopted Assumption / Formula / Parameter | Status |
|---|---|---|---|---|---|

---

## Current Core References (Recovered)

| Step-ID | Model Step | Reference | How It Is Used | Adopted Assumption / Formula / Parameter | Status |
|---|---|---|---|---|---|
| S1 | Diffusion PDE basics | Crank, *The Mathematics of Diffusion* https://people.bath.ac.uk/ensdasr/PAPERS/Crank-The-Mathematics-of-Diffusion.pdf | Foundation for 1D Fick diffusion and boundary-condition forms | `∂C/∂t = ∂/∂z(D∂C/∂z)`; Dirichlet/Neumann/Robin forms | direct |
| S2 | erfc emitter initialization | MIT diffusion notes https://ocw.mit.edu/courses/6-152j-micro-nano-processing-technology-fall-2005/fa6170fba10bd1341251791563a18fc2_lecture6.pdf | Build pre-diffused emitter initial profile | `C_init(z) = C_s erfc(z/(2L))` with junction-matching calibration | direct |
| S3 | Si optical constants at 532 nm | Green 2008 optical parameters https://subversion.xray.aps.anl.gov/AGIPD_TCAD/PyTCADTools/Attenuation/Silicon_absorption_coeff_visible_photon.pdf | 532 nm absorption-depth scale for thermal source | Beer-Lambert depth scale from Si optical data | direct |
| S4 | PSG precursor laser-doping framework | Lill et al., Materials 2021 (unified model) https://www.mdpi.com/1996-1944/14/9/2322 | High-level coupled thermal/diffusion workflow for precursor laser doping | Thermal + phase change + dopant transport coupling | direct |
| S5 | Liquid-phase redistribution | Jaeger et al., J. Appl. Phys. 2015 https://www.osti.gov/biblio/22402853 | Physical basis for strong redistribution during melt/re-solidification | Liquid-phase diffusion dominates in melt window | direct |
| S6 | Precursor-source sensitivity, threshold behavior | Lill et al., Materials 2017 https://www.mdpi.com/1996-1944/10/2/189 | Supports threshold sensitivity and precursor/melt coupling | Near-threshold outputs are highly sensitive to process/model conditions | direct |
| S7 | Threshold crossing in practical precursor laser doping | Lill et al., Solar 2022 https://www.mdpi.com/2673-9941/2/2/15 | Regime logic: crossing melt threshold enables strong doping response | Non-melt to melt regime transition is a key trend break | direct |
| S8 | PSG material-stack definition | PNNL 2012 PSG model https://www.pnnl.gov/publications/model-phosphosilicate-glass-deposition-pocl3-control-phosphorus-dose-si | Supports `PSG = P2O5-SiO2` glass interpretation | Effective high-P SiO2 layer approximation | direct |
| S9 | Industrial POCl3/PSG stack realism | Fraunhofer ISE 2017 https://www.ise.fraunhofer.de/content/dam/ise/de/documents/publications/conference-paper/33-eupvsec-2017/Werner_2AV214.pdf | Supports practical `PSG/SiO2/Si` stack context and barrier effects | Keep oxide/interface barrier as explicit caveat | direct |

---

## Texture Enhancement References (Newly Consolidated)

### T1. Texture lowers effective reflectance / increases effective absorption

| Step-ID | Model Step | Reference | How It Is Used | Adopted Assumption / Formula / Parameter | Status |
|---|---|---|---|---|---|
| T1-1 | Texture optics | Campbell and Green 1987, J. Appl. Phys. DOI https://doi.org/10.1063/1.339189 | Canonical basis that pyramidal texturing reduces front reflectance via light trapping | In 1D, collapse texture optics into `R_eff` modifier | direct |
| T1-2 | Texture optics reduction to model input | McIntosh and Baker-Finch (OPAL2 context) https://www2.pvlighthouse.com.au/calculators/opal%202/McIntosh%20and%20Baker-Finch%20-%20paper%20on%20OPAL2%20for%2038th%20IEEE.pdf | Practical route to map ray-tracing/texture optics into effective reflectance | `R_eff = m_R * R_flat` (calibrated by measurement/simulation) | inference |

Current project implementation used in texture cases:
- Historical sensitivity-test setting:
  - `m_R = 0.5` (i.e., `R_eff = 0.045` from `R_flat = 0.09`)
  - `absorptivity = 1 - R_eff = 0.955`
- Current official project interpretation after user clarification:
  - the user-provided `9%` reflectance is treated as a measured, already-textured value
  - therefore the formal modeling path sets `m_R = 1.0`
  - texture is currently carried only through the effective-area channel unless a separate reflectance calibration is provided

### T2. Texture increases true interface area and contact area

| Step-ID | Model Step | Reference | How It Is Used | Adopted Assumption / Formula / Parameter | Status |
|---|---|---|---|---|---|
| T2-1 | Texture area factor | Baker-Finch and McIntosh, IEEE JPV 2011 https://openresearch-repository.anu.edu.au/bitstreams/d07eb28a-1860-4a7a-a055-154c920f85a4/download | Gives ideal upright random-pyramid area scaling and discusses non-ideal coverage | Full-texture area ratio approximated as `A_real/A_proj ≈ sqrt(3)` at ideal 100% coverage | direct |
| T2-2 | Interface transfer scaling | Crank diffusion text https://people.bath.ac.uk/ensdasr/PAPERS/Crank-The-Mathematics-of-Diffusion.pdf | Supports using effective transfer coefficient in Robin boundary | `h_m,eff = h_m * A_factor` in reduced 1D boundary | inference |

Current project implementation used in texture cases:
- `texture_interface_area_factor = 1.732238499217892` (from 54.74 deg sidewall geometry)

### T3. Texture under laser can make local melt behavior spatially nonuniform

| Step-ID | Model Step | Reference | How It Is Used | Adopted Assumption / Formula / Parameter | Status |
|---|---|---|---|---|---|
| T3-1 | Local nonuniform melt intuition | NAIST thesis (laser doping on textured surfaces) https://naist.repo.nii.ac.jp/record/11626/files/R011537.pdf | Experimental/SEM narrative: textured morphology can lead to local melt-recrystallization nonuniformity | In 1D, represent this by effective threshold/parameter modifiers, not explicit lateral geometry | inference |
| T3-2 | Near-threshold regime sensitivity | Lill et al., Materials 2017 https://www.mdpi.com/1996-1944/10/2/189 | Supports strong sensitivity near threshold to modest condition changes | Treat threshold-adjacent anomalies with caution; require mesh/time-step checks | direct |

---

## 1D Reduction Recipe for Texture Effects

For current 1D model, the recommended reduced-order texture entry points are:

1. Optical channel:
   - `R_eff = m_R * R_flat`
   - `A_eff = 1 - R_eff`
   - affects thermal source and thus `T(t,z)`, melt depth, melt duration.

2. Interfacial mass-transfer channel:
   - `A_factor = A_real/A_proj` (default ideal: `sqrt(3)`)
   - `h_m,eff = A_factor * h_m`
   - if assuming conformal precursor coverage:
     `Gamma_src,0,eff = A_factor * Gamma_src,0`.

3. Optional threshold-spread channel (future):
   - replace hard single melt threshold by distributed effective melt gate.

---

## Validation Note: Texture First-Run Results (60 W and 90 W)

Data directories:
- [texture_cases_60w](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/texture_cases_60w)
- [texture_cases_90w](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/texture_cases_90w)

### Observed trend summary

1. `60 W`:
   - `area_only` almost identical to `flat` (no effective extra injection under current melt-gated logic).
   - `optical_only` raises `T_peak` and pushes slight injection activation.
   - `both` combines those effects.

2. `90 W`:
   - `area_only`: thermal is unchanged from `flat`, but `peak P` and dose rise strongly.
   - `optical_only`: thermal/melt metrics rise clearly (`T_peak`, melt depth, melt window), with moderate `peak P` rise.
   - `both`: strongest thermal + strongest chemical response.

### Literature consistency judgment

`directly consistent`:
- Optical modifier primarily changes heating/melting metrics.
- Interface-area modifier primarily changes source-to-Si transfer strength and near-surface concentration response.
- Combined modifier gives superposed/strongest response.

`most likely consistent`:
- At 60 W, area-only is weak because source exchange is melt-gated and melt activity is marginal.
- At 90 W, area-only mainly boosts `peak P` with limited junction-depth change because deeper broadening is still thermally limited.

`still pending`:
- Whether source inventory should always scale with `A_factor` (depends on real precursor conformality and how dose is defined per projected area).
- Need dedicated texture metrology-backed calibration for `m_R` and effective coverage factor.

### Current official reading after measured-reflectance clarification

The user later clarified that `surface_reflectance = 0.09` is a measured value for the real textured sample, not a flat-surface placeholder.
Therefore:

1. `optical_only` and `both` should now be read as sensitivity studies, not the mainline calibrated cases.
2. The current official texture path is:
   - keep `surface_reflectance = 0.09`
   - set `texture_reflectance_multiplier = 1.0`
   - study only the effective-area channel
3. Under this interpretation, the current official texture comparison cases are:
   - [texture_cases_60w/area_only](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/texture_cases_60w/area_only)
   - [texture_cases_90w/area_only](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/texture_cases_90w/area_only)

---

## Interface-Transport References

### I1. Thin interfacial oxide is real and affects phosphorus transport

| Step-ID | Model Step | Reference | How It Is Used | Adopted Assumption / Formula / Parameter | Status |
|---|---|---|---|---|---|
| I1-1 | `PSG/SiO2/Si` stack realism | Werner et al. 2017, Fraunhofer ISE https://www.ise.fraunhofer.de/content/dam/ise/de/documents/publications/conference-paper/33-eupvsec-2017/Werner_2AV214.pdf | Confirms that an intermediate oxide exists and that thinner oxide enhances laser doping effectiveness | Real interfacial barrier thickness is expected in the nm-to-tens-of-nm range, not implicitly `100 nm` | direct |
| I1-2 | POCl3/PSG diffusion chemistry | Jäger et al. 2020, ISFH abstract https://isfh.de/en/publications/advanced-chemical-model-for-the-diffusion-mechanism-of-phosphorus-into-the-silicon-wafer-during-pocl3-diffusion | Supports explicit growth of interfacial `SiO2` during diffusion/drive-in and its effect on P transport | Replace single `L_int` with explicit barrier thickness in next-generation interface model | direct |
| I1-3 | Laser doping sensitivity to oxide thickness | Messmer et al. 2020, Fraunhofer ISE https://www.ise.fraunhofer.de/content/dam/ise/de/documents/publications/conference-paper/37th-eupvsec-2020/Messmer_2CV144.pdf | Supports the trend that thinner intermediate oxide correlates with stronger `Rsh` reduction by laser doping | Use oxide thickness as a physical interface-control parameter rather than treating `100 nm` as real thickness | direct |

### I2. Segregation / pile-up at the interface should enter the model

| Step-ID | Model Step | Reference | How It Is Used | Adopted Assumption / Formula / Parameter | Status |
|---|---|---|---|---|---|
| I2-1 | Segregation boundary idea | Mustafa Radi dissertation, TU Wien https://www.iue.tuwien.ac.at/diss/radi/node24.html | Supports using segregation/pile-up at `Si/SiO2` interface in the boundary condition | Introduce `m = C_si / C_ox` or equivalent partition/segregation factor in future interface model | direct |
| I2-2 | Dopant crossing `SiOx` barrier | Feldmann et al. 2019, Solar Energy Materials and Solar Cells DOI https://doi.org/10.1016/j.solmat.2019.109978 | Closely analogous source/oxide/c-Si problem; abstract reports segregation coefficient and diffusivity in `SiOx` | Support explicit `oxide diffusivity + segregation coefficient` model instead of only `D_surface / L_int` | direct |

### I3. Recommended current interpretation

| Step-ID | Model Step | Reference | How It Is Used | Adopted Assumption / Formula / Parameter | Status |
|---|---|---|---|---|---|
| I3-1 | Current effective interface length | Current project code + references above | Clarifies the role of `interfacial_transport_length_m` in the present solver | `L_int` is a lumped effective transport-resistance length, not a measured oxide thickness | direct |
| I3-2 | Suggested next interface model | Lill 2017 https://www.mdpi.com/1996-1944/10/2/189, Hassan 2021 https://www.mdpi.com/1996-1944/14/9/2322 | Supports explicit precursor/source treatment for laser doping | Move toward `source cell + oxide barrier + segregation` rather than continuing with one ad hoc `L_int` | inference |

---

## Immediate Register Additions Suggested

Add these to the formal reference table in the next update cycle:

- `R-017`: Campbell and Green 1987 (pyramidal texture light trapping), DOI https://doi.org/10.1063/1.339189
- `R-018`: McIntosh/Baker-Finch OPAL2 optics reduction reference, link above
- `R-019`: Baker-Finch and McIntosh 2011 JPV (area factor `sqrt(3)` and facet/edge discussion), link above
- `R-020`: NAIST thesis for textured laser-doping morphology nonuniformity, link above

---

## Sheet Resistance Post-Processing

### References used

- `R-021`: Masetti et al. 1983, DOI [10.1109/T-ED.1983.21207](https://doi.org/10.1109/T-ED.1983.21207)

### Where it was used

1. New post-processing module:
   - [sheet_resistance.py](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/sheet_resistance.py)
2. New case post-processor:
   - [run_sheet_resistance_cases.py](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_sheet_resistance_cases.py)
3. Current use:
   - converting `active donor profile -> mobility -> conductivity(z) -> Rsh`
   - current mobility closure for `Rsh_init` / `Rsh_af`

### Current modeling note

- The present `Rsh` post-processing assumes single-crystal silicon electron mobility with the `Masetti @ 300 K` closure.
- The thin chemically inactive surface-P layer is not counted as fully active; its electrical contribution is scaled by a user-set activation fraction.
- In the 2026-04-09 run, the default electrical assumptions were:
  - `f_inactive = 0.05`
  - `f_injected = 1.0`
