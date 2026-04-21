from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from scipy.linalg.lapack import dgtsv

from .phase1_thermal import (
    Domain1D,
    LaserPulse,
    MaterialProperties,
    SimulationResult,
    SubstrateDoping,
    SurfaceSourceLayer,
    apparent_heat_capacity,
    gaussian_flux,
    liquid_fraction as silicon_liquid_fraction,
    thermal_conductivity as silicon_thermal_conductivity,
    validate_doping_inputs,
)


@dataclass(slots=True)
class PSGLayerProperties:
    rho: float = 2200.0
    cp: float = 730.0
    k: float = 1.4
    thickness: float = 150.0e-9
    matrix_material: str = "SiO2"
    dopant_oxide: str = "P2O5"
    model_description: str = (
        "Phosphosilicate glass is approximated as a phosphorus-rich SiO2 layer with silica-like thermal properties."
    )


@dataclass(slots=True)
class StackOpticalProperties:
    surface_reflectance: float = 0.05
    texture_reflectance_multiplier: float = 1.0
    interface_transmission: float = 0.68
    psg_absorption_depth: float = 50.0e-6
    si_absorption_depth: float = 1274.0e-9


@dataclass(slots=True)
class StackDomain1D:
    silicon_thickness: float = 8.0e-6
    nz: int = 600
    dt: float = 0.2e-9
    t_end: float = 150.0e-9
    ambient_temp: float = 300.0
    bottom_bc: str = "dirichlet"


@dataclass(slots=True)
class StackSimulationResult:
    time: np.ndarray
    depth: np.ndarray
    temperature: np.ndarray
    liquid_fraction: np.ndarray
    melt_depth: np.ndarray
    laser_flux: np.ndarray
    surface_source: SurfaceSourceLayer
    substrate_doping: SubstrateDoping
    silicon_material: MaterialProperties
    psg_material: PSGLayerProperties
    optics: StackOpticalProperties
    pulse: LaserPulse
    domain: StackDomain1D


