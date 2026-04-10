# %% [markdown]
# # Laser PSG Phosphorus Doping Project
#
# ## Notebook-Style Total Walkthrough
#
# This document is a notebook-style master guide for the current project.
# It is written to answer four questions:
#
# 1. What problem are we modeling?
# 2. How is the code organized?
# 3. What mathematical and physical formulas are used in each module?
# 4. Why was each numerical algorithm chosen?
#
# The current code base is not yet a full FEM project.
# The present implementation is a staged 1D implicit finite-difference / finite-volume style model,
# built first to stabilize the physics chain:
#
# `laser -> heating -> phase change -> phosphorus transport -> profile / junction / dose`
#
# That choice was deliberate:
#
# 1. It is faster to validate.
# 2. It is easier to debug.
# 3. It is good for threshold studies.
# 4. It gives us a reliable baseline before adding texture enhancement or later moving to 2D / axisymmetric FEM.

# %% [markdown]
# ## 0. Repository Map
#
# The main files are:
#
# - `src/laser_doping_sim/phase1_thermal.py`
# - `src/laser_doping_sim/phase2_diffusion.py`
# - `src/laser_doping_sim/phase3_stack_thermal.py`
# - `run_phase3.py`
# - `run_phase3_power_scan.py`
# - `run_phase3_physics_validation.py`
#
# Their roles are:
#
# - `phase1_thermal.py`
#   Builds the base thermal model for Si under pulsed laser heating.
# - `phase2_diffusion.py`
#   Uses the thermal history to compute phosphorus transport in Si.
# - `phase3_stack_thermal.py`
#   Extends the thermal model from bare Si to a PSG / Si stack.
# - `run_phase3.py`
#   Runs one complete Phase 3 case.
# - `run_phase3_power_scan.py`
#   Runs many Phase 3 cases over a power sweep.
# - `run_phase3_physics_validation.py`
#   Checks whether the scan follows basic physical and logical trends.

# %% [markdown]
# ## 1. Physical Problem Statement
#
# We are modeling laser-assisted phosphorus doping of silicon with a surface PSG source.
#
# The physical sequence is:
#
# 1. A short green laser pulse deposits energy near the surface.
# 2. The PSG / Si stack heats very quickly.
# 3. Silicon may partially melt or fully melt locally.
# 4. The diffusion coefficient of P in Si rises dramatically with temperature and even more in liquid Si.
# 5. Phosphorus redistributes into the Si substrate.
# 6. The resulting P profile sets junction depth, sheet dose, and later sheet resistance.
#
# Important current assumptions:
#
# - Wavelength: `532 nm`
# - Repetition rate is used only to convert average power into pulse energy.
# - The present solver is single-pulse.
# - PSG is currently approximated as a P-rich `SiO2`-like layer with simplified thermal and optical properties.
# - The present model is `1D in depth`.
# - Texture enhancement has not yet been added to the solver itself.

# %% [markdown]
# ## 2. Why We Started With 1D Instead of FEM
#
# The original goal included FEM, which is reasonable.
# But for this problem, the main early risk was not mesh geometry.
# The main risk was getting the physics chain wrong.
#
# So the current sequence was:
#
# 1. Build a robust 1D thermal model.
# 2. Add phase change.
# 3. Add phosphorus transport.
# 4. Add PSG / Si stack physics.
# 5. Validate trends.
# 6. Only then move toward texture enhancement and later more geometric models.
#
# Why this is a good choice:
#
# - Nanosecond phase-change problems are stiff.
# - Boundary conditions and source terms matter more than geometry in the first debugging stage.
# - A wrong 2D FEM model is slower and harder to diagnose than a right 1D model.
#
# So the current solver is best understood as:
#
# - **physics-first baseline**
# - not yet **final geometry-complete production model**

