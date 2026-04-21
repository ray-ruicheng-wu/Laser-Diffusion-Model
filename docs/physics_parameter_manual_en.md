# Physics Parameter and Command-Line Manual

This manual is written for users who want a systematic understanding of the model parameters.

The goal is not just to list parameter names, but to place each one back into:

1. Which physical quantity it represents
2. Which equation it appears in
3. Why it affects the result
4. What usually happens if you increase or decrease it

## 1. Keep the main equations in mind

### 1.1 Thermal model

The single-layer silicon thermal model is based on:

```text
rho * c_eff(T) * dT/dt = d/dz [ k_eff(T) * dT/dz ] + Q(z,t)
```

where:

- `rho` is density
- `c_eff(T)` is the apparent heat capacity
- `k_eff(T)` is the effective thermal conductivity
- `Q(z,t)` is the laser volumetric heat source

### 1.2 Solid-liquid mixed region

The liquid fraction is represented through a narrow transition interval:

```text
f_l(T) =
0,                           T <= solidus
(T - solidus) / mushy_width, solidus < T < liquidus
1,                           T >= liquidus
```

### 1.3 Diffusion

The phosphorus diffusion model is based on:

```text
dC/dt = d/dz [ D_eff(T, f_l) * dC/dz ]
```

with

```text
D_eff = D_solid(T) * (1 - f_l) + D_liquid(T) * f_l
```

### 1.4 Interfacial injection

The source-to-silicon surface exchange is modeled as:

```text
J = h_m (C_src - C_surf)
```

with

```text
h_m ~ D_surface / L_tr
```

### 1.5 Sheet resistance

`Rsh` is not computed directly from total phosphorus. It is computed from electrically active donors:

```text
sigma(z) = q * mu(N_ionized) * n(z)
G_sheet = ∫ sigma(z) dz
Rsh = 1 / G_sheet
```

## 2. `src/laser_doping_sim/phase1_thermal.py`

This file defines the core parameters of the single-layer silicon thermal model.

### 2.1 `MaterialProperties`

Definition:

