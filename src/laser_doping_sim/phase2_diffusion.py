from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from scipy.constants import Boltzmann, e as elementary_charge
from scipy.integrate import cumulative_trapezoid
from scipy.linalg.lapack import dgtsv
from scipy.special import erfc, erfcinv

from .measured_profiles import load_measured_initial_profile_csv, interpolate_profile_log_cm3
from .phase1_thermal import MAX_CONCENTRATION_CM3, SimulationResult


CM3_TO_M3 = 1.0e6


@dataclass(slots=True)
class DiffusionParameters:
    boundary_model: str = "finite_source_cell"
    source_exchange_mode: str = "all_states"
    solid_diffusivity_m2_s: float = 0.0
    solid_prefactor_cm2_s: float = 8.0e-4
    solid_activation_energy_ev: float = 2.74
    liquid_prefactor_cm2_s: float = 1.4e-3
    liquid_activation_energy_ev: float = 0.183
    interface_liquid_threshold: float = 0.01
    source_effective_thickness_m: float = 100.0e-9
    interfacial_transport_length_m: float = 100.0e-9
    initial_profile_kind: str = "none"
    initial_profile_csv: str = ""
    initial_surface_concentration_cm3: float = 0.0
    initial_junction_depth_m: float = 0.0
    initial_inactive_surface_p_concentration_cm3: float = 0.0
    initial_inactive_surface_thickness_m: float = 0.0
    texture_interface_area_factor: float = 1.0


@dataclass(slots=True)
class DiffusionResult:
    thermal: SimulationResult
    concentration_p_cm3: np.ndarray
    initial_active_p_cm3: np.ndarray
    initial_inactive_p_cm3: np.ndarray
    junction_depth_m: np.ndarray
    source_inventory_atoms_m2: np.ndarray
    source_cell_concentration_cm3: np.ndarray
    surface_injection_flux_atoms_m2_s: np.ndarray
    diffusion_parameters: DiffusionParameters
    initial_injected_p_cm3: np.ndarray | None = None
    final_active_origin_p_cm3: np.ndarray | None = None
    final_inactive_origin_p_cm3: np.ndarray | None = None
    final_injected_origin_p_cm3: np.ndarray | None = None


def liquid_phosphorus_diffusivity_m2_s(
    temperature_k: np.ndarray,
    params: DiffusionParameters,
) -> np.ndarray:
    prefactor_m2_s = params.liquid_prefactor_cm2_s * 1.0e-4
    activation_j = params.liquid_activation_energy_ev * elementary_charge
    return prefactor_m2_s * np.exp(-activation_j / (Boltzmann * temperature_k))


def solid_phosphorus_diffusivity_m2_s(
    temperature_k: np.ndarray,
    params: DiffusionParameters,
) -> np.ndarray:
    prefactor_m2_s = params.solid_prefactor_cm2_s * 1.0e-4
    activation_j = params.solid_activation_energy_ev * elementary_charge
    intrinsic = prefactor_m2_s * np.exp(-activation_j / (Boltzmann * temperature_k))
    if params.solid_diffusivity_m2_s > 0.0:
        return np.maximum(intrinsic, params.solid_diffusivity_m2_s)
    return intrinsic


def effective_diffusivity_m2_s(
    temperature_k: np.ndarray,
    liquid_fraction: np.ndarray,
    params: DiffusionParameters,
) -> np.ndarray:
    solid_diffusivity = solid_phosphorus_diffusivity_m2_s(temperature_k, params)
    liquid_diffusivity = liquid_phosphorus_diffusivity_m2_s(temperature_k, params)
    return solid_diffusivity * (1.0 - liquid_fraction) + liquid_diffusivity * liquid_fraction