# %% [markdown]
# ## 3. Phase 1 Thermal Model
#
# File:
#
# - `src/laser_doping_sim/phase1_thermal.py`
#
# ### 3.1 Main Data Structures
#
# The key dataclasses are:
#
# - `MaterialProperties`
# - `LaserPulse`
# - `SurfaceSourceLayer`
# - `SubstrateDoping`
# - `Domain1D`
# - `SimulationResult`
#
# Why dataclasses were chosen:
#
# 1. The project has many physical parameters.
# 2. We need explicit, typed containers instead of loose dictionaries.
# 3. It makes it easier to serialize summaries and reports.

# %% [markdown]
# ### 3.2 Laser Pulse Model
#
# The pulse is represented with a Gaussian time envelope.
#
# Core idea:
#
# \[
# q''(t) = q''_{peak} \exp\left(-\frac{(t-t_{peak})^2}{2\sigma^2}\right)
# \]
#
# where:
#
# - `t_peak` is the pulse-center time in the simulation window
# - `sigma` is related to the pulse FWHM
#
# The helper function is:
#
# - `gaussian_flux(...)`
#
# Why this choice:
#
# 1. It is smooth and easy to integrate numerically.
# 2. It is a common first approximation for pulsed laser heating.
# 3. It avoids artificial discontinuities from a hard rectangular pulse.

# %% [markdown]
# ### 3.3 Fluence and Energy Conversion
#
# The run scripts convert average laser power into pulse energy and fluence:
#
# \[
# E_{pulse} = \frac{P_{avg}}{f}
# \]
#
# \[
# F = \frac{E_{pulse}}{A_{spot}}
# \]
#
# where:
#
# - `P_avg` is average power
# - `f` is repetition rate
# - `A_spot` is the projected spot area
#
# This logic lives in:
#
# - `run_phase3.py`
# - `run_phase3_power_scan.py`
#
# Why this matters:
#
# - The heat solver uses fluence.
# - Experiments are often specified in average power.
# - The conversion is necessary to align simulation with the laser tool settings.

# %% [markdown]
# ### 3.4 Heat Equation
#
# The thermal model solves a 1D transient heat equation:
#
# \[
# \rho c_p^{app}(T)\frac{\partial T}{\partial t}
# = \frac{\partial}{\partial z}\left(k(T)\frac{\partial T}{\partial z}\right) + Q(z,t)
# \]
#
# Terms:
#
# - `rho`: density
# - `c_p^{app}(T)`: apparent heat capacity
# - `k(T)`: thermal conductivity
# - `Q(z,t)`: absorbed laser volumetric heat source
#
# Functions involved:
#
# - `apparent_heat_capacity(...)`
# - `thermal_conductivity(...)`
# - `volumetric_heat_source(...)`
# - `_assemble_matrix(...)`
# - `run_simulation(...)`

# %% [markdown]
# ### 3.5 Why Apparent Heat Capacity Was Chosen
#
# Phase change is currently handled with an apparent heat capacity / enthalpy-style approach.
#
# Instead of explicitly moving a sharp melt front, we spread latent heat over a small mushy range:
#
# \[
# c_p^{app}(T) = c_p(T) + \text{latent heat term over } [T_m-\Delta T/2,\; T_m+\Delta T/2]
# \]
#
# Why this algorithm was chosen:
#
# 1. It is stable for a first implementation.
# 2. It avoids front-tracking complexity.
# 3. It works well for rapid parameter scans.
#
# Why it is not final:
#
# - A moving-interface model is more physical.
# - But it is also more complex, especially once dopant partitioning is added.

# %% [markdown]
# ### 3.6 Heat Source in Si
#
# The simple thermal model uses a Beer-Lambert style absorbed source:
#
# \[
# Q(z,t) = \frac{(1-R)\, q''(t)}{\delta} \exp\left(-\frac{z}{\delta}\right)
# \]
#
# where:
#
# - `R` is reflectance
# - `delta` is absorption depth
#
# Why this was chosen:
#
# 1. It captures depth-localized absorption simply.
# 2. It is the standard first-order model for laser heating in absorbing media.
# 3. It is easy to generalize later to layered stacks.

