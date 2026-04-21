# Laser Activation Literature Notes

## Purpose

This note records primary literature relevant to the current question:

1. How much of phosphorus measured by `SIMS` is electrically active after
   laser processing.
2. Whether laser processing can reactivate initially inactive phosphorus in
   a pre-diffused emitter.
3. Whether phosphorus injected from a PSG-like source should be treated as
   fully active or only partially active in the sheet-resistance model.

The current conclusion is that the literature does **not** support using one
universal activation coefficient for all laser-doped phosphorus. Most papers
report:

- `SIMS` vs `ECV` profile differences,
- sheet-resistance changes,
- and process-regime dependence on laser fluence / melt state,

rather than one fixed activation fraction.

---

## Reference A1

- James et al., *CO2 laser processing of diffusion induced lattice imperfections in silicon: Experiment and theory*, Journal of Applied Physics 62 (1987), DOI:
  [10.1063/1.339384](https://doi.org/10.1063/1.339384)
- Accessible record:
  [ORNL / impact page](https://impact.ornl.gov/en/publications/cosub2sub-laser-processing-of-diffusion-induced-lattice-imperfect/)

### Why it matters here

This paper directly supports the idea that a pre-existing phosphorus-rich,
electrically inactive near-surface layer can become more electrically useful
after laser melting / regrowth.

### Evidence recorded

- The paper states that high-temperature phosphorus diffusion can form
  electrically inactive phosphorus-rich precipitates near the surface.
- It further reports that laser irradiation causes a large increase in carrier
  concentration and a drop in sheet resistivity.
- The mechanism is tied to near-surface melting and liquid-phase regrowth.

### Current project use

- Supports the assumption that part of the initial `inactive` phosphorus may
  become electrically active after laser processing.
- Supports treating this activation as melt-regime dependent rather than as a
  constant independent of thermal history.

### Status

- `direct`

---

## Reference A2

- Fell et al., *Industrial n-type PERL cells with screen printed front side
  electrodes approaching 21% efficiency*, 31st EUPVSEC (2015)
- PDF:
  [Fraunhofer ISE conference paper](https://www.ise.fraunhofer.de/content/dam/ise/de/documents/publications/conference-paper/31-eupvsec-2015/Jaeger_2CO31.pdf)

### Why it matters here

This paper is directly relevant because it compares `ECV` and `SIMS` after
laser doping from passivating / dopant layers and explicitly links the gap
between them to the amount of electrically active phosphorus.

### Evidence recorded

- Lower sheet resistance is associated with a higher amount of electrically
  active phosphorus.
- For one layer stack the authors report a significant difference between
  `ECV` and `SIMS`; for another stack the agreement is much better.
- This means the electrical activation cannot be treated as fixed only by the
  chemical phosphorus dose; layer chemistry matters.

### Current project use

- Supports splitting `final total P` and `final active donor` in the model.
- Supports using a separate activation factor for source-injected phosphorus,
  rather than assuming all injected phosphorus is automatically active.

### Status

- `direct`

---

## Reference A3

- Herguth et al., *On elimination of inactive phosphorus in industrial POCl3
  diffused emitters for high efficiency silicon solar cells*, Solar Energy
  Materials and Solar Cells (2017)
- Publisher page:
  [ScienceDirect abstract](https://www.sciencedirect.com/science/article/abs/pii/S0927024817303446)

### Why it matters here

This paper is not a laser-doping paper, but it is very important for the
initial condition. It shows that industrial phosphorus emitters can have a
dead layer and that the degree of inactivity depends strongly on the process.

### Evidence recorded

- The paper explicitly states that a dead layer forms when phosphorus exceeds
  solid-solubility-related limits and many phosphorus atoms become electrically
  inactive.
- It also reports inactive-phosphorus-free emitters in the range
  `65–140 ohm/sq` with surface doping roughly `1e20–3e20 cm^-3`.

### Current project use

- Supports the physical reality of the measured `SIMS - ECV` difference before
  laser processing.
- Supports not forcing the initial measured inactive layer to zero just because
  it is inconvenient numerically.

### Status

- `direct`

---

## Reference A4

- Lill et al., *Comparison of laser-doped emitters from as-deposited and
  thermally diffused APCVD doping glasses on silicon substrates*, SiliconPV
  2019 / AIP Proceedings record:
  [DNB copy](https://d-nb.info/1217194649/34)

### Why it matters here

This is one of the closest references to the current PSG question because it
compares laser doping from as-deposited and previously diffused glass / emitter
states and reports ECV-based active profiles plus sheet resistance.

### Evidence recorded

- The paper reports that a previously diffused shallow emitter gives only a
  small contribution to the final sheet resistance for APCVD PSG, compared with
  as-deposited PSG.
- It also reports that ECV-measured active phosphorus profiles are deeper when
  a shallow emitter already exists.
- This suggests that pre-existing inactive / active phosphorus and newly
  injected source phosphorus should not automatically be assigned the same
  activation behaviour.

### Current project use

- Supports keeping separate buckets for:
  - initial active phosphorus,
  - initial inactive phosphorus,
  - newly injected phosphorus.
- Supports calibrating different post-laser activation factors for those
  buckets.

### Status

- `direct`

---

## Working Conclusion for the Model

The current literature-backed modeling guidance is:

1. `Final total P` must include PSG-injected phosphorus.
2. `Final active donor` should **not** be assumed equal to `final total P`.
3. A pre-existing inactive phosphorus layer can become more electrically active
   after laser processing, especially when melt / regrowth occurs.
4. Source-injected phosphorus should also have its own activation factor.
5. These activation factors should be calibrated against measured
   `Rsh / ECV / SIMS`, rather than fixed a priori from one universal constant.

---

## Current Project Calibration Note

Using the current measured profile plus the experimental anchors:

- `30 W -> ~150 ohm/sq`
- `60 W -> ~60 ohm/sq`

the present reduced-order electrical fit gives:

- post-laser activation of initially inactive phosphorus:
  about `0.127`
- post-laser activation of PSG-injected phosphorus:
  about `0.194`

These are **current calibrated modeling parameters**, not universal material
constants.