def _harmonic_mean(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    denominator = left + right
    mean = np.zeros_like(left)
    nonzero = denominator > 0.0
    mean[nonzero] = 2.0 * left[nonzero] * right[nonzero] / denominator[nonzero]
    return mean


def _surface_reservoir_concentration_m3(
    inventory_atoms_m2: float,
    source_concentration_cm3: float,
    params: DiffusionParameters,
) -> float:
    if inventory_atoms_m2 <= 0.0:
        return 0.0
    equivalent_m3 = inventory_atoms_m2 / params.source_effective_thickness_m
    source_limit_m3 = min(source_concentration_cm3, MAX_CONCENTRATION_CM3) * CM3_TO_M3
    return min(source_limit_m3, equivalent_m3)


def _surface_exchange_velocity_m_s(
    surface_diffusivity_m2_s: float,
    liquid_fraction_surface: float,
    surface_concentration_m3: float,
    source_concentration_m3: float,
    inventory_atoms_m2: float,
    dt: float,
    params: DiffusionParameters,
) -> float:
    if inventory_atoms_m2 <= 0.0 or source_concentration_m3 <= 0.0:
        return 0.0

    if params.boundary_model == "finite_source_cell":
        if params.source_exchange_mode == "melt_only" and liquid_fraction_surface <= params.interface_liquid_threshold:
            return 0.0
        if params.source_exchange_mode not in {"melt_only", "all_states"}:
            raise ValueError(f"Unsupported source_exchange_mode: {params.source_exchange_mode}")
    elif params.boundary_model != "robin_reservoir":
        raise ValueError(f"Unsupported boundary_model: {params.boundary_model}")

    driving_concentration_m3 = source_concentration_m3 - surface_concentration_m3
    if driving_concentration_m3 <= 0.0:
        return 0.0

    exchange_velocity_m_s = (
        params.texture_interface_area_factor * surface_diffusivity_m2_s / params.interfacial_transport_length_m
    )
    max_velocity_m_s = inventory_atoms_m2 / (dt * driving_concentration_m3)
    return max(0.0, min(exchange_velocity_m_s, max_velocity_m_s))


def _initial_active_profile_m3(
    depth_m: np.ndarray,
    background_m3: float,
    params: DiffusionParameters,
) -> np.ndarray:
    if params.initial_profile_kind == "none":
        return np.zeros_like(depth_m)

    if params.initial_profile_kind == "measured":
        if not params.initial_profile_csv:
            raise ValueError("initial_profile_csv must be provided when initial_profile_kind='measured'.")
        profile = load_measured_initial_profile_csv(params.initial_profile_csv)
        active_cm3 = interpolate_profile_log_cm3(depth_m * 1.0e9, profile.depth_nm, profile.active_p_cm3)
        return np.clip(active_cm3 * CM3_TO_M3, 0.0, MAX_CONCENTRATION_CM3 * CM3_TO_M3)

    if params.initial_profile_kind != "erfc_emitter":
        raise ValueError(f"Unsupported initial_profile_kind: {params.initial_profile_kind}")

    if params.initial_surface_concentration_cm3 <= 0.0 or params.initial_junction_depth_m <= 0.0:
        return np.zeros_like(depth_m)

    surface_m3 = min(params.initial_surface_concentration_cm3, MAX_CONCENTRATION_CM3) * CM3_TO_M3
    if surface_m3 <= background_m3:
        return np.zeros_like(depth_m)

    ratio = np.clip(background_m3 / surface_m3, 1.0e-30, 1.0 - 1.0e-15)
    eta = float(erfcinv(ratio))
    if not np.isfinite(eta) or eta <= 0.0:
        return np.zeros_like(depth_m)

    diffusion_length_m = params.initial_junction_depth_m / (2.0 * eta)
    profile = surface_m3 * erfc(depth_m / (2.0 * diffusion_length_m))
    return np.clip(profile, 0.0, MAX_CONCENTRATION_CM3 * CM3_TO_M3)


def _initial_total_profile_m3(
    depth_m: np.ndarray,
    background_m3: float,
    params: DiffusionParameters,
) -> np.ndarray:
    if params.initial_profile_kind == "measured":
        if not params.initial_profile_csv:
            raise ValueError("initial_profile_csv must be provided when initial_profile_kind='measured'.")
        profile = load_measured_initial_profile_csv(params.initial_profile_csv)
        total_cm3 = interpolate_profile_log_cm3(depth_m * 1.0e9, profile.depth_nm, profile.total_p_cm3)
        return np.clip(total_cm3 * CM3_TO_M3, 0.0, MAX_CONCENTRATION_CM3 * CM3_TO_M3)

    initial_active_profile = _initial_active_profile_m3(depth_m, background_m3, params)
    initial_inactive_profile = _initial_inactive_surface_profile_m3(depth_m, params)
    return np.clip(
        initial_active_profile + initial_inactive_profile,
        0.0,
        MAX_CONCENTRATION_CM3 * CM3_TO_M3,
    )


def _initial_inactive_surface_profile_m3(
    depth_m: np.ndarray,
    params: DiffusionParameters,
) -> np.ndarray:
    if params.initial_profile_kind == "measured":
        if not params.initial_profile_csv:
            raise ValueError("initial_profile_csv must be provided when initial_profile_kind='measured'.")
        profile = load_measured_initial_profile_csv(params.initial_profile_csv)
        inactive_cm3 = interpolate_profile_log_cm3(depth_m * 1.0e9, profile.depth_nm, profile.inactive_p_cm3)
        return np.clip(inactive_cm3 * CM3_TO_M3, 0.0, MAX_CONCENTRATION_CM3 * CM3_TO_M3)

    if params.initial_inactive_surface_p_concentration_cm3 <= 0.0 or params.initial_inactive_surface_thickness_m <= 0.0:
        return np.zeros_like(depth_m)
    inactive_concentration_m3 = (
        min(params.initial_inactive_surface_p_concentration_cm3, MAX_CONCENTRATION_CM3) * CM3_TO_M3
    )
    profile = np.zeros_like(depth_m)
    profile[depth_m <= params.initial_inactive_surface_thickness_m] = inactive_concentration_m3
    return profile


def _default_initial_source_inventory_atoms_m2(
    source_concentration_cm3: float,
    params: DiffusionParameters,
) -> float:
    return (
        source_concentration_cm3
        * CM3_TO_M3
        * params.source_effective_thickness_m
        * params.texture_interface_area_factor
    )


def _coerce_initial_profile_m3(
    profile_cm3: np.ndarray | None,
    depth_m: np.ndarray,
    label: str,
) -> np.ndarray | None:
    if profile_cm3 is None:
        return None
    values = np.asarray(profile_cm3, dtype=float)
    if values.shape != depth_m.shape:
        raise ValueError(
            f"{label} must have the same shape as thermal.depth. "
            f"Expected {depth_m.shape}, got {values.shape}."
        )
    return np.clip(values, 0.0, MAX_CONCENTRATION_CM3) * CM3_TO_M3


def _solve_tridiagonal(
    lower: np.ndarray,
    diag: np.ndarray,
    upper: np.ndarray,
    rhs: np.ndarray,
) -> np.ndarray:
    rhs_matrix = np.asarray(rhs, dtype=float)
    squeeze = rhs_matrix.ndim == 1
    if squeeze:
        rhs_matrix = rhs_matrix[:, None]
    _, _, _, solution, info = dgtsv(
        lower,
        diag,
        upper,
        rhs_matrix,
        overwrite_dl=1,
        overwrite_d=1,
        overwrite_du=1,
        overwrite_b=1,
    )
    if info != 0:
        raise np.linalg.LinAlgError(f"dgtsv failed with info={info}")
    if squeeze:
        return solution[:, 0]
    return solution


def _assemble_diffusion_matrix(
    diffusivity: np.ndarray,
    dt: float,
    dz: float,
    surface_exchange_velocity_m_s: float,
) -> tuple:
    n = diffusivity.size
    coeff = dt * _harmonic_mean(diffusivity[:-1], diffusivity[1:]) / dz**2

    lower = np.empty(n - 1, dtype=float)
    diag = np.empty(n, dtype=float)
    upper = np.empty(n - 1, dtype=float)

    surface_exchange = 2.0 * dt * surface_exchange_velocity_m_s / dz
    diag[0] = 1.0 + 2.0 * coeff[0] + surface_exchange
    upper[0] = -2.0 * coeff[0]
    if n > 2:
        diag[1:-1] = 1.0 + coeff[:-1] + coeff[1:]
        lower[:-1] = -coeff[:-1]
        upper[1:] = -coeff[1:]
    diag[-1] = 1.0 + 2.0 * coeff[-1]
    lower[-1] = -2.0 * coeff[-1]

    return lower, diag, upper


def junction_depth_m(
    concentration_m3: np.ndarray,
    background_m3: float,
    depth_m: np.ndarray,
) -> float:
    active = concentration_m3 >= background_m3
    if not np.any(active):
        return 0.0
    last_above = int(np.flatnonzero(active)[-1])
    if last_above == depth_m.size - 1:
        return float(depth_m[-1])

    next_index = last_above + 1
    c0 = concentration_m3[last_above]
    c1 = concentration_m3[next_index]
    z0 = depth_m[last_above]
    z1 = depth_m[next_index]

    if c0 == c1:
        return float(z0)

    fraction = (background_m3 - c0) / (c1 - c0)
    fraction = float(np.clip(fraction, 0.0, 1.0))
    return float(z0 + fraction * (z1 - z0))


def run_diffusion_with_state(
    thermal: SimulationResult,
    params: DiffusionParameters | None = None,
    initial_active_p_cm3: np.ndarray | None = None,
    initial_inactive_p_cm3: np.ndarray | None = None,
    initial_injected_p_cm3: np.ndarray | None = None,
    initial_source_inventory_atoms_m2: float | None = None,
) -> DiffusionResult:
    if params is None:
        params = DiffusionParameters()

    depth = thermal.depth
    time = thermal.time
    dz = depth[1] - depth[0]
    dt = time[1] - time[0]

    concentration_m3 = np.zeros((time.size, depth.size))
    junction_depth = np.zeros(time.size)
    inventory = np.zeros(time.size)
    source_cell_concentration_cm3 = np.zeros(time.size)
    surface_injection_flux_atoms_m2_s = np.zeros(time.size)

    source_concentration_cm3 = thermal.surface_source.dopant_concentration_cm3
    background_m3 = thermal.substrate_doping.concentration_cm3 * CM3_TO_M3
    derived_initial_active_profile = _initial_active_profile_m3(depth, background_m3, params)
    derived_initial_inactive_profile = _initial_inactive_surface_profile_m3(depth, params)
    derived_initial_injected_profile = np.zeros_like(depth)
    initial_active_profile = _coerce_initial_profile_m3(initial_active_p_cm3, depth, "initial_active_p_cm3")
    if initial_active_profile is None:
        initial_active_profile = derived_initial_active_profile
    initial_inactive_profile = _coerce_initial_profile_m3(initial_inactive_p_cm3, depth, "initial_inactive_p_cm3")
    if initial_inactive_profile is None:
        initial_inactive_profile = derived_initial_inactive_profile
    initial_injected_profile = _coerce_initial_profile_m3(initial_injected_p_cm3, depth, "initial_injected_p_cm3")
    if initial_injected_profile is None:
        initial_injected_profile = derived_initial_injected_profile
    initial_profile = np.clip(
        initial_active_profile + initial_inactive_profile + initial_injected_profile,
        0.0,
        MAX_CONCENTRATION_CM3 * CM3_TO_M3,
    )
    if initial_source_inventory_atoms_m2 is None:
        initial_inventory = _default_initial_source_inventory_atoms_m2(source_concentration_cm3, params)
    else:
        initial_inventory = float(max(0.0, initial_source_inventory_atoms_m2))
    initial_silicon_inventory = float(np.trapezoid(initial_profile, depth))
    total_inventory = initial_inventory + initial_silicon_inventory
    concentration_m3[0] = initial_profile
    junction_depth[0] = junction_depth_m(initial_profile, background_m3, depth)
    inventory[0] = initial_inventory
    source_cell_concentration_cm3[0] = _surface_reservoir_concentration_m3(
        inventory[0],
        source_concentration_cm3,
        params,
    ) / CM3_TO_M3

    if params.source_effective_thickness_m <= 0.0:
        raise ValueError("source_effective_thickness_m must be positive.")
    if params.interfacial_transport_length_m <= 0.0:
        raise ValueError("interfacial_transport_length_m must be positive.")
    if params.texture_interface_area_factor <= 0.0:
        raise ValueError("texture_interface_area_factor must be positive.")
    if params.initial_profile_kind == "measured" and not params.initial_profile_csv:
        raise ValueError("initial_profile_csv must be provided when initial_profile_kind='measured'.")

    previous_silicon_inventory_atoms_m2 = initial_silicon_inventory
    active_component_m3 = initial_active_profile.copy()
    inactive_component_m3 = initial_inactive_profile.copy()
    injected_component_m3 = initial_injected_profile.copy()

    for step in range(1, time.size):
        previous = active_component_m3 + inactive_component_m3 + injected_component_m3
        diffusivity = effective_diffusivity_m2_s(
            thermal.temperature[step],
            thermal.liquid_fraction[step],
            params,
        )

        surface_reservoir_concentration_m3 = _surface_reservoir_concentration_m3(
            inventory[step - 1],
            source_concentration_cm3,
            params,
        )
        surface_exchange_velocity_m_s = _surface_exchange_velocity_m_s(
            surface_diffusivity_m2_s=diffusivity[0],
            liquid_fraction_surface=float(thermal.liquid_fraction[step, 0]),
            surface_concentration_m3=previous[0],
            source_concentration_m3=surface_reservoir_concentration_m3,
            inventory_atoms_m2=float(inventory[step - 1]),
            dt=dt,
            params=params,
        )
        surface_injection_flux_atoms_m2_s[step] = (
            surface_exchange_velocity_m_s * max(0.0, surface_reservoir_concentration_m3 - previous[0])
        )

        lower, diag, upper = _assemble_diffusion_matrix(
            diffusivity=diffusivity,
            dt=dt,
            dz=dz,
            surface_exchange_velocity_m_s=surface_exchange_velocity_m_s,
        )
        zero_exchange_lower, zero_exchange_diag, zero_exchange_upper = _assemble_diffusion_matrix(
            diffusivity=diffusivity,
            dt=dt,
            dz=dz,
            surface_exchange_velocity_m_s=0.0,
        )

        total_rhs = previous.copy()
        if surface_exchange_velocity_m_s > 0.0:
            total_rhs[0] += (
                2.0
                * dt
                * surface_exchange_velocity_m_s
                * surface_reservoir_concentration_m3
                / dz
            )

        updated = _solve_tridiagonal(lower, diag, upper, total_rhs)
        updated = np.clip(updated, 0.0, MAX_CONCENTRATION_CM3 * CM3_TO_M3)

        zero_exchange_rhs = np.empty((depth.size, 2), dtype=float)
        zero_exchange_rhs[:, 0] = active_component_m3
        zero_exchange_rhs[:, 1] = inactive_component_m3
        solved_components = _solve_tridiagonal(
            zero_exchange_lower,
            zero_exchange_diag,
            zero_exchange_upper,
            zero_exchange_rhs,
        )
        updated_active_component = np.clip(solved_components[:, 0], 0.0, MAX_CONCENTRATION_CM3 * CM3_TO_M3)
        updated_inactive_component = np.clip(solved_components[:, 1], 0.0, MAX_CONCENTRATION_CM3 * CM3_TO_M3)

        silicon_inventory_atoms_m2 = float(np.trapezoid(updated, depth))
        max_step_inventory_atoms_m2 = previous_silicon_inventory_atoms_m2 + inventory[step - 1]
        if silicon_inventory_atoms_m2 > max_step_inventory_atoms_m2 > 0.0:
            scale = max_step_inventory_atoms_m2 / silicon_inventory_atoms_m2
            updated *= scale
            silicon_inventory_atoms_m2 = max_step_inventory_atoms_m2

        updated_injected_component = np.clip(
            updated - updated_active_component - updated_inactive_component,
            0.0,
            MAX_CONCENTRATION_CM3 * CM3_TO_M3,
        )
        updated = (
            updated_active_component
            + updated_inactive_component
            + updated_injected_component
        )
        silicon_inventory_atoms_m2 = float(np.trapezoid(updated, depth))

        silicon_gain_atoms_m2 = max(0.0, silicon_inventory_atoms_m2 - previous_silicon_inventory_atoms_m2)
        inventory[step] = max(0.0, inventory[step - 1] - silicon_gain_atoms_m2)
        source_cell_concentration_cm3[step] = _surface_reservoir_concentration_m3(
            inventory[step],
            source_concentration_cm3,
            params,
        ) / CM3_TO_M3
        concentration_m3[step] = updated
        junction_depth[step] = junction_depth_m(updated, background_m3, depth)
        previous_silicon_inventory_atoms_m2 = silicon_inventory_atoms_m2
        active_component_m3 = updated_active_component
        inactive_component_m3 = updated_inactive_component
        injected_component_m3 = updated_injected_component

    return DiffusionResult(
        thermal=thermal,
        concentration_p_cm3=concentration_m3 / CM3_TO_M3,
        initial_active_p_cm3=initial_active_profile / CM3_TO_M3,
        initial_inactive_p_cm3=initial_inactive_profile / CM3_TO_M3,
        junction_depth_m=junction_depth,
        source_inventory_atoms_m2=inventory,
        source_cell_concentration_cm3=source_cell_concentration_cm3,
        surface_injection_flux_atoms_m2_s=surface_injection_flux_atoms_m2_s,
        diffusion_parameters=params,
        initial_injected_p_cm3=initial_injected_profile / CM3_TO_M3,
        final_active_origin_p_cm3=active_component_m3 / CM3_TO_M3,
        final_inactive_origin_p_cm3=inactive_component_m3 / CM3_TO_M3,
        final_injected_origin_p_cm3=injected_component_m3 / CM3_TO_M3,
    )


def run_diffusion(
    thermal: SimulationResult,
    params: DiffusionParameters | None = None,
) -> DiffusionResult:
    return run_diffusion_with_state(
        thermal=thermal,
        params=params,
    )


def _summary(result: DiffusionResult) -> dict:
    initial_profile = result.concentration_p_cm3[0]
    final_profile = result.concentration_p_cm3[-1]
    background_cm3 = float(result.thermal.substrate_doping.concentration_cm3)
    initial_active_profile = result.initial_active_p_cm3
    initial_inactive_profile = result.initial_inactive_p_cm3
    initial_injected_profile = (
        result.initial_injected_p_cm3
        if result.initial_injected_p_cm3 is not None
        else np.zeros_like(final_profile)
    )
    final_active_origin_profile = (
        result.final_active_origin_p_cm3
        if result.final_active_origin_p_cm3 is not None
        else np.zeros_like(final_profile)
    )
    final_inactive_origin_profile = (
        result.final_inactive_origin_p_cm3
        if result.final_inactive_origin_p_cm3 is not None
        else np.zeros_like(final_profile)
    )
    final_injected_origin_profile = (
        result.final_injected_origin_p_cm3
        if result.final_injected_origin_p_cm3 is not None
        else np.zeros_like(final_profile)
    )
    depth_cm = result.thermal.depth * 1.0e2
    initial_active_donor_profile = np.maximum(initial_active_profile - background_cm3, 0.0)
    final_net_donor_profile = np.maximum(final_profile - background_cm3, 0.0)
    aligned_depth_cm, aligned_initial_profile = _surface_aligned_profile(depth_cm, initial_profile)
    _, aligned_final_profile = _surface_aligned_profile(depth_cm, final_profile)
    _, aligned_initial_active_profile = _surface_aligned_profile(depth_cm, initial_active_profile)
    _, aligned_initial_inactive_profile = _surface_aligned_profile(depth_cm, initial_inactive_profile)
    _, aligned_initial_injected_profile = _surface_aligned_profile(depth_cm, initial_injected_profile)
    _, aligned_initial_active_donor_profile = _surface_aligned_profile(depth_cm, initial_active_donor_profile)
    _, aligned_final_net_donor_profile = _surface_aligned_profile(depth_cm, final_net_donor_profile)
    _, aligned_final_active_origin_profile = _surface_aligned_profile(depth_cm, final_active_origin_profile)
    _, aligned_final_inactive_origin_profile = _surface_aligned_profile(depth_cm, final_inactive_origin_profile)
    _, aligned_final_injected_origin_profile = _surface_aligned_profile(depth_cm, final_injected_origin_profile)
    initial_silicon_inventory_atoms_m2 = float(np.trapezoid(initial_profile * CM3_TO_M3, result.thermal.depth))
    silicon_inventory_atoms_m2 = float(np.trapezoid(final_profile * CM3_TO_M3, result.thermal.depth))
    initial_source_inventory_atoms_m2 = float(result.source_inventory_atoms_m2[0])
    final_source_inventory_atoms_m2 = float(result.source_inventory_atoms_m2[-1])
    cumulative_injected_dose_atoms_m2 = float(np.trapezoid(result.surface_injection_flux_atoms_m2_s, result.thermal.time))
    surface_liquid_fraction = result.thermal.liquid_fraction[:, 0]
    source_depletion_atoms_m2 = max(0.0, initial_source_inventory_atoms_m2 - final_source_inventory_atoms_m2)
    if result.diffusion_parameters.source_exchange_mode == "melt_only":
        melt_gate_active_fraction = float(
            np.mean(surface_liquid_fraction > result.diffusion_parameters.interface_liquid_threshold)
        )
    else:
        melt_gate_active_fraction = 1.0
    return {
        "initial_peak_p_concentration_cm3": float(np.max(initial_profile)),
        "initial_junction_depth_m": float(result.junction_depth_m[0]),
        "final_peak_p_concentration_cm3": float(np.max(final_profile)),
        "final_junction_depth_m": float(result.junction_depth_m[-1]),
        "max_junction_depth_m": float(np.max(result.junction_depth_m)),
        "initial_active_peak_p_cm3": float(np.max(initial_active_profile)),
        "initial_inactive_surface_peak_p_cm3": float(np.max(initial_inactive_profile)),
        "texture_interface_area_factor": float(result.diffusion_parameters.texture_interface_area_factor),
        "peak_source_cell_concentration_cm3": float(np.max(result.source_cell_concentration_cm3)),
        "peak_surface_injection_flux_atoms_m2_s": float(np.max(result.surface_injection_flux_atoms_m2_s)),
        "cumulative_injected_dose_cm2": cumulative_injected_dose_atoms_m2 / 1.0e4,
        "max_surface_liquid_fraction": float(np.max(surface_liquid_fraction)),
        "initial_source_inventory_atoms_m2": initial_source_inventory_atoms_m2,
        "initial_silicon_inventory_atoms_m2": initial_silicon_inventory_atoms_m2,
        "final_source_inventory_atoms_m2": final_source_inventory_atoms_m2,
        "final_silicon_inventory_atoms_m2": silicon_inventory_atoms_m2,
        "source_depletion_fraction": (
            0.0
            if initial_source_inventory_atoms_m2 <= 0.0
            else max(0.0, (initial_source_inventory_atoms_m2 - final_source_inventory_atoms_m2) / initial_source_inventory_atoms_m2)
        ),
        "cumulative_injected_vs_depletion_relative_error": (
            0.0
            if source_depletion_atoms_m2 <= 0.0
            else (cumulative_injected_dose_atoms_m2 - source_depletion_atoms_m2) / source_depletion_atoms_m2
        ),
        "melt_gate_active_fraction": melt_gate_active_fraction,
        "initial_sheet_dose_cm2": float(np.trapezoid(aligned_initial_profile, aligned_depth_cm)),
        "final_sheet_dose_cm2": float(np.trapezoid(aligned_final_profile, aligned_depth_cm)),
        "initial_active_sheet_dose_cm2": float(np.trapezoid(aligned_initial_active_profile, aligned_depth_cm)),
        "initial_inactive_sheet_dose_cm2": float(np.trapezoid(aligned_initial_inactive_profile, aligned_depth_cm)),
        "initial_injected_sheet_dose_cm2": float(np.trapezoid(aligned_initial_injected_profile, aligned_depth_cm)),
        "initial_net_donor_sheet_dose_cm2": float(np.trapezoid(aligned_initial_active_donor_profile, aligned_depth_cm)),
        "final_net_donor_sheet_dose_cm2": float(np.trapezoid(aligned_final_net_donor_profile, aligned_depth_cm)),
        "final_active_origin_sheet_dose_cm2": float(np.trapezoid(aligned_final_active_origin_profile, aligned_depth_cm)),
        "final_inactive_origin_sheet_dose_cm2": float(np.trapezoid(aligned_final_inactive_origin_profile, aligned_depth_cm)),
        "final_injected_origin_sheet_dose_cm2": float(np.trapezoid(aligned_final_injected_origin_profile, aligned_depth_cm)),
        "final_mass_balance_error_atoms_m2": (
            initial_source_inventory_atoms_m2
            + initial_silicon_inventory_atoms_m2
            - final_source_inventory_atoms_m2
            - silicon_inventory_atoms_m2
        ),
        "background_ga_concentration_cm3": background_cm3,
    }


def save_outputs(result: DiffusionResult, output_dir: str | Path) -> Path:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    np.savez_compressed(
        output_path / "phase2_results.npz",
        time_s=result.thermal.time,
        depth_m=result.thermal.depth,
        concentration_p_cm3=result.concentration_p_cm3,
        initial_active_p_cm3=result.initial_active_p_cm3,
        initial_inactive_p_cm3=result.initial_inactive_p_cm3,
        initial_injected_p_cm3=result.initial_injected_p_cm3,
        final_active_origin_p_cm3=result.final_active_origin_p_cm3,
        final_inactive_origin_p_cm3=result.final_inactive_origin_p_cm3,
        final_injected_origin_p_cm3=result.final_injected_origin_p_cm3,
        junction_depth_m=result.junction_depth_m,
        source_inventory_atoms_m2=result.source_inventory_atoms_m2,
        source_cell_concentration_cm3=result.source_cell_concentration_cm3,
        surface_injection_flux_atoms_m2_s=result.surface_injection_flux_atoms_m2_s,
    )

    summary = {
        "phase2_output_dir": str(output_path),
        "surface_source": asdict(result.thermal.surface_source),
        "substrate_doping": asdict(result.thermal.substrate_doping),
        "diffusion_parameters": asdict(result.diffusion_parameters),
        "metrics": _summary(result),
    }
    with (output_path / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)

    _plot_concentration_heatmap(result, output_path / "p_concentration_heatmap.png")
    _plot_final_profile(result, output_path / "final_p_profile.png")
    _plot_final_profile_cropped(result, output_path / "final_p_profile_cropped_to_junction_plus_50nm.png")
    _plot_junction_depth(result, output_path / "junction_depth_vs_time.png")
    _plot_source_inventory(result, output_path / "source_inventory_vs_time.png")
    _plot_sheet_analysis_profile(result, output_path / "silicon_p_profile_sheet_analysis.png")
    _plot_cumulative_sheet_dose(result, output_path / "cumulative_p_dose_vs_depth.png")
    _save_profile_analysis_table(result, output_path / "silicon_profile_analysis.csv")
    return output_path


def _plot_concentration_heatmap(result: DiffusionResult, path: Path) -> None:
    values = np.log10(np.maximum(result.concentration_p_cm3, 1.0e10))
    figure, axis = plt.subplots(figsize=(8, 5))
    image = axis.imshow(
        values.T,
        origin="lower",
        aspect="auto",
        extent=[
            result.thermal.time[0] * 1.0e9,
            result.thermal.time[-1] * 1.0e9,
            result.thermal.depth[0] * 1.0e6,
            result.thermal.depth[-1] * 1.0e6,
        ],
        cmap="magma",
    )
    axis.set_xlabel("Time (ns)")
    axis.set_ylabel("Depth (um)")
    axis.set_title("log10(P Concentration)")
    colorbar = figure.colorbar(image, ax=axis)
    colorbar.set_label("log10(P) [cm^-3]")
    figure.tight_layout()
    figure.savefig(path, dpi=200)
    plt.close(figure)


def _plot_final_profile(result: DiffusionResult, path: Path) -> None:
    figure, axis = plt.subplots(figsize=(8, 4))
    depth_um = result.thermal.depth * 1.0e6
    raw_initial_profile = result.concentration_p_cm3[0]
    final_profile = np.maximum(result.concentration_p_cm3[-1], 1.0e10)
    background = result.thermal.substrate_doping.concentration_cm3

    if np.max(raw_initial_profile) > 0.0:
        initial_profile = np.maximum(raw_initial_profile, 1.0e10)
        axis.semilogy(
            depth_um,
            initial_profile,
            color="#5d6d7e",
            lw=1.8,
            ls="--",
            label="Initial P profile",
        )
    axis.semilogy(
        depth_um,
        final_profile,
        color="#117864",
        lw=2.0,
        label="Final P profile",
    )
    axis.axhline(background, color="#cb4335", ls="--", lw=1.5, label="Ga background")
    if result.junction_depth_m[0] > 0.0:
        axis.axvline(
            result.junction_depth_m[0] * 1.0e6,
            color="#5d6d7e",
            ls=":",
            lw=1.4,
            label="Initial junction depth",
        )
    if result.junction_depth_m[-1] > 0.0:
        axis.axvline(
            result.junction_depth_m[-1] * 1.0e6,
            color="#7d3c98",
            ls="-.",
            lw=1.5,
            label="Final junction depth",
        )

    axis.set_xlabel("Depth (um)")
    axis.set_ylabel("Concentration (cm^-3)")
    axis.set_title("Initial vs Final P Concentration Profile")
    axis.grid(alpha=0.25)
    axis.legend()
    figure.tight_layout()
    figure.savefig(path, dpi=200)
    plt.close(figure)


def _profile_crop_limit_um(result: DiffusionResult, margin_nm: float = 50.0) -> float:
    final_junction_um = max(float(result.junction_depth_m[-1]) * 1.0e6, 0.0)
    initial_junction_um = max(float(result.junction_depth_m[0]) * 1.0e6, 0.0)
    margin_um = margin_nm * 1.0e-3
    crop_limit_um = max(final_junction_um, initial_junction_um) + margin_um
    minimum_window_um = 0.1
    maximum_window_um = float(result.thermal.depth[-1] * 1.0e6)
    return min(max(crop_limit_um, minimum_window_um), maximum_window_um)


def _plot_final_profile_cropped(result: DiffusionResult, path: Path) -> None:
    figure, axis = plt.subplots(figsize=(8, 4))
    depth_um = result.thermal.depth * 1.0e6
    raw_initial_profile = result.concentration_p_cm3[0]
    final_profile = np.maximum(result.concentration_p_cm3[-1], 1.0e10)
    background = result.thermal.substrate_doping.concentration_cm3
    crop_limit_um = _profile_crop_limit_um(result)

    if np.max(raw_initial_profile) > 0.0:
        initial_profile = np.maximum(raw_initial_profile, 1.0e10)
        axis.semilogy(
            depth_um,
            initial_profile,
            color="#5d6d7e",
            lw=1.8,
            ls="--",
            label="Initial P profile",
        )
    axis.semilogy(
        depth_um,
        final_profile,
        color="#117864",
        lw=2.0,
        label="Final P profile",
    )
    axis.axhline(background, color="#cb4335", ls="--", lw=1.5, label="Ga background")
    if result.junction_depth_m[0] > 0.0:
        axis.axvline(
            result.junction_depth_m[0] * 1.0e6,
            color="#5d6d7e",
            ls=":",
            lw=1.4,
            label="Initial junction depth",
        )
    if result.junction_depth_m[-1] > 0.0:
        axis.axvline(
            result.junction_depth_m[-1] * 1.0e6,
            color="#7d3c98",
            ls="-.",
            lw=1.5,
            label="Final junction depth",
        )

    axis.set_xlim(0.0, crop_limit_um)
    axis.set_xlabel("Depth (um)")
    axis.set_ylabel("Concentration (cm^-3)")
    axis.set_title("P Profile Cropped to Junction + 50 nm")
    axis.grid(alpha=0.25)
    axis.legend()
    figure.tight_layout()
    figure.savefig(path, dpi=200)
    plt.close(figure)


def _plot_junction_depth(result: DiffusionResult, path: Path) -> None:
    figure, axis = plt.subplots(figsize=(8, 4))
    axis.plot(
        result.thermal.time * 1.0e9,
        result.junction_depth_m * 1.0e9,
        color="#6c3483",
        lw=2.0,
        label="Laser process junction depth",
    )
    if result.junction_depth_m[0] > 0.0:
        axis.axhline(
            result.junction_depth_m[0] * 1.0e9,
            color="#5d6d7e",
            ls="--",
            lw=1.5,
            label="Initial junction depth",
        )
    axis.set_xlabel("Time (ns)")
    axis.set_ylabel("Doping Depth (nm)")
    axis.set_title("Initial vs Evolving Junction Depth")
    axis.grid(alpha=0.25)
    axis.legend()
    figure.tight_layout()
    figure.savefig(path, dpi=200)
    plt.close(figure)


def _plot_source_inventory(result: DiffusionResult, path: Path) -> None:
    figure, axis = plt.subplots(figsize=(8, 4))
    axis.plot(
        result.thermal.time * 1.0e9,
        result.source_inventory_atoms_m2,
        color="#af601a",
        lw=2.0,
    )
    axis.set_xlabel("Time (ns)")
    axis.set_ylabel("Source Inventory (atoms/m^2)")
    axis.set_title("PSG Source Inventory vs Time")
    axis.grid(alpha=0.25)
    figure.tight_layout()
    figure.savefig(path, dpi=200)
    plt.close(figure)


def _profile_window_um(result: DiffusionResult) -> float:
    junction_depth_um = max(float(np.max(result.junction_depth_m)) * 1.0e6, 0.0)
    if junction_depth_um <= 0.0:
        return min(1.0, float(result.thermal.depth[-1] * 1.0e6))
    return min(max(1.0, 2.0 * junction_depth_um), float(result.thermal.depth[-1] * 1.0e6))


def _surface_aligned_profile(depth_cm: np.ndarray, profile_cm3: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    if depth_cm.size == 0:
        return depth_cm, profile_cm3
    if depth_cm[0] <= 0.0:
        return depth_cm, profile_cm3
    aligned_depth_cm = np.concatenate(([0.0], depth_cm))
    aligned_profile_cm3 = np.concatenate(([profile_cm3[0]], profile_cm3))
    return aligned_depth_cm, aligned_profile_cm3


def _plot_sheet_analysis_profile(result: DiffusionResult, path: Path) -> None:
    figure, axis = plt.subplots(figsize=(8.5, 4.5))
    depth_um = result.thermal.depth * 1.0e6
    background = float(result.thermal.substrate_doping.concentration_cm3)
    raw_initial_profile = result.concentration_p_cm3[0]
    initial_active_profile = result.initial_active_p_cm3
    initial_inactive_profile = result.initial_inactive_p_cm3
    final_profile = result.concentration_p_cm3[-1]
    initial_active_donor = np.maximum(initial_active_profile - background, 1.0e10)
    final_net_donor_upper_bound = np.maximum(final_profile - background, 1.0e10)
    window_um = _profile_window_um(result)

    if np.max(raw_initial_profile) > 0.0:
        axis.semilogy(
            depth_um,
            np.maximum(raw_initial_profile, 1.0e10),
            color="#5d6d7e",
            lw=1.6,
            ls="--",
            label="Initial total P",
        )
        if np.max(initial_inactive_profile) > 0.0:
            axis.semilogy(
                depth_um,
                np.maximum(initial_inactive_profile, 1.0e10),
                color="#1f618d",
                lw=1.6,
                ls=":",
                label="Initial inactive P",
            )
        axis.semilogy(
            depth_um,
            initial_active_donor,
            color="#7d6608",
            lw=1.6,
            ls="-.",
            label="Initial active donor estimate",
        )

    axis.semilogy(
        depth_um,
        np.maximum(final_profile, 1.0e10),
        color="#117864",
        lw=2.0,
        label="Final total P",
    )
    axis.semilogy(
        depth_um,
        final_net_donor_upper_bound,
        color="#ca6f1e",
        lw=1.9,
        ls=(0, (6, 2)),
        label="Final chemical net donor upper bound",
    )
    axis.axhline(background, color="#cb4335", ls="--", lw=1.3, label="Ga background")
    axis.set_xlim(0.0, window_um)
    axis.set_xlabel("Depth in Si (um)")
    axis.set_ylabel("Concentration (cm^-3)")
    axis.set_title("Silicon P Profile for Sheet-Dose / Sheet-Resistance Analysis")
    axis.grid(alpha=0.25)
    axis.legend()
    figure.tight_layout()
    figure.savefig(path, dpi=200)
    plt.close(figure)


def _plot_cumulative_sheet_dose(result: DiffusionResult, path: Path) -> None:
    figure, axis = plt.subplots(figsize=(8.5, 4.5))
    depth_um = result.thermal.depth * 1.0e6
    depth_cm = result.thermal.depth * 1.0e2
    background = float(result.thermal.substrate_doping.concentration_cm3)
    initial_profile = result.concentration_p_cm3[0]
    initial_active_profile = result.initial_active_p_cm3
    initial_inactive_profile = result.initial_inactive_p_cm3
    final_profile = result.concentration_p_cm3[-1]
    initial_active_donor = np.maximum(initial_active_profile - background, 0.0)
    final_net_donor_upper_bound = np.maximum(final_profile - background, 0.0)
    aligned_depth_cm, aligned_initial_profile = _surface_aligned_profile(depth_cm, initial_profile)
    _, aligned_initial_inactive_profile = _surface_aligned_profile(depth_cm, initial_inactive_profile)
    _, aligned_final_profile = _surface_aligned_profile(depth_cm, final_profile)
    _, aligned_initial_active_donor = _surface_aligned_profile(depth_cm, initial_active_donor)
    _, aligned_final_net_donor = _surface_aligned_profile(depth_cm, final_net_donor_upper_bound)
    aligned_depth_um = aligned_depth_cm * 1.0e4
    initial_cumulative = np.concatenate(([0.0], cumulative_trapezoid(aligned_initial_profile, aligned_depth_cm)))
    initial_inactive_cumulative = np.concatenate(
        ([0.0], cumulative_trapezoid(aligned_initial_inactive_profile, aligned_depth_cm))
    )
    final_cumulative = np.concatenate(([0.0], cumulative_trapezoid(aligned_final_profile, aligned_depth_cm)))
    initial_net_cumulative = np.concatenate(([0.0], cumulative_trapezoid(aligned_initial_active_donor, aligned_depth_cm)))
    final_net_cumulative = np.concatenate(([0.0], cumulative_trapezoid(aligned_final_net_donor, aligned_depth_cm)))
    window_um = _profile_window_um(result)

    if np.max(initial_profile) > 0.0:
        axis.plot(
            aligned_depth_um,
            initial_cumulative,
            color="#5d6d7e",
            lw=1.6,
            ls="--",
            label="Initial cumulative total P",
        )
        if np.max(initial_inactive_profile) > 0.0:
            axis.plot(
                aligned_depth_um,
                initial_inactive_cumulative,
                color="#1f618d",
                lw=1.5,
                ls=":",
                label="Initial cumulative inactive P",
            )
        axis.plot(
            aligned_depth_um,
            initial_net_cumulative,
            color="#7d6608",
            lw=1.6,
            ls="-.",
            label="Initial cumulative active donor",
        )
    axis.plot(aligned_depth_um, final_cumulative, color="#117864", lw=2.0, label="Final cumulative total P")
    axis.plot(
        aligned_depth_um,
        final_net_cumulative,
        color="#ca6f1e",
        lw=1.9,
        ls=(0, (6, 2)),
        label="Final cumulative chemical net donor upper bound",
    )
    axis.set_xlim(0.0, window_um)
    axis.set_xlabel("Depth in Si (um)")
    axis.set_ylabel("Integrated dose from surface to depth (cm^-2)")
    axis.set_title("Cumulative P Dose in Silicon")
    axis.grid(alpha=0.25)
    axis.legend()
    figure.tight_layout()
    figure.savefig(path, dpi=200)
    plt.close(figure)


def _save_profile_analysis_table(result: DiffusionResult, path: Path) -> None:
    depth_um = result.thermal.depth * 1.0e6
    depth_nm = result.thermal.depth * 1.0e9
    depth_cm = result.thermal.depth * 1.0e2
    background = float(result.thermal.substrate_doping.concentration_cm3)
    initial_profile = result.concentration_p_cm3[0]
    initial_active_profile = result.initial_active_p_cm3
    initial_inactive_profile = result.initial_inactive_p_cm3
    final_profile = result.concentration_p_cm3[-1]
    initial_active_donor = np.maximum(initial_active_profile - background, 0.0)
    initial_chemical_net_donor = np.maximum(initial_profile - background, 0.0)
    final_net_donor = np.maximum(final_profile - background, 0.0)
    aligned_depth_cm, aligned_initial_profile = _surface_aligned_profile(depth_cm, initial_profile)
    _, aligned_initial_active_profile = _surface_aligned_profile(depth_cm, initial_active_profile)
    _, aligned_initial_inactive_profile = _surface_aligned_profile(depth_cm, initial_inactive_profile)
    _, aligned_final_profile = _surface_aligned_profile(depth_cm, final_profile)
    _, aligned_initial_active_donor = _surface_aligned_profile(depth_cm, initial_active_donor)
    _, aligned_initial_chemical_net_donor = _surface_aligned_profile(depth_cm, initial_chemical_net_donor)
    _, aligned_final_net_donor = _surface_aligned_profile(depth_cm, final_net_donor)
    aligned_depth_um = aligned_depth_cm * 1.0e4
    aligned_depth_nm = aligned_depth_cm * 1.0e7
    initial_cumulative = np.concatenate(([0.0], cumulative_trapezoid(aligned_initial_profile, aligned_depth_cm)))
    final_cumulative = np.concatenate(([0.0], cumulative_trapezoid(aligned_final_profile, aligned_depth_cm)))
    initial_active_cumulative = np.concatenate(
        ([0.0], cumulative_trapezoid(aligned_initial_active_donor, aligned_depth_cm))
    )
    initial_inactive_cumulative = np.concatenate(
        ([0.0], cumulative_trapezoid(aligned_initial_inactive_profile, aligned_depth_cm))
    )
    initial_chemical_net_cumulative = np.concatenate(
        ([0.0], cumulative_trapezoid(aligned_initial_chemical_net_donor, aligned_depth_cm))
    )
    final_net_cumulative = np.concatenate(([0.0], cumulative_trapezoid(aligned_final_net_donor, aligned_depth_cm)))

    data = np.column_stack(
        [
            aligned_depth_um,
            aligned_depth_nm,
            aligned_initial_profile,
            aligned_initial_active_profile,
            aligned_initial_inactive_profile,
            aligned_final_profile,
            aligned_initial_active_donor,
            aligned_initial_chemical_net_donor,
            aligned_final_net_donor,
            initial_cumulative,
            final_cumulative,
            initial_active_cumulative,
            initial_inactive_cumulative,
            initial_chemical_net_cumulative,
            final_net_cumulative,
        ]
    )
    np.savetxt(
        path,
        data,
        delimiter=",",
        header=(
            "depth_um,depth_nm,initial_total_p_cm3,initial_active_p_cm3,initial_inactive_p_cm3,final_total_p_cm3,"
            "initial_active_donor_cm3,initial_chemical_net_donor_cm3,final_chemical_net_donor_upper_bound_cm3,"
            "initial_cumulative_total_p_cm2,final_cumulative_total_p_cm2,"
            "initial_cumulative_active_donor_cm2,initial_cumulative_inactive_p_cm2,"
            "initial_cumulative_chemical_net_donor_cm2,final_cumulative_chemical_net_donor_upper_bound_cm2"
        ),
        comments="",
    )