# %% [markdown]
# ### 3.7 Numerical Method in Phase 1
#
# The solver uses an implicit sparse linear solve at each time step.
#
# Why:
#
# 1. Nanosecond thermal diffusion with phase change is stiff.
# 2. An explicit method would require much smaller time steps for stability.
# 3. The coefficient matrix is banded and efficient to solve.
#
# In plain language:
#
# - We write the heat equation on the depth grid.
# - We discretize time.
# - We solve a linear system for the next temperature field.
#
# This is one of the main reasons the current code is stable enough for sweeps.

# %% [markdown]
# ## 4. Phase 2 Diffusion Model
#
# File:
#
# - `src/laser_doping_sim/phase2_diffusion.py`
#
# Phase 2 takes a thermal history as input and computes the phosphorus concentration field in silicon.

# %% [markdown]
# ### 4.1 Core Diffusion Equation
#
# The transport equation is the 1D diffusion equation with time-dependent diffusivity:
#
# \[
# \frac{\partial C}{\partial t}
# = \frac{\partial}{\partial z}\left(D_{eff}(T,f_l)\frac{\partial C}{\partial z}\right)
# \]
#
# Here:
#
# - `C(z,t)` is phosphorus concentration
# - `D_eff` depends on temperature and liquid fraction
#
# This is implemented in:
#
# - `effective_diffusivity_m2_s(...)`
# - `_assemble_diffusion_matrix(...)`
# - `run_diffusion(...)`

# %% [markdown]
# ### 4.2 Solid and Liquid Diffusivity
#
# The solid and liquid diffusivities are both Arrhenius forms:
#
# \[
# D_s(T)=D_{0,s}\exp\left(-\frac{E_{a,s}}{k_B T}\right)
# \]
#
# \[
# D_l(T)=D_{0,l}\exp\left(-\frac{E_{a,l}}{k_B T}\right)
# \]
#
# Functions:
#
# - `solid_phosphorus_diffusivity_m2_s(...)`
# - `liquid_phosphorus_diffusivity_m2_s(...)`
#
# Why Arrhenius:
#
# 1. It is the standard form for thermally activated diffusion.
# 2. It makes the temperature dependence explicit.
# 3. It correctly creates huge diffusivity contrast between cold solid Si and near-liquid / liquid Si.

# %% [markdown]
# ### 4.3 What Happens in Partial Melting
#
# In the current model, partial melting uses a linear mixture:
#
# \[
# D_{eff}(T,f_l)= (1-f_l)D_s(T) + f_l D_l(T)
# \]
#
# where:
#
# - `f_l = 0` means fully solid
# - `f_l = 1` means fully liquid
# - `0 < f_l < 1` means partial melting
#
# Why this was chosen:
#
# 1. It is continuous and easy to compute.
# 2. It avoids abrupt jumps in `D`.
# 3. It is numerically stable for threshold studies.
#
# Why it is only an intermediate model:
#
# - Real interface transport is not necessarily a linear mixture.
# - A later moving-interface model can replace this approximation.

# %% [markdown]
# ### 4.4 Source Boundary Condition
#
# The present model does not use an infinite constant-concentration source at the surface.
# Instead, it uses a finite PSG reservoir / source-cell logic.
#
# The interface exchange velocity is modeled from:
#
# \[
# v_{ex} \sim \frac{D_{surf}}{\ell_{int}}
# \]
#
# and the surface flux is effectively:
#
# \[
# J \sim v_{ex}\left(C_{src}-C_{surf}\right)
# \]
#
# Functions:
#
# - `_surface_reservoir_concentration_m3(...)`
# - `_surface_exchange_velocity_m_s(...)`
#
# Why this was chosen:
#
# 1. It is more physical than a hard Dirichlet boundary.
# 2. It lets source inventory deplete.
# 3. It keeps the current model conservative.