def _harmonic_mean(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    denominator = left + right
    mean = np.zeros_like(left)
    nonzero = denominator > 0.0
    mean[nonzero] = 2.0 * left[nonzero] * right[nonzero] / denominator[nonzero]
    return mean


def _total_thickness(domain: StackDomain1D, psg: PSGLayerProperties) -> float:
    return domain.silicon_thickness + psg.thickness


def _psg_mask(depth: np.ndarray, psg: PSGLayerProperties) -> np.ndarray:
    return depth < psg.thickness


def _stack_masks(depth: np.ndarray, psg: PSGLayerProperties) -> tuple[np.ndarray, np.ndarray]:
    psg_mask = _psg_mask(depth, psg)
    return psg_mask, ~psg_mask


def effective_surface_reflectance(optics: StackOpticalProperties) -> float:
    return float(np.clip(optics.surface_reflectance * optics.texture_reflectance_multiplier, 0.0, 0.999999))


def _stack_liquid_fraction(
    temperature: np.ndarray,
    silicon_mask: np.ndarray,
    silicon_material: MaterialProperties,
) -> np.ndarray:
    fraction = np.zeros_like(temperature)
    if np.any(silicon_mask):
        fraction[silicon_mask] = silicon_liquid_fraction(temperature[silicon_mask], silicon_material)
    return fraction


def _stack_apparent_heat_capacity(
    temperature: np.ndarray,
    silicon_mask: np.ndarray,
    silicon_material: MaterialProperties,
    psg: PSGLayerProperties,
) -> np.ndarray:
    cp = np.full_like(temperature, psg.cp, dtype=float)
    if np.any(silicon_mask):
        cp[silicon_mask] = apparent_heat_capacity(temperature[silicon_mask], silicon_material)
    return cp


def _stack_thermal_conductivity(
    temperature: np.ndarray,
    silicon_mask: np.ndarray,
    silicon_material: MaterialProperties,
    psg: PSGLayerProperties,
) -> np.ndarray:
    conductivity = np.full_like(temperature, psg.k, dtype=float)
    if np.any(silicon_mask):
        conductivity[silicon_mask] = silicon_thermal_conductivity(temperature[silicon_mask], silicon_material)
    return conductivity


def _stack_density(silicon_mask: np.ndarray, silicon_material: MaterialProperties, psg: PSGLayerProperties) -> np.ndarray:
    density = np.full(silicon_mask.shape, psg.rho, dtype=float)
    density[silicon_mask] = silicon_material.rho
    return density


def _stack_heat_source_profile(
    depth: np.ndarray,
    optics: StackOpticalProperties,
    psg: PSGLayerProperties,
    psg_mask: np.ndarray,
    silicon_mask: np.ndarray,
) -> np.ndarray:
    source = np.zeros_like(depth)

    if psg.thickness > 0.0 and optics.psg_absorption_depth > 0.0 and np.any(psg_mask):
        source[psg_mask] = (
            1.0
            / optics.psg_absorption_depth
            * np.exp(-depth[psg_mask] / optics.psg_absorption_depth)
        )
        transmitted_to_si = (
            np.exp(-psg.thickness / optics.psg_absorption_depth) * optics.interface_transmission
        )
    else:
        transmitted_to_si = optics.interface_transmission

    if optics.si_absorption_depth > 0.0 and np.any(silicon_mask):
        silicon_depth = depth[silicon_mask] - psg.thickness
        source[silicon_mask] = (
            transmitted_to_si
            / optics.si_absorption_depth
            * np.exp(-silicon_depth / optics.si_absorption_depth)
        )

    return source


def layered_volumetric_heat_source(
    depth: np.ndarray,
    time_value: float,
    pulse: LaserPulse,
    optics: StackOpticalProperties,
    psg: PSGLayerProperties,
) -> np.ndarray:
    flux_value = gaussian_flux(np.array([time_value]), pulse)[0]
    psg_mask, silicon_mask = _stack_masks(depth, psg)
    source_profile = _stack_heat_source_profile(depth, optics, psg, psg_mask, silicon_mask)
    return (1.0 - effective_surface_reflectance(optics)) * flux_value * source_profile


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


def _assemble_matrix(
    temperature_iter: np.ndarray,
    temperature_prev: np.ndarray,
    source_term: np.ndarray,
    domain: StackDomain1D,
    silicon_material: MaterialProperties,
    psg: PSGLayerProperties,
    silicon_mask: np.ndarray,
    density: np.ndarray,
    dz: float,
) -> tuple:
    n = temperature_iter.size

    cp = _stack_apparent_heat_capacity(temperature_iter, silicon_mask, silicon_material, psg)
    capacity = density * cp / domain.dt
    conductivity = _stack_thermal_conductivity(temperature_iter, silicon_mask, silicon_material, psg)
    coeff = _harmonic_mean(conductivity[:-1], conductivity[1:]) / dz**2

    if domain.bottom_bc == "dirichlet":
        active = n - 1
        lower = np.empty(active - 1, dtype=float)
        diag = np.empty(active, dtype=float)
        upper = np.empty(active - 1, dtype=float)
        rhs = capacity[:active] * temperature_prev[:active] + source_term[:active]

        diag[0] = capacity[0] + 2.0 * coeff[0]
        upper[0] = -2.0 * coeff[0]
        if active > 1:
            diag[1:] = capacity[1:active] + coeff[: active - 1] + coeff[1:active]
            lower[:] = -coeff[: active - 1]
            if active > 2:
                upper[1:] = -coeff[1 : active - 1]
            rhs[-1] += coeff[active - 1] * domain.ambient_temp

        return lower, diag, upper, rhs

    if domain.bottom_bc == "neumann":
        lower = np.empty(n - 1, dtype=float)
        diag = np.empty(n, dtype=float)
        upper = np.empty(n - 1, dtype=float)
        rhs = capacity * temperature_prev + source_term

        diag[0] = capacity[0] + 2.0 * coeff[0]
        upper[0] = -2.0 * coeff[0]
        if n > 2:
            diag[1:-1] = capacity[1:-1] + coeff[:-1] + coeff[1:]
            lower[:-1] = -coeff[:-1]
            upper[1:] = -coeff[1:]
        diag[-1] = capacity[-1] + 2.0 * coeff[-1]
        lower[-1] = -2.0 * coeff[-1]

        return lower, diag, upper, rhs

    raise ValueError(f"Unsupported bottom boundary condition: {domain.bottom_bc}")


def run_stack_simulation(
    domain: StackDomain1D,
    silicon_material: MaterialProperties,
    psg_material: PSGLayerProperties,
    pulse: LaserPulse,
    optics: StackOpticalProperties,
    surface_source: SurfaceSourceLayer | None = None,
    substrate_doping: SubstrateDoping | None = None,
    initial_temperature_profile_k: np.ndarray | None = None,
    max_iterations: int = 10,
    tolerance: float = 1.0e-6,
) -> StackSimulationResult:
    if surface_source is None:
        surface_source = SurfaceSourceLayer()
    if substrate_doping is None:
        substrate_doping = SubstrateDoping()

    validate_doping_inputs(surface_source, substrate_doping)

    total_thickness = _total_thickness(domain, psg_material)
    depth = np.linspace(0.0, total_thickness, domain.nz)
    time = np.arange(0.0, domain.t_end + domain.dt, domain.dt)
    dz = depth[1] - depth[0]
    psg_mask, silicon_mask = _stack_masks(depth, psg_material)
    silicon_depth = depth[silicon_mask] - psg_material.thickness
    density = _stack_density(silicon_mask, silicon_material, psg_material)
    incident_after_reflection_scale = 1.0 - effective_surface_reflectance(optics)
    source_profile = _stack_heat_source_profile(depth, optics, psg_material, psg_mask, silicon_mask)

    temperature = np.zeros((time.size, depth.size))
    if initial_temperature_profile_k is None:
        temperature[0, :] = domain.ambient_temp
    else:
        initial_temperature = np.asarray(initial_temperature_profile_k, dtype=float)
        if initial_temperature.shape != depth.shape:
            raise ValueError(
                "initial_temperature_profile_k must match the stack depth grid shape "
                f"{depth.shape}, got {initial_temperature.shape}."
            )
        temperature[0, :] = initial_temperature
        if domain.bottom_bc == "dirichlet":
            temperature[0, -1] = domain.ambient_temp
    liquid = np.zeros_like(temperature)
    melt_depth = np.zeros(time.size)
    flux_history = gaussian_flux(time, pulse)

    for step in range(1, time.size):
        prev = temperature[step - 1].copy()
        current = prev.copy()
        source_term = incident_after_reflection_scale * flux_history[step] * source_profile

        for _ in range(max_iterations):
            lower, diag, upper, rhs = _assemble_matrix(
                current,
                prev,
                source_term,
                domain,
                silicon_material,
                psg_material,
                silicon_mask,
                density,
                dz,
            )
            solved = _solve_tridiagonal(lower, diag, upper, rhs)
            if domain.bottom_bc == "dirichlet":
                updated = np.empty_like(current)
                updated[:-1] = solved
                updated[-1] = domain.ambient_temp
            else:
                updated = solved
            if np.max(np.abs(updated - current)) < tolerance:
                current = updated
                break
            current = updated

        temperature[step] = current
        liquid[step] = _stack_liquid_fraction(current, silicon_mask, silicon_material)
        melted = np.flatnonzero(liquid[step, silicon_mask] > 0.5)
        if melted.size:
            melt_depth[step] = silicon_depth[melted[-1]]

    liquid[0] = _stack_liquid_fraction(temperature[0], silicon_mask, silicon_material)

    return StackSimulationResult(
        time=time,
        depth=depth,
        temperature=temperature,
        liquid_fraction=liquid,
        melt_depth=melt_depth,
        laser_flux=flux_history,
        surface_source=surface_source,
        substrate_doping=substrate_doping,
        silicon_material=silicon_material,
        psg_material=psg_material,
        optics=optics,
        pulse=pulse,
        domain=domain,
    )


def silicon_subdomain_view(result: StackSimulationResult) -> SimulationResult:
    silicon_mask = ~_psg_mask(result.depth, result.psg_material)
    silicon_depth = result.depth[silicon_mask] - result.psg_material.thickness
    domain = Domain1D(
        thickness=result.domain.silicon_thickness,
        nz=silicon_depth.size,
        dt=result.domain.dt,
        t_end=result.domain.t_end,
        ambient_temp=result.domain.ambient_temp,
        bottom_bc=result.domain.bottom_bc,
    )
    return SimulationResult(
        time=result.time,
        depth=silicon_depth,
        temperature=result.temperature[:, silicon_mask],
        liquid_fraction=result.liquid_fraction[:, silicon_mask],
        melt_depth=result.melt_depth,
        laser_flux=result.laser_flux,
        surface_source=result.surface_source,
        substrate_doping=result.substrate_doping,
        material=result.silicon_material,
        pulse=result.pulse,
        domain=domain,
    )


def _optical_summary(result: StackSimulationResult) -> dict:
    optics = result.optics
    psg = result.psg_material
    effective_reflectance = effective_surface_reflectance(optics)
    psg_fraction = (1.0 - effective_reflectance) * (
        1.0 - np.exp(-psg.thickness / optics.psg_absorption_depth)
    )
    si_fraction = (
        (1.0 - effective_reflectance)
        * np.exp(-psg.thickness / optics.psg_absorption_depth)
        * optics.interface_transmission
        * (1.0 - np.exp(-result.domain.silicon_thickness / optics.si_absorption_depth))
    )
    return {
        "flat_surface_reflectance": float(optics.surface_reflectance),
        "texture_reflectance_multiplier": float(optics.texture_reflectance_multiplier),
        "effective_surface_reflectance": effective_reflectance,
        "psg_absorbed_fraction_estimate": float(psg_fraction),
        "si_absorbed_fraction_estimate": float(si_fraction),
        "total_absorbed_fraction_estimate": float(psg_fraction + si_fraction),
        "estimated_unabsorbed_fraction": float(max(0.0, 1.0 - effective_reflectance - psg_fraction - si_fraction)),
        "psg_optical_assumption": (
            "Current Phase 3 treats the PSG as a weakly absorbing P-rich SiO2 layer and keeps the main 532 nm absorption in silicon."
        ),
        "texture_optical_assumption": (
            "Current texture enhancement collapses multi-bounce light trapping into an effective surface-reflectance multiplier."
        ),
    }


def _summary(result: StackSimulationResult) -> dict:
    melted = result.melt_depth > 0.0
    first_melt = float(result.time[melted][0]) if np.any(melted) else None
    last_melt = float(result.time[melted][-1]) if np.any(melted) else None
    silicon_mask = ~_psg_mask(result.depth, result.psg_material)
    peak_si_surface = float(np.max(result.temperature[:, silicon_mask][:, 0]))
    peak_si_surface_liquid_fraction = float(np.max(result.liquid_fraction[:, silicon_mask][:, 0]))
    return {
        "peak_stack_surface_temperature_k": float(np.max(result.temperature[:, 0])),
        "peak_silicon_surface_temperature_k": peak_si_surface,
        "max_melt_depth_m": float(np.max(result.melt_depth)),
        "melt_start_s": first_melt,
        "melt_end_s": last_melt,
        "max_liquid_fraction": float(np.max(result.liquid_fraction)),
        "max_silicon_surface_liquid_fraction": peak_si_surface_liquid_fraction,
        "effective_surface_reflectance": effective_surface_reflectance(result.optics),
        "psg_thickness_m": float(result.psg_material.thickness),
        "silicon_thickness_m": float(result.domain.silicon_thickness),
    }


def save_outputs(result: StackSimulationResult, output_dir: str | Path, fast_output: bool = False) -> Path:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    npz_path = output_path / "phase3_stack_results.npz"
    if fast_output:
        np.savez(
            npz_path,
            time_s=result.time,
            depth_m=result.depth,
            temperature_k=result.temperature,
            liquid_fraction=result.liquid_fraction,
            melt_depth_m=result.melt_depth,
            laser_flux_w_per_m2=result.laser_flux,
        )
    else:
        np.savez_compressed(
            npz_path,
            time_s=result.time,
            depth_m=result.depth,
            temperature_k=result.temperature,
            liquid_fraction=result.liquid_fraction,
            melt_depth_m=result.melt_depth,
            laser_flux_w_per_m2=result.laser_flux,
        )

    summary = {
        "psg_material": asdict(result.psg_material),
        "silicon_material": asdict(result.silicon_material),
        "optics": asdict(result.optics),
        "pulse": asdict(result.pulse),
        "surface_source": asdict(result.surface_source),
        "substrate_doping": asdict(result.substrate_doping),
        "domain": asdict(result.domain),
        "output_mode": "fast" if fast_output else "full",
        "metrics": _summary(result),
        "optical_budget": _optical_summary(result),
    }
    with (output_path / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)

    if not fast_output:
        _plot_temperature_heatmap(result, output_path / "temperature_heatmap.png")
        _plot_liquid_fraction_heatmap(result, output_path / "liquid_fraction_heatmap.png")
        _plot_melt_depth(result, output_path / "melt_depth_vs_time.png")
        _plot_surface_temperature(result, output_path / "surface_temperature.png")
    return output_path


def _plot_temperature_heatmap(result: StackSimulationResult, path: Path) -> None:
    figure, axis = plt.subplots(figsize=(8, 5))
    image = axis.imshow(
        result.temperature.T,
        origin="lower",
        aspect="auto",
        extent=[
            result.time[0] * 1.0e9,
            result.time[-1] * 1.0e9,
            result.depth[0] * 1.0e6,
            result.depth[-1] * 1.0e6,
        ],
        cmap="inferno",
    )
    axis.axhline(result.psg_material.thickness * 1.0e6, color="white", ls="--", lw=1.0)
    axis.set_xlabel("Time (ns)")
    axis.set_ylabel("Depth (um)")
    axis.set_title("PSG/Si Temperature Field")
    colorbar = figure.colorbar(image, ax=axis)
    colorbar.set_label("Temperature (K)")
    figure.tight_layout()
    figure.savefig(path, dpi=200)
    plt.close(figure)


def _plot_liquid_fraction_heatmap(result: StackSimulationResult, path: Path) -> None:
    figure, axis = plt.subplots(figsize=(8, 5))
    image = axis.imshow(
        result.liquid_fraction.T,
        origin="lower",
        aspect="auto",
        extent=[
            result.time[0] * 1.0e9,
            result.time[-1] * 1.0e9,
            result.depth[0] * 1.0e6,
            result.depth[-1] * 1.0e6,
        ],
        cmap="viridis",
        vmin=0.0,
        vmax=1.0,
    )
    axis.axhline(result.psg_material.thickness * 1.0e6, color="white", ls="--", lw=1.0)
    axis.set_xlabel("Time (ns)")
    axis.set_ylabel("Depth (um)")
    axis.set_title("PSG/Si Liquid Fraction")
    colorbar = figure.colorbar(image, ax=axis)
    colorbar.set_label("Liquid Fraction")
    figure.tight_layout()
    figure.savefig(path, dpi=200)
    plt.close(figure)


def _plot_melt_depth(result: StackSimulationResult, path: Path) -> None:
    figure, axis = plt.subplots(figsize=(8, 4))
    axis.plot(result.time * 1.0e9, result.melt_depth * 1.0e9, color="#2874a6", lw=2.0)
    axis.set_xlabel("Time (ns)")
    axis.set_ylabel("Silicon Melt Depth (nm)")
    axis.set_title("Silicon Melt Depth vs Time")
    axis.grid(alpha=0.25)
    figure.tight_layout()
    figure.savefig(path, dpi=200)
    plt.close(figure)


def _plot_surface_temperature(result: StackSimulationResult, path: Path) -> None:
    silicon_mask = ~_psg_mask(result.depth, result.psg_material)
    figure, axis = plt.subplots(figsize=(8, 4))
    axis.plot(
        result.time * 1.0e9,
        result.temperature[:, 0],
        color="#c0392b",
        lw=2.0,
        label="Stack surface",
    )
    axis.plot(
        result.time * 1.0e9,
        result.temperature[:, silicon_mask][:, 0],
        color="#1e8449",
        lw=2.0,
        label="Silicon surface",
    )
    axis.axhline(result.silicon_material.melt_temp, color="black", ls="--", lw=1.2, label="Si melt temp")
    axis.set_xlabel("Time (ns)")
    axis.set_ylabel("Temperature (K)")
    axis.set_title("Surface Temperature History")
    axis.grid(alpha=0.25)
    axis.legend()
    figure.tight_layout()
    figure.savefig(path, dpi=200)
    plt.close(figure)