- [phase1_thermal.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase1_thermal.py#L21)

Parameters:

- `rho`
  - Physical quantity: density, in `kg/m^3`
  - Role: appears in the thermal inertia term `rho * c`
  - If increased: heating becomes slower and melting becomes harder

- `cp_solid`
  - Physical quantity: solid specific heat, in `J/(kg*K)`
  - Role: controls how much energy is required to heat the solid
  - If increased: the same laser input causes a smaller temperature rise

- `cp_liquid`
  - Physical quantity: liquid specific heat, in `J/(kg*K)`
  - Role: controls how easily the liquid region keeps heating
  - If increased: once melted, the temperature rises more slowly

- `k_solid`
  - Physical quantity: solid thermal conductivity, in `W/(m*K)`
  - Role: controls how quickly heat is conducted deeper into the substrate
  - If increased: the surface peak temperature usually drops, but heat may spread deeper

- `k_liquid`
  - Physical quantity: liquid thermal conductivity, in `W/(m*K)`
  - Role: controls heat transport in the liquid region
  - If increased: liquid-phase heat spreads away more easily

- `latent_heat`
  - Physical quantity: latent heat of fusion, in `J/kg`
  - Role: extra energy required during phase change
  - If increased: melting becomes harder and melt depth usually decreases

- `melt_temp`
  - Physical quantity: nominal melting temperature, in `K`
  - Role: defines the center of the phase-change interval
  - If increased: a higher temperature is required to melt

- `mushy_width`
  - Physical quantity: width of the solid-liquid transition interval, in `K`
  - Role: smooths a sharp phase change over a finite temperature range
  - If increased: the phase transition becomes numerically smoother, but the interface becomes less sharp

### 2.2 `LaserPulse`

Definition:

- [phase1_thermal.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase1_thermal.py#L33)

Parameters:

- `fluence`
  - Physical quantity: single-pulse energy density, in `J/m^2`
  - Role: controls the total injected energy
  - If increased: the temperature rises more and melting becomes easier

- `pulse_fwhm`
  - Physical quantity: pulse full width at half maximum, in `s`
  - Role: controls the time width of the Gaussian pulse
  - Principle: Gaussian temporal pulse shape
  - If decreased: the peak heat flux becomes sharper and larger
  - If increased: for the same total energy, the peak becomes lower and heating is more gradual

- `peak_time`
  - Physical quantity: pulse peak time, in `s`
  - Role: places the Gaussian pulse inside the simulation time window
  - This is mainly a numerical time-axis setting, not a material property
  - Changing it usually does not change total energy; it changes when the pulse arrives within the computational window

- `absorptivity`
  - Physical quantity: absorptivity, dimensionless
  - Role: determines how much of the incident light actually enters the heat source
  - If increased: heating becomes stronger

- `absorption_depth`
  - Physical quantity: absorption depth, in `m`
  - Principle: Beer-Lambert exponential absorption
  - If decreased: energy is deposited closer to the surface
  - If increased: energy is deposited deeper and more broadly

### 2.3 `SurfaceSourceLayer`

Definition:

- [phase1_thermal.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase1_thermal.py#L42)

Parameters:

- `kind`
  - Physical meaning: source type, for example `PSG`
  - Role: mainly metadata and later diffusion interpretation

- `dopant`
  - Physical meaning: dopant species in the source, for example `P`

- `dopant_concentration_cm3`
  - Physical quantity: dopant concentration in the source, in `cm^-3`
  - Role in diffusion: affects source inventory and available phosphorus supply
  - If increased: strong injection becomes easier

- `notes`
  - Documentation field, not a physics input

### 2.4 `SubstrateDoping`

Definition:

- [phase1_thermal.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase1_thermal.py#L50)

Parameters:

- `species`
  - Background substrate dopant species, for example `Ga`

- `concentration_cm3`
  - Physical quantity: background acceptor concentration, in `cm^-3`
  - Role: sets the junction-depth criterion and the net donor level
  - If increased: a higher donor concentration is needed to form a junction, so the junction usually becomes shallower

- `notes`
  - Documentation field

### 2.5 `Domain1D`

Definition:

- [phase1_thermal.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase1_thermal.py#L57)

Parameters:

- `thickness`
  - Physical quantity: computational depth, in `m`
  - If increased: boundary effects become smaller, but the computation becomes more expensive

- `nz`
  - Physical quantity: number of depth grid points
  - If increased: spatial resolution improves, but runtime increases

- `dt`
  - Physical quantity: time step, in `s`
  - If decreased: time resolution improves, but runtime increases

- `t_end`
  - Physical quantity: simulation end time, in `s`
  - If increased: longer cooling or post-pulse evolution can be captured

- `ambient_temp`
  - Physical quantity: ambient / initial temperature, in `K`
  - If increased: the substrate starts hotter and melting becomes easier

- `bottom_bc`
  - Physical meaning: bottom boundary condition
  - `dirichlet`: fixed bottom temperature
  - `neumann`: zero heat flux at the bottom
  - `dirichlet` is usually more conservative, while `neumann` tends to retain more heat

## 3. `src/laser_doping_sim/phase2_diffusion.py`

### 3.1 `DiffusionParameters`

Definition:

- [phase2_diffusion.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase2_diffusion.py#L27)

Parameters:

- `boundary_model`
  - Physical meaning: surface source boundary model
  - `finite_source_cell`: finite source inventory
  - `robin_reservoir`: more idealized Robin reservoir
  - The main workflow generally prefers `finite_source_cell`

- `source_exchange_mode`
  - Physical meaning: when source-to-silicon exchange is allowed
  - `melt_only`: injection only when the surface is liquid
  - `all_states`: exchange allowed in both solid and liquid states
  - `all_states` is closer to a continuous physical picture of weak solid-state injection and strong liquid-state injection

- `solid_diffusivity_m2_s`
  - Physical meaning: lower bound on solid-state diffusivity, in `m^2/s`
  - If set to `0`, solid diffusivity is computed purely from the Arrhenius law
  - If set to a positive value, it acts as a floor

- `solid_prefactor_cm2_s`
  - Physical quantity: Arrhenius prefactor for solid-state diffusion, in `cm^2/s`
  - If increased: solid-state diffusion becomes stronger

- `solid_activation_energy_ev`
  - Physical quantity: activation energy for solid-state diffusion, in `eV`
  - If increased: solid-state diffusion becomes harder

- `liquid_prefactor_cm2_s`
  - Physical quantity: Arrhenius prefactor for liquid-state diffusion, in `cm^2/s`
  - If increased: liquid-state diffusion becomes stronger

- `liquid_activation_energy_ev`
  - Physical quantity: activation energy for liquid-state diffusion, in `eV`
  - If increased: liquid-state diffusion becomes weaker

- `interface_liquid_threshold`
  - Physical meaning: liquid-fraction threshold used to decide whether the interface counts as melted
  - Only matters in `melt_only` mode
  - If increased: it becomes harder to turn on interface injection

- `source_effective_thickness_m`
  - Physical meaning: effective source thickness used when converting a source concentration into a finite surface inventory
  - If increased: the same source concentration corresponds to a larger total inventory

- `interfacial_transport_length_m`
  - Physical meaning: interfacial transport length / interfacial exchange resistance scale
  - Principle: `h_m ~ D / L_tr`
  - If increased: interface injection becomes slower
  - If decreased: interface injection becomes faster

- `initial_profile_kind`
  - Initial profile type
  - `none`: no initial emitter
  - `erfc_emitter`: analytical emitter profile
  - `measured`: measured initial profile

- `initial_profile_csv`
  - Path to the measured initial profile file

- `initial_surface_concentration_cm3`
  - Surface phosphorus concentration for the `erfc_emitter` option
  - If increased: the initial emitter becomes heavier doped

- `initial_junction_depth_m`
  - Initial junction depth for the `erfc_emitter` option
  - If increased: the initial emitter becomes deeper

- `initial_inactive_surface_p_concentration_cm3`
  - Physical meaning: concentration of an initial inactive surface phosphorus layer
  - Used to represent a high-concentration surface phosphorus reservoir that may not be electrically active

- `initial_inactive_surface_thickness_m`
  - Physical meaning: thickness of the initial inactive surface phosphorus layer
  - If increased: the inactive surface inventory becomes larger

- `texture_interface_area_factor`
  - Physical meaning: actual surface area divided by projected area for a textured interface
  - Role: increases total source-to-silicon exchange for conformal PSG coverage
  - If increased: injection becomes stronger for the same projected area

### 3.2 `DiffusionResult`

Definition:

- [phase2_diffusion.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase2_diffusion.py#L48)

This is mainly an output container. The most important fields are:

- `concentration_p_cm3`
  - Total phosphorus
- `initial_active_p_cm3`
  - Initial active profile
- `initial_inactive_p_cm3`
  - Initial inactive profile
- `junction_depth_m`
  - Junction depth over time
- `source_inventory_atoms_m2`
  - Remaining source inventory
- `surface_injection_flux_atoms_m2_s`
  - Interfacial injection flux

The additional `*_origin_*` fields are used for component bookkeeping and post-processing.

## 4. `src/laser_doping_sim/phase3_stack_thermal.py`

### 4.1 `PSGLayerProperties`

Definition:

- [phase3_stack_thermal.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase3_stack_thermal.py#L32)

Parameters:

- `rho`
  - PSG density, in `kg/m^3`
- `cp`
  - PSG specific heat, in `J/(kg*K)`
- `k`
  - PSG thermal conductivity, in `W/(m*K)`
- `thickness`
  - PSG thickness, in `m`
- `matrix_material`
  - Matrix-material label, default `SiO2`
- `dopant_oxide`
  - Dopant-oxide label, default `P2O5`
- `model_description`
  - Documentation field

Parameter intuition:

- Increasing `psg_thickness` changes how much light is absorbed before reaching Si
- Increasing `psg_k` makes PSG conduct heat more efficiently

### 4.2 `StackOpticalProperties`

Definition:

- [phase3_stack_thermal.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase3_stack_thermal.py#L45)

Parameters:

- `surface_reflectance`
  - Top-surface reflectance
  - If increased: less energy enters the stack

- `texture_reflectance_multiplier`
  - Texture correction factor
  - Used to convert a flat-surface reflectance into an effective textured reflectance
  - Values below `1` often represent stronger light trapping

- `interface_transmission`
  - PSG/Si interface transmission
  - If increased: more energy reaches silicon

- `psg_absorption_depth`
  - PSG absorption depth, in `m`
  - If decreased: PSG absorbs more strongly

- `si_absorption_depth`
  - Silicon absorption depth, in `m`
  - If increased: energy is deposited deeper in silicon

### 4.3 `StackDomain1D`

Definition:

- [phase3_stack_thermal.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase3_stack_thermal.py#L54)

Parameters:

- `silicon_thickness`
  - Silicon thickness
- `nz`
  - Total grid count in the stack
- `dt`
  - Time step
- `t_end`
  - End time
- `ambient_temp`
  - Initial temperature
- `bottom_bc`
  - Bottom boundary condition

## 5. `src/laser_doping_sim/phase4_multishot.py`

### 5.1 `MultiShotParameters`

Definition:

- [phase4_multishot.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase4_multishot.py#L34)

Parameters:

- `shot_count`
  - Number of shots
  - If increased: cumulative effects become stronger

- `source_replenishment_mode`
  - Whether the source is replenished between shots
  - Physically related to whether the precursor source recovers between repeated exposures

- `thermal_history_mode`
  - How thermal history is propagated across shots
  - Controls whether the model simply reuses a single-pulse history or carries temperature between shots

- `notes`
  - Documentation field

`MultiShotResult` is mainly an output structure, not a set of tuning inputs.

## 6. `src/laser_doping_sim/sheet_resistance.py`

### 6.1 `MasettiElectronMobilityModel`

Definition:

- [sheet_resistance.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/sheet_resistance.py#L10)

This is the empirical mobility parameter set used for sheet-resistance estimation.

Parameters:

- `temperature_k`
  - Measurement temperature, default `300 K`

- `mu_max_cm2_v_s`
  - Physical meaning: upper mobility limit in the lightly doped regime
  - If increased: conductivity rises in the low-to-moderate doping range and `Rsh` tends to decrease
- `mu_min1_cm2_v_s`
  - Physical meaning: one of the minimum-mobility terms in the heavily doped regime
  - If increased: the high-doping mobility floor is less severe and `Rsh` tends to drop
- `mu_min2_cm2_v_s`
  - Physical meaning: a second minimum-mobility term for the high-doping regime
  - If increased: conductivity in very heavily doped regions increases
- `mu_1_cm2_v_s`
  - Physical meaning: empirical amplitude of the high-concentration correction term
  - If increased: mobility suppression at high doping becomes stronger
- `c_r_cm3`
  - Physical meaning: characteristic concentration where the first mobility roll-off becomes important
  - If increased: the mobility drop is shifted to higher doping
- `c_s_cm3`
  - Physical meaning: characteristic concentration for the high-doping correction term
  - If increased: the strongest high-doping correction moves to higher concentration
- `alpha`
  - Physical meaning: exponent controlling the slope of the first roll-off
  - If increased: the mobility transition becomes steeper
- `beta`
  - Physical meaning: exponent controlling the slope of the high-doping correction
  - If increased: mobility becomes more sensitive in the ultra-high-doping range
- `p_c_cm3`
  - Physical meaning: reference concentration in the exponential pre-correction term
  - The default `0` means this term does not further reshape the low-doping behavior

These are empirical coefficients of the Masetti mobility model.

Physical interpretation:

- Together they determine how electron mobility changes with ionized impurity concentration
- They should usually not be changed casually without a literature basis

If you do change them, the main effect is on:

- `conductivity(z)`
- `Rsh`

They do not change the thermal or diffusion solvers themselves.

## 7. `src/laser_doping_sim/activation_models.py`

These are not parameters of the main diffusion PDE. They are empirical activation models used in `Rsh` post-processing.

### 7.1 `PiecewiseLinearNonactiveActivationModel`

Parameters:

- `initial_inactive_activation_fraction`
  - Baseline activation fraction of the initial inactive pool before the laser step

- `power_w`
  - Power sampling points

- `final_nonactive_activation_fraction`
  - Empirical activation fraction curve for the final non-active pool
  - If increased: more of the final non-active pool is counted as active donor and `Rsh` decreases

### 7.2 `PiecewiseLinearDualChannelActivationModel`

Parameters:

- `initial_inactive_activation_fraction`
  - Baseline activation fraction of the initial inactive pool before the laser step
- `power_w`
  - Power sampling points
- `final_inactive_activation_fraction`
  - Activation curve applied to the redistributed initial inactive component after laser processing
- `final_injected_activation_fraction`
  - Activation curve applied to the newly injected phosphorus component after laser processing

Physical idea:

- Initial inactive re-activation and newly injected-phosphorus activation are treated as separate channels

### 7.3 `PiecewiseMultiShotDualChannelActivationModel`

Parameters:

- `inactive_shot1_fraction`
  - Inactive-channel activation fraction after the first shot
- `inactive_inf_fraction`
  - Asymptotic inactive-channel activation fraction at large shot count
- `inactive_n0_shots`
  - Characteristic shot count controlling how fast the inactive channel approaches its asymptote
- `injected_shot1_fraction`
  - Injected-channel activation fraction after the first shot
- `injected_inf_fraction`
  - Asymptotic injected-channel activation fraction at large shot count
- `injected_reference_dose_cm2`
  - Reference injected dose used to scale the injected channel
- `injected_q0_cm2`
  - Characteristic injected dose controlling the activation evolution

Physical meaning:

- Describes how activation fractions evolve with shot number and accumulated dose in a multi-shot setting

This part is best treated as an empirical electrical-calibration layer rather than a first-round physics tuning target.

## 8. `src/laser_doping_sim/measured_profiles.py`

### 8.1 `MeasuredInitialProfile`

Parameters:

- `depth_nm`
  - Depth coordinate, in `nm`
- `total_p_cm3`
  - Total phosphorus concentration
  - Usually closest to the chemical total measured by SIMS
- `active_p_cm3`
  - Electrically active phosphorus
  - Usually closer to an ECV-like or electrically visible donor profile
- `inactive_p_cm3`
  - Inactive phosphorus
  - In the current measured-profile workflow, this is usually constructed as `max(total - active, 0)`

This is a data structure, not a PDE parameter block.

## 9. `run_phase1.py` parameter guide

This is the single-layer thermal driver.

### 9.1 Laser parameters

- `--fluence-j-cm2`
  - Single-pulse fluence
  - Increasing it usually makes melting easier

- `--pulse-fwhm-ns`
  - Temporal pulse width
  - Decreasing it increases the peak heat flux

- `--peak-time-ns`
  - Pulse peak time
  - Mainly controls where the pulse sits inside the time window

- `--absorption-depth-nm`
  - Single-layer Si absorption depth
  - Decreasing it shifts energy deposition closer to the surface

- `--absorptivity`
  - Absorptivity
  - Increasing it raises the temperature response

### 9.2 Grid and boundary parameters

- `--thickness-um`
  - 1D computational depth
  - If too small, the bottom boundary can affect the result; if too large, runtime increases
- `--nz`
  - Number of depth grid points
  - Increasing it improves spatial resolution
- `--dt-ns`
  - Time step
  - Decreasing it improves temporal resolution but increases runtime
- `--t-end-ns`
  - Total simulation time
  - Increasing it is useful for longer cooling tails
- `--ambient-temp-k`
  - Initial / ambient temperature
  - Increasing it makes melting easier
- `--bottom-bc`
  - Bottom boundary condition
  - `dirichlet` behaves more like a strong heat sink, `neumann` more like insulation

### 9.3 Phase-change parameters

- `--melt-temp-k`
  - Nominal melting temperature
  - Increasing it makes melting harder
- `--mushy-width-k`
  - Width of the solid-liquid transition interval
  - Increasing it smooths the transition and makes the interface less sharp

### 9.4 Source and substrate metadata

- `--source-kind`
  - Source label, for example `PSG`
- `--source-dopant`
  - Dopant label in the source, for example `P`
- `--source-dopant-concentration-cm3`
  - Source concentration metadata
  - In `Phase 1` it is recorded for downstream use, but does not feed back into the thermal field
- `--source-notes`
  - Source description text
- `--substrate-dopant`
  - Substrate background dopant label
- `--substrate-dopant-concentration-cm3`
  - Substrate background concentration metadata
- `--substrate-notes`
  - Substrate description text

## 10. `run_phase2.py` parameter guide

This inherits the `run_phase1.py` thermal parameters and adds diffusion-related ones.

Additional diffusion-related parameters:

- `--boundary-model`
  - Selects the surface boundary model

- `--source-exchange-mode`
  - Selects `melt_only` or `all_states`

- `--solid-diffusivity-m2-s`
  - Solid-state diffusivity lower bound

- `--solid-prefactor-cm2-s`
  - Solid-state Arrhenius prefactor
- `--solid-activation-energy-ev`
  - Solid-state diffusion activation energy
- `--liquid-prefactor-cm2-s`
  - Liquid-state Arrhenius prefactor
- `--liquid-activation-energy-ev`
  - Liquid-state diffusion activation energy

- `--interface-liquid-threshold`
  - Surface liquid-fraction threshold for `melt_only`

- `--source-effective-thickness-nm`
  - Effective source thickness used for source inventory

- `--interfacial-transport-length-nm`
  - Interfacial transport length

- `--initial-profile-kind`
  - `none` or `erfc_emitter`

- `--initial-surface-p-concentration-cm3`
  - Initial emitter surface concentration

- `--initial-junction-depth-nm`
  - Initial emitter junction depth

- `--initial-inactive-surface-p-concentration-cm3`
  - Initial inactive surface-layer concentration

- `--initial-inactive-surface-thickness-nm`
  - Initial inactive surface-layer thickness

Tuning intuition:

- If you want the pre-existing emitter to evolve even without melting, focus on the solid-state diffusion parameters
- If you want stronger `PSG` injection, focus on `source_effective_thickness`, `interfacial_transport_length`, and `source_exchange_mode`

## 11. `run_phase3.py` parameter guide

This is the main driver.

### 11.1 Equipment and spot parameters

- `--average-power-w`
  - Average laser power
  - Increasing it raises single-pulse energy

- `--repetition-rate-hz`
  - Repetition rate
  - At fixed average power, increasing it lowers single-pulse energy

- `--spot-shape`
  - `square_flat_top` or `circular_flat_top`

- `--square-side-um`
  - Square flat-top side length
  - Increasing it increases spot area and lowers fluence

- `--spot-diameter-um`
  - Circular flat-top diameter

- `--fluence-j-cm2`
  - If manually specified, it overrides the fluence derived from average power and spot area

### 11.2 Temporal pulse parameters

- `--pulse-fwhm-ns`
  - Temporal pulse width
  - Decreasing it sharpens the peak heat flux
- `--peak-time-ns`
  - Time location of the pulse peak on the simulation time axis
  - Mainly affects time-window placement

### 11.3 Optical parameters

- `--surface-reflectance`
  - Top-surface reflectance
  - If increased: less energy enters the sample, so temperature rise and melt depth usually decrease

- `--texture-reflectance-multiplier`
  - Texture reflectance correction
  - Values below `1` often represent stronger light trapping

- `--interface-transmission`
  - PSG/Si interface transmission
  - If increased: more energy reaches silicon

- `--psg-absorption-depth-um`
  - PSG absorption depth
  - If decreased: absorption inside PSG becomes stronger

- `--si-absorption-depth-nm`
  - Silicon absorption depth
  - If increased: heat deposition moves deeper; the surface peak may drop while the thermal penetration deepens

### 11.4 PSG layer properties

- `--psg-thickness-nm`
  - PSG thickness
  - Increasing it changes how much light is absorbed before reaching silicon
- `--psg-rho`
  - PSG density
- `--psg-cp`
  - PSG specific heat
- `--psg-k`
  - PSG thermal conductivity

### 11.5 Silicon thermal and grid parameters

- `--si-thickness-um`
  - Silicon subdomain thickness
- `--nz`
  - Total grid count in the stacked model
- `--dt-ns`
  - Time step
- `--t-end-ns`
  - Total simulation time
- `--ambient-temp-k`
  - Initial temperature
- `--melt-temp-k`
  - Nominal silicon melting temperature
- `--mushy-width-k`
  - Width of the silicon solid-liquid transition interval
- `--bottom-bc`
  - Bottom boundary condition

### 11.6 Source and substrate parameters

- `--source-kind`
  - Source label
- `--source-dopant`
  - Source dopant label
- `--source-dopant-concentration-cm3`
  - Source concentration
  - Increasing it raises the ceiling for possible injected dose
- `--source-notes`
  - Source description text
- `--substrate-dopant`
  - Background substrate dopant species
- `--substrate-dopant-concentration-cm3`
  - Background substrate concentration
  - Increasing it makes the junction criterion more stringent
- `--substrate-notes`
  - Substrate description text

### 11.7 Diffusion parameters

- `--boundary-model`
  - Selects finite source-cell or Robin-reservoir boundary behavior
- `--source-exchange-mode`
  - Selects melt-only injection or all-state exchange
- `--solid-diffusivity-m2-s`
  - Solid-state diffusivity floor
- `--solid-prefactor-cm2-s`
  - Solid-state Arrhenius prefactor
- `--solid-activation-energy-ev`
  - Solid-state diffusion activation energy
- `--liquid-prefactor-cm2-s`
  - Liquid-state Arrhenius prefactor
- `--liquid-activation-energy-ev`
  - Liquid-state diffusion activation energy
- `--interface-liquid-threshold`
  - Liquid-fraction threshold for opening the interface in `melt_only` mode
- `--source-effective-thickness-nm`
  - Effective source thickness
- `--interfacial-transport-length-nm`
  - Interfacial transport length

### 11.8 Initial-doping parameters

- `--initial-profile-kind`
  - `none`, `erfc_emitter`, or `measured`

- `--initial-profile-csv`
  - Path to the measured initial profile

- `--initial-surface-p-concentration-cm3`
  - Surface concentration used in the `erfc emitter` mode
- `--initial-junction-depth-nm`
  - Initial junction depth used in the `erfc emitter` mode

- `--initial-inactive-surface-p-concentration-cm3`
  - Concentration of the initial inactive surface layer
- `--initial-inactive-surface-thickness-nm`
  - Thickness of the initial inactive surface layer

### 11.9 Texture parameters

- `--texture-interface-area-factor`
  - Directly sets the actual/projected interface-area ratio
  - If increased: the total PSG-to-Si exchange area becomes larger and injection becomes stronger

- `--texture-pyramid-sidewall-angle-deg`
  - If the area factor is not given explicitly, it is estimated as `sec(angle)`
  - Larger angle means a larger estimated interface-area factor

- `--texture-notes`
  - Documentation field

Parameter intuition:

- To raise peak temperature: increase `average_power_w` or decrease `surface_reflectance`
- To deposit energy deeper: increase `si_absorption_depth_nm`
- To strengthen injection: increase `source_dopant_concentration_cm3` or decrease `interfacial_transport_length_nm`
- To strengthen texture-driven interface supply: increase `texture_interface_area_factor`

## 12. `run_phase3_power_scan.py` parameter guide

This script is largely the same as `run_phase3.py`, but adds power-scan controls:

- `--power-start-w`
  - Starting power

- `--power-stop-w`
  - Ending power

- `--power-step-w`
  - Step size

These three parameters only control the scan range, not the single-case physics itself.

Note that this script has defaults aimed more at research studies than at a minimal demo:

- `nz = 1200`
- `t_end_ns = 400`
- `initial_profile_kind = erfc_emitter`
- `initial_surface_p_concentration_cm3 = 3.5e20`
- `initial_junction_depth_nm = 300`
- `initial_inactive_surface_p_concentration_cm3 = 5.0e20`
- `initial_inactive_surface_thickness_nm = 30`

So it is best for systematic trend studies rather than a first minimal run.

## 13. `prepare_measured_initial_profile.py` parameter guide

- `--ecv-csv`
  - Path to the raw ECV file
  - This is the main source used to build the active profile

- `--sims-xlsx`
  - Path to the raw SIMS file
  - This is the main source used to build the total profile

- `--sims-location`
  - Which measurement location to read from the xlsx file
  - Changing it switches to a different measured profile in the same file

- `--output-csv`
  - Output path for the unified measured profile
  - This is the file most often reused later with `--initial-profile-kind measured`

- `--output-plot`
  - Output path for the preview plot
  - Useful for quickly checking whether the total / active / inactive split looks reasonable

- `--output-summary`
  - Output path for the summary json
  - Useful for recording which raw inputs were used to build the profile

Physically, this step is data preparation, not PDE solving.

## 14. `run_sheet_resistance_cases.py` parameter guide

This is the `Rsh` post-processing driver.

- `--case-dirs`
  - Case directories to process
  - Multiple power cases can be processed in a single run

- `--output-dir`
  - Output directory
  - The script writes summary tables and comparison plots here

- `--inactive-activation-fraction`
  - Activation fraction of the initial inactive pool before laser processing
  - Increasing it lowers `Rsh_init`

- `--final-inactive-activation-fraction`
  - Activation fraction of the redistributed inactive pool after laser processing
  - Increasing it lowers the post-laser `Rsh`

- `--injected-activation-fraction`
  - Activation fraction assumed for newly injected phosphorus after laser processing
  - Increasing it strengthens the electrical contribution of injected dose

- `--measurement-temperature-k`
  - Measurement temperature for the mobility model
  - Changing it affects `Rsh` through the mobility model

- `--activation-model`
  - `fixed_fractions`
  - `piecewise_nonactive_pool`
  - `piecewise_dual_channel`
  - Selects either fixed activation assumptions or power-dependent empirical activation curves

- `--activation-table-csv`
  - CSV file for the empirical activation curve
  - Only used in the piecewise activation modes

The most important physical point here is:

- This is not part of the main thermal-diffusion PDE system
- It is applied after total phosphorus has already been computed, in order to interpret some fraction of that phosphorus as electrically active donor

## 15. Advanced calibration scripts

These are research-oriented utilities, not first-pass scripts for a new user.

### 15.1 `run_dual_channel_activation_calibration.py`

Main parameters:

- `--case-dirs`
  - List of case directories used for calibration
- `--measured-rsh-csv`
  - CSV file containing measured `Rsh`
- `--output-dir`
  - Output directory for the calibrated model
- `--measurement-temperature-k`
  - Electrical post-processing temperature
- `--injection-threshold-cm2`
  - Cases below this injected-dose threshold are treated as mostly inactive-re-activation-dominated
- `--target-initial-rsh-ohm-per-sq`
  - Target initial sheet resistance used for calibration

### 15.2 `run_dual_channel_high_power_refit.py`

Main parameters:

- `--case-dirs`
  - Cases used in the high-power refit
- `--measured-rsh-csv`
  - Measured high-power `Rsh` table
- `--base-activation-csv`
  - Previously calibrated low-power activation curve
- `--initial-inactive-activation-fraction`
  - Baseline initial inactive activation fraction used when loading the base curve
- `--boundary-power-w`
  - Power at which the low-power activation curve is held fixed and the high-power refit begins
- `--output-dir`
  - Refit output directory
- `--measurement-temperature-k`
  - Electrical post-processing temperature

### 15.3 `run_dual_channel_monotonic_segment_refit.py`

Main parameters:

- `--case-dirs`
  - Cases used in the segment refit
- `--measured-rsh-csv`
  - Measured `Rsh` data
- `--base-activation-csv`
  - Base low-power activation table
- `--initial-inactive-activation-fraction`
  - Initial inactive activation fraction used when loading the base table
- `--measurement-temperature-k`
  - Electrical post-processing temperature
- `--output-dir`
  - Output directory

These scripts are not used to change the thermal or diffusion PDEs. They are used to calibrate how high-power electrical activation should be interpreted.

### 15.4 `run_phase4_multishot.py`

This script is the main multi-shot chemistry / thermal-history driver.

Main parameters:

- `--average-power-w`
  - Average laser power
  - Sets the per-pulse fluence through repetition rate and spot area
- `--shots`
  - Number of pulses in the train
  - Increasing it strengthens cumulative chemistry and thermal-history effects
- `--thermal-history-mode`
  - `reuse_single_pulse`: reuse one single-pulse thermal history every shot
  - `accumulate`: carry the cycle-end temperature profile into the next shot
- `--cycle-end-ns`
  - End time of each shot cycle in `accumulate` mode
  - Increasing it lets more cooling happen before the next shot
- `--source-replenishment-mode`
  - Controls whether the local source inventory is carried or reset between shots
- `--profile-shots`
  - Which shot indices should get detailed saved profiles
- `--fast-output`
  - Keeps the core `csv/json/npz` outputs but skips plots
  - Useful for long benchmark and calibration runs
- `--nz`
  - Stack grid count
  - Higher values improve spatial resolution but increase runtime
- `--dt-ns`
  - Thermal time step
  - Smaller values improve threshold-region fidelity but increase runtime

Most important physical interpretation:

- `thermal-history-mode` changes the pulse-train thermal assumption
- `shots` changes the accumulated chemistry history
- `fast-output` changes only output overhead, not the modeled physics

### 15.5 `run_phase4_multishot_sheet_resistance.py`

This script is the multi-shot electrical post-processing driver.

Main parameters:

- `--phase4-dir`
  - Existing multi-shot chemistry output directory
- `--activation-parameter-csv`
  - Multi-shot dual-channel activation parameter table
- `--output-dir`
  - Output directory for the post-processed `Rsh` results

Main interpretation:

- this script does not change the chemistry solution
- it applies the empirical electrical calibration layer shot by shot
- the key outputs are the activation ratios and `Rsh` trend with shot count

### 15.6 `run_phase3_physics_validation.py`

This script checks whether the power-scan outputs follow basic physical and logical trends.

Main parameters:

- `--scan-dir`
  - Main power-scan directory

- `--fine-scan-dir`
  - Fine-resolution power-scan directory

- `--output-dir`
  - Output directory for validation results

- `--depths-nm`
  - Depths at which the final phosphorus profile is sampled

- `--near-surface-window-nm`
  - Surface window thickness used for near-surface dose and center-of-mass checks

This script does not solve new PDEs. It audits existing scan results for trends such as:

- whether temperature rises overall with power
- whether melt depth and junction depth trends look reasonable
- whether near-surface dose and profile center of mass behave smoothly
- whether mass-balance errors remain acceptable

## 16. If you only want the shortest “what happens if I change this?” table

- Increase `average_power_w`
  - Single-pulse energy increases
  - Peak temperature rises
  - Melting becomes easier
  - Injection and junction depth are more likely to increase

- Decrease `pulse_fwhm_ns`
  - Peak heat flux rises
  - Instantaneous melting becomes easier

- Increase `surface_reflectance`
  - Less energy enters the sample
  - Temperature, melt depth, and diffusion response usually decrease

- Increase `si_absorption_depth_nm`
  - Heat is deposited deeper
  - Surface peak temperature may drop, while thermal penetration may deepen

- Increase `source_dopant_concentration_cm3`
  - The source becomes more phosphorus-rich
  - The injection ceiling increases

- Increase `interfacial_transport_length_nm`
  - Interfacial exchange slows down
  - Injection weakens

- Increase `solid_activation_energy_ev`
  - Solid-state diffusion weakens
  - Low-power diffusion becomes harder to observe

- Increase `liquid_prefactor_cm2_s`
  - Liquid-state diffusion strengthens
  - Doping penetrates more easily through melted regions

- Increase `initial_surface_p_concentration_cm3`
  - The initial emitter becomes more heavily doped
  - Even if later injection is weak, the final profile may still remain relatively deep

- Increase `initial_inactive_surface_p_concentration_cm3`
  - The initial inactive surface inventory becomes larger
  - The final `Rsh` interpretation becomes more sensitive to activation assumptions

- Increase `inactive_activation_fraction` or `injected_activation_fraction`
  - `Rsh` decreases
  - But this is an electrical post-processing effect, not an increase in total phosphorus

## 17. Recommended tuning order

If you want to fit the model physically, a good order is:

1. Fix the equipment input first
   - `average_power_w`
   - `repetition_rate_hz`
   - `spot size`
   - `pulse_fwhm_ns`

2. Then fix the optics
   - `surface_reflectance`
   - `interface_transmission`
   - `psg_absorption_depth`
   - `si_absorption_depth`

3. Then fix the thermal side
   - `melt_temp`
   - `mushy_width`
   - `PSG` / `Si` thermal properties

4. Then fix the diffusion side
   - `solid/liquid diffusivity`
   - `source_effective_thickness`
   - `interfacial_transport_length`

5. Only then use `Rsh` activation parameters for electrical calibration

If this order is reversed, it becomes easy to produce an apparently good `Rsh` fit while the underlying thermal or diffusion physics is still not right.