# %% [markdown]
# ### 4.5 Why `melt_only` Was Introduced
#
# The current project often uses:
#
# - `boundary_model = finite_source_cell`
# - `source_exchange_mode = melt_only`
#
# This means:
#
# - strong extra PSG-to-Si injection is only enabled once the interface becomes sufficiently liquid
#
# Why this was introduced:
#
# 1. It prevents unrealistic strong solid-state interfacial injection during a nanosecond pulse.
# 2. It matches the literature intuition that strong laser doping is mainly melt-enabled.
# 3. It makes threshold behavior easier to interpret.
#
# Current caveat:
#
# - The exact threshold definition still needs refinement.
# - This is one of the known future cleanup items.

# %% [markdown]
# ### 4.6 Initial Profiles
#
# The model supports two initial sources inside silicon:
#
# 1. A base active emitter, modeled as an `erfc` profile
# 2. An inactive near-surface phosphorus layer
#
# #### Base Active Emitter
#
# The `erfc` emitter is:
#
# \[
# C_{init}(z)=C_s \, \mathrm{erfc}\left(\frac{z}{2L}\right)
# \]
#
# Why:
#
# - It is the classic analytical constant-source diffusion profile.
# - It is a good first approximation for a pre-existing `POCl3` emitter.
#
# #### Inactive Surface P Layer
#
# The inactive layer is represented as a top-hat concentration over a small surface thickness.
#
# Why:
#
# - It approximates residual surface phosphorus from previous processing.
# - It lets us distinguish chemical P inventory from electrically active donors.

# %% [markdown]
# ### 4.7 Junction Depth
#
# Junction depth is defined by the point where phosphorus concentration falls to the Ga background:
#
# \[
# C_P(z_j) = N_A^{Ga}
# \]
#
# In code:
#
# - `junction_depth_m(...)`
#
# Why this definition:
#
# 1. It is standard for an n-on-p compensation picture.
# 2. It directly connects profile shape to device-relevant depth.

# %% [markdown]
# ### 4.8 Net Donor and Active Donor Plots
#
# Two important electrical-style quantities are plotted:
#
# #### Initial active donor estimate
#
# \[
# N_{D,init}^{est}=\max(C_{active,init}-N_A^{Ga},0)
# \]
#
# #### Final chemical net donor upper bound
#
# \[
# N_{D,final}^{upper}=\max(C_{final}-N_A^{Ga},0)
# \]
#
# Why these are useful:
#
# 1. They are more device-relevant than total P concentration.
# 2. They show the effect of compensation by Ga.
# 3. They are the correct starting point for later sheet-resistance analysis.
#
# Why they can show a sharp drop:
#
# - Once `P` approaches the `Ga` background, the net donor collapses quickly.
# - In log plots, that appears as a steep fall.

# %% [markdown]
# ### 4.9 Numerical Method in Phase 2
#
# Diffusion is also solved with an implicit sparse linear system.
#
# Why this was chosen:
#
# 1. The liquid diffusivity can become very large.
# 2. Explicit time stepping would again become too restrictive.
# 3. It keeps the solver stable through strong diffusivity changes.
#
# One important detail:
#
# - harmonic averaging is used at cell interfaces
#
# Why:
#
# - it handles strong diffusivity contrast better than arithmetic averaging
# - it is more robust near sharp changes in temperature or liquid fraction

# %% [markdown]
# ## 5. Phase 3 Stack Thermal Model
#
# File:
#
# - `src/laser_doping_sim/phase3_stack_thermal.py`
#
# Phase 3 generalizes the bare-Si thermal model to a layered PSG / Si stack.

# %% [markdown]
# ### 5.1 Layered Geometry
#
# The stack includes:
#
# - a top PSG layer
# - an underlying Si layer
#
# Key dataclasses:
#
# - `PSGLayerProperties`
# - `StackOpticalProperties`
# - `StackDomain1D`
# - `StackSimulationResult`

# %% [markdown]
# ### 5.2 Layered Optical Heat Source
#
# The stack heat source uses a layered Beer-Lambert style model.
#
# In words:
#
# 1. The incident laser flux loses a fraction at the top reflectance.
# 2. Some energy is absorbed in PSG.
# 3. The remaining transmitted part enters Si.
# 4. Si then absorbs exponentially with its own absorption depth.
#
# Symbolically:
#
# \[
# Q_{PSG}(z,t)\propto (1-R) q''(t)\exp(-z/\delta_{PSG})
# \]
#
# \[
# Q_{Si}(z,t)\propto (1-R) T_{int} q''(t)\exp(-z/\delta_{Si})
# \]
#
# Function:
#
# - `layered_volumetric_heat_source(...)`
#
# Why this was chosen:
#
# 1. It is the simplest useful extension beyond bare Si.
# 2. It lets us separate surface reflectance, interface transmission, PSG absorption depth, and Si absorption depth.
# 3. It is still cheap enough for scans.

# %% [markdown]
# ### 5.3 Why PSG Is Currently Treated as P-Rich SiO2
#
# Present approximation:
#
# - PSG is modeled as a phosphorus-rich `SiO2`-like thermal layer
#
# Why:
#
# 1. It captures the fact that PSG is not bare silicon.
# 2. It gives us a surface source layer and thermal buffer.
# 3. It avoids pretending we already know the full detailed PSG composition-dependent optics.
#
# Why this is not final:
#
# - Real PSG is a `P2O5-SiO2` glass.
# - Real optical behavior may depend on composition and any thin interfacial oxide.

# %% [markdown]
# ### 5.4 How the Stack Connects to Diffusion
#
# After the stack thermal solve is done, the silicon part is extracted:
#
# - `silicon_subdomain_view(...)`
#
# That silicon-only thermal history becomes the input to Phase 2 diffusion.
#
# This is important conceptually:
#
# - the heat model is stack-aware
# - the dopant diffusion model is currently Si-only
#
# That separation keeps the code modular and easier to validate.

# %% [markdown]
# ## 6. Scans and Validation
#
# Two utility scripts matter a lot for development:
#
# - `run_phase3_power_scan.py`
# - `run_phase3_physics_validation.py`

# %% [markdown]
# ### 6.1 Power Scan
#
# The power scan script:
#
# 1. loops over powers
# 2. converts power to fluence
# 3. runs thermal stack simulation
# 4. runs diffusion
# 5. saves case-level summaries and aggregate plots
#
# Why this script exists:
#
# - Threshold behavior cannot be understood from one case.
# - Laser doping is highly sensitive to power around the melt threshold.

# %% [markdown]
# ### 6.2 Physics Validation
#
# The physics validation script was added to answer:
#
# - Are the scan trends physically self-consistent?
#
# It checks:
#
# - monotonic fluence
# - temperature behavior
# - liquid fraction trend
# - melt depth trend
# - junction depth trend
# - dose trend
# - mass balance
# - profile broadening diagnostics
#
# Why this matters:
#
# - a model can produce nice figures and still be physically misleading
# - this script gives us a reusable sanity gate before new features are added

# %% [markdown]
# ## 7. What `max_liquid_fraction` Means
#
# This metric is:
#
# \[
# \max_{z,t} f_l(z,t)
# \]
#
# It is the largest liquid fraction reached anywhere in the simulation.
#
# Interpretation:
#
# - `0` means completely solid everywhere
# - `1` means fully molten somewhere
# - values between `0` and `1` mean partial melting in the mushy model
#
# Why this metric is useful:
#
# 1. It tells us how close a case gets to melting.
# 2. It is often more informative than a binary melted / not-melted label.
# 3. It helps diagnose near-threshold cases.

# %% [markdown]
# ## 8. Why `peak P` Can Fall While Junction And Dose Rise
#
# This is one of the most important interpretation points in the project.
#
# `peak P` is only the maximum concentration value:
#
# \[
# C_{peak} = \max_z C(z)
# \]
#
# But junction depth and sheet dose depend on the entire profile.
#
# So it is entirely possible for:
#
# - the sharp surface peak to flatten
# - the profile to broaden
# - deeper concentrations to rise
# - total dose to rise
# - junction depth to rise
#
# all at the same time.
#
# This is why the project now uses additional diagnostics like:
#
# - `P(30 nm)`
# - `P(100 nm)`
# - `P(300 nm)`
# - near-surface cumulative dose
# - near-surface center of mass

# %% [markdown]
# ## 9. Current Limitations
#
# The present model is useful, but it is not yet complete.
#
# Main limitations:
#
# 1. Still `1D`
# 2. Not yet texture-enhanced
# 3. PSG optics are simplified
# 4. Interface transport is simplified
# 5. Partial-melt diffusivity is still a mixture approximation
# 6. No moving solid-liquid interface model yet
# 7. No solute trapping / partition coefficient model yet
# 8. No final activated-carrier + mobility sheet-resistance model yet

# %% [markdown]
# ## 10. Why Texture Enhancement Is the Next Step
#
# The present validation work suggests that the next important physical upgrade is not a giant melting-point correction.
# The next important upgrade is texture enhancement.
#
# Best first texture terms:
#
# 1. effective optical enhancement
# 2. effective increase in true PSG / Si interface area per projected wafer area
#
# Why these are the right first additions:
#
# - they are directly supported by textured-surface optics intuition
# - they change the absorbed thermal budget without forcing a nonphysical melt-point change

# %% [markdown]
# ## 11. Reproducibility Guide
#
# Typical commands:
#
# Single run:
#
# ```powershell
# python .\run_phase3.py --average-power-w 90 --t-end-ns 400
# ```
#
# Power scan:
#
# ```powershell
# python .\run_phase3_power_scan.py --output-dir outputs/phase3/power_scan_30_100w_dt005 --power-start-w 30 --power-stop-w 100 --power-step-w 5 --dt-ns 0.05 --t-end-ns 400 --nz 1200
# ```
#
# Physics validation:
#
# ```powershell
# python .\run_phase3_physics_validation.py
# ```

# %% [markdown]
# ## 12. Reading Order Recommendation
#
# If someone new joins the project, the fastest useful reading order is:
#
# 1. `run_phase3.py`
# 2. `phase3_stack_thermal.py`
# 3. `phase2_diffusion.py`
# 4. `run_phase3_power_scan.py`
# 5. `run_phase3_physics_validation.py`
#
# Why:
#
# - `run_phase3.py` tells you what inputs are exposed
# - `phase3_stack_thermal.py` tells you how heating is computed
# - `phase2_diffusion.py` tells you how doping is computed
# - the scan and validation scripts show how we judge whether the model behaves reasonably

# %% [markdown]
# ## 13. Final Summary
#
# The current project is a staged laser-doping simulator with:
#
# 1. pulsed thermal solve
# 2. phase-change handling
# 3. melt-sensitive phosphorus transport
# 4. stack-aware PSG / Si heating
# 5. power-scan infrastructure
# 6. explicit physical-validation tooling
#
# Its biggest strength right now is not geometric completeness.
# Its biggest strength is that the current baseline is explainable, testable, and physically audited.
#
# That is why it is a strong base for the next step: texture enhancement.

# %% [markdown]
# ## 14. Useful Companion Documents
#
# If you want the shorter prose versions, also read:
#
# - `docs/model_report_for_humans.md`
# - `docs/laser-psg-phosphorus-doping-paper-draft.md`
# - `docs/phase3-physics-validation.md`
# - `docs/phase3-physics-validation-work-report.md`
