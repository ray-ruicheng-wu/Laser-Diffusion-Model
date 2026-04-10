from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from scipy.sparse import diags
from scipy.sparse.linalg import spsolve


MAX_CONCENTRATION_CM3 = 4.991e22


@dataclass(slots=True)
class MaterialProperties:
    rho: float = 2330.0
    cp_solid: float = 700.0
    cp_liquid: float = 1000.0
    k_solid: float = 90.0
    k_liquid: float = 55.0
    latent_heat: float = 1.8e6
    melt_temp: float = 1687.0
    mushy_width: float = 20.0


@dataclass(slots=True)
class LaserPulse:
    fluence: float = 0.55 * 1.0e4
    pulse_fwhm: float = 10.0e-9
    peak_time: float = 30.0e-9
    absorptivity: float = 0.72
    absorption_depth: float = 80.0e-9


@dataclass(slots=True)
class SurfaceSourceLayer:
    kind: str = "PSG"
    dopant: str = "P"
    dopant_concentration_cm3: float = 2.0e21
    notes: str = "Phase 2 source layer placeholder; not coupled into the Phase 1 thermal solve."


@dataclass(slots=True)
class SubstrateDoping:
    species: str = "Ga"
    concentration_cm3: float = 1.0e16
    notes: str = "Background substrate doping placeholder; not coupled into the Phase 1 thermal solve."


@dataclass(slots=True)
class Domain1D:
    thickness: float = 8.0e-6
    nz: int = 500
    dt: float = 0.2e-9
    t_end: float = 150.0e-9
    ambient_temp: float = 300.0
    bottom_bc: str = "dirichlet"


@dataclass(slots=True)
class SimulationResult:
    time: np.ndarray
    depth: np.ndarray
    temperature: np.ndarray
    liquid_fraction: np.ndarray
    melt_depth: np.ndarray
    laser_flux: np.ndarray
    surface_source: SurfaceSourceLayer
    substrate_doping: SubstrateDoping
    material: MaterialProperties
    pulse: LaserPulse
    domain: Domain1D


def _validate_positive_concentration(name: str, value_cm3: float) -> None:
    if value_cm3 < 0.0:
        raise ValueError(f"{name} must be non-negative, got {value_cm3:.3e} cm^-3.")
    if value_cm3 > MAX_CONCENTRATION_CM3:
        raise ValueError(
            f"{name}={value_cm3:.3e} cm^-3 exceeds the current sanity limit of "
            f"{MAX_CONCENTRATION_CM3:.3e} cm^-3."
        )


def validate_doping_inputs(
    surface_source: SurfaceSourceLayer,
    substrate_doping: SubstrateDoping,
) -> None:
    _validate_positive_concentration(
        f"{surface_source.kind} {surface_source.dopant} concentration",
        surface_source.dopant_concentration_cm3,
    )
    _validate_positive_concentration(
        f"Si substrate {substrate_doping.species} concentration",
        substrate_doping.concentration_cm3,
    )


def liquid_fraction(temperature: np.ndarray, material: MaterialProperties) -> np.ndarray:
    solidus = material.melt_temp - 0.5 * material.mushy_width
    liquidus = material.melt_temp + 0.5 * material.mushy_width
    fraction = np.zeros_like(temperature)
    fraction[temperature >= liquidus] = 1.0
    mushy = (temperature > solidus) & (temperature < liquidus)
    fraction[mushy] = (temperature[mushy] - solidus) / material.mushy_width
    return fraction


def apparent_heat_capacity(temperature: np.ndarray, material: MaterialProperties) -> np.ndarray:
    fraction = liquid_fraction(temperature, material)
    cp_base = material.cp_solid * (1.0 - fraction) + material.cp_liquid * fraction
    solidus = material.melt_temp - 0.5 * material.mushy_width
    liquidus = material.melt_temp + 0.5 * material.mushy_width
    latent_term = np.zeros_like(temperature)
    mushy = (temperature >= solidus) & (temperature <= liquidus)
    latent_term[mushy] = material.latent_heat / material.mushy_width
    return cp_base + latent_term


def thermal_conductivity(temperature: np.ndarray, material: MaterialProperties) -> np.ndarray:
    fraction = liquid_fraction(temperature, material)
    return material.k_solid * (1.0 - fraction) + material.k_liquid * fraction


def gaussian_flux(time: np.ndarray, pulse: LaserPulse) -> np.ndarray:
    sigma = pulse.pulse_fwhm / (2.0 * np.sqrt(2.0 * np.log(2.0)))
    prefactor = pulse.fluence / (sigma * np.sqrt(2.0 * np.pi))
    return prefactor * np.exp(-0.5 * ((time - pulse.peak_time) / sigma) ** 2)


def volumetric_heat_source(depth: np.ndarray, time_value: float, pulse: LaserPulse) -> np.ndarray:
    flux_value = gaussian_flux(np.array([time_value]), pulse)[0]
    absorption = pulse.absorptivity * flux_value / pulse.absorption_depth
    return absorption * np.exp(-depth / pulse.absorption_depth)


def _assemble_matrix(
    temperature_iter: np.ndarray,
    temperature_prev: np.ndarray,
    source_term: np.ndarray,
    domain: Domain1D,
    material: MaterialProperties,
) -> tuple:
    n = domain.nz
    dz = domain.thickness / (n - 1)

    capacity = material.rho * apparent_heat_capacity(temperature_iter, material) / domain.dt
    conductivity = thermal_conductivity(temperature_iter, material)
    interface_k = 0.5 * (conductivity[:-1] + conductivity[1:])

    if domain.bottom_bc == "dirichlet":
        active = n - 1
        lower = np.zeros(active - 1)
        diag = np.zeros(active)
        upper = np.zeros(active - 1)
        rhs = capacity[:active] * temperature_prev[:active] + source_term[:active]

        diag[0] = capacity[0] + 2.0 * interface_k[0] / dz**2
        upper[0] = -2.0 * interface_k[0] / dz**2

        for idx in range(1, active):
            west = interface_k[idx - 1] / dz**2
            east = interface_k[idx] / dz**2 if idx < n - 1 else 0.0
            diag[idx] = capacity[idx] + west + east
            lower[idx - 1] = -west
            if idx < active - 1:
                upper[idx] = -east
            else:
                rhs[idx] += east * domain.ambient_temp

        matrix = diags(
            diagonals=[lower, diag, upper],
            offsets=[-1, 0, 1],
            shape=(active, active),
            format="csc",
        )
        return matrix, rhs

    if domain.bottom_bc == "neumann":
        lower = np.zeros(n - 1)
        diag = np.zeros(n)
        upper = np.zeros(n - 1)
        rhs = capacity * temperature_prev + source_term

        diag[0] = capacity[0] + 2.0 * interface_k[0] / dz**2
        upper[0] = -2.0 * interface_k[0] / dz**2

        for idx in range(1, n - 1):
            west = interface_k[idx - 1] / dz**2
            east = interface_k[idx] / dz**2
            diag[idx] = capacity[idx] + west + east
            lower[idx - 1] = -west
            upper[idx] = -east

        diag[-1] = capacity[-1] + 2.0 * interface_k[-1] / dz**2
        lower[-1] = -2.0 * interface_k[-1] / dz**2

        matrix = diags(
            diagonals=[lower, diag, upper],
            offsets=[-1, 0, 1],
            shape=(n, n),
            format="csc",
        )
        return matrix, rhs

    raise ValueError(f"Unsupported bottom boundary condition: {domain.bottom_bc}")


def run_simulation(
    domain: Domain1D,
    material: MaterialProperties,
    pulse: LaserPulse,
    surface_source: SurfaceSourceLayer | None = None,
    substrate_doping: SubstrateDoping | None = None,
    max_iterations: int = 10,
    tolerance: float = 1.0e-6,
) -> SimulationResult:
    if surface_source is None:
        surface_source = SurfaceSourceLayer()
    if substrate_doping is None:
        substrate_doping = SubstrateDoping()

    validate_doping_inputs(surface_source, substrate_doping)

    depth = np.linspace(0.0, domain.thickness, domain.nz)
    time = np.arange(0.0, domain.t_end + domain.dt, domain.dt)

    temperature = np.zeros((time.size, depth.size))
    temperature[0, :] = domain.ambient_temp
    liquid = np.zeros_like(temperature)
    melt_depth = np.zeros(time.size)
    flux_history = gaussian_flux(time, pulse)

    for step in range(1, time.size):
        prev = temperature[step - 1].copy()
        current = prev.copy()
        source_term = volumetric_heat_source(depth, time[step], pulse)

        for _ in range(max_iterations):
            matrix, rhs = _assemble_matrix(current, prev, source_term, domain, material)
            solved = spsolve(matrix, rhs)
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
        liquid[step] = liquid_fraction(current, material)
        melted = np.flatnonzero(liquid[step] > 0.5)
        melt_depth[step] = depth[melted[-1]] if melted.size else 0.0

    liquid[0] = liquid_fraction(temperature[0], material)

    return SimulationResult(
        time=time,
        depth=depth,
        temperature=temperature,
        liquid_fraction=liquid,
        melt_depth=melt_depth,
        laser_flux=flux_history,
        surface_source=surface_source,
        substrate_doping=substrate_doping,
        material=material,
        pulse=pulse,
        domain=domain,
    )


def _summary(result: SimulationResult) -> dict:
    melted = result.melt_depth > 0.0
    first_melt = float(result.time[melted][0]) if np.any(melted) else None
    last_melt = float(result.time[melted][-1]) if np.any(melted) else None
    return {
        "peak_surface_temperature_k": float(np.max(result.temperature[:, 0])),
        "max_melt_depth_m": float(np.max(result.melt_depth)),
        "melt_start_s": first_melt,
        "melt_end_s": last_melt,
        "max_liquid_fraction": float(np.max(result.liquid_fraction)),
        "fluence_j_per_m2": float(result.pulse.fluence),
        "pulse_fwhm_s": float(result.pulse.pulse_fwhm),
        "absorption_depth_m": float(result.pulse.absorption_depth),
        "time_steps": int(result.time.size),
        "grid_points": int(result.depth.size),
    }


def save_outputs(result: SimulationResult, output_dir: str | Path) -> Path:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    np.savez_compressed(
        output_path / "phase1_results.npz",
        time_s=result.time,
        depth_m=result.depth,
        temperature_k=result.temperature,
        liquid_fraction=result.liquid_fraction,
        melt_depth_m=result.melt_depth,
        laser_flux_w_per_m2=result.laser_flux,
    )

    summary = {
        "material": asdict(result.material),
        "pulse": asdict(result.pulse),
        "surface_source": asdict(result.surface_source),
        "substrate_doping": asdict(result.substrate_doping),
        "domain": asdict(result.domain),
        "metrics": _summary(result),
        "limits": {
            "max_concentration_cm3": MAX_CONCENTRATION_CM3,
            "notes": (
                "Sanity ceiling used to avoid non-physical concentration inputs before a "
                "material-specific solubility model is introduced."
            ),
        },
    }
    with (output_path / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)

    _plot_temperature_heatmap(result, output_path / "temperature_heatmap.png")
    _plot_liquid_fraction_heatmap(result, output_path / "liquid_fraction_heatmap.png")
    _plot_melt_depth(result, output_path / "melt_depth_vs_time.png")
    _plot_surface_temperature(result, output_path / "surface_temperature.png")
    return output_path


def _plot_temperature_heatmap(result: SimulationResult, path: Path) -> None:
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
    axis.set_xlabel("Time (ns)")
    axis.set_ylabel("Depth (um)")
    axis.set_title("Temperature Field")
    colorbar = figure.colorbar(image, ax=axis)
    colorbar.set_label("Temperature (K)")
    figure.tight_layout()
    figure.savefig(path, dpi=200)
    plt.close(figure)


def _plot_liquid_fraction_heatmap(result: SimulationResult, path: Path) -> None:
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
    axis.set_xlabel("Time (ns)")
    axis.set_ylabel("Depth (um)")
    axis.set_title("Liquid Fraction")
    colorbar = figure.colorbar(image, ax=axis)
    colorbar.set_label("f_l")
    figure.tight_layout()
    figure.savefig(path, dpi=200)
    plt.close(figure)


def _plot_melt_depth(result: SimulationResult, path: Path) -> None:
    figure, axis = plt.subplots(figsize=(8, 4))
    axis.plot(result.time * 1.0e9, result.melt_depth * 1.0e9, color="#c0392b", lw=2.0)
    axis.set_xlabel("Time (ns)")
    axis.set_ylabel("Melt Depth (nm)")
    axis.set_title("Melt Depth vs Time")
    axis.grid(alpha=0.25)
    figure.tight_layout()
    figure.savefig(path, dpi=200)
    plt.close(figure)


def _plot_surface_temperature(result: SimulationResult, path: Path) -> None:
    figure, axis = plt.subplots(figsize=(8, 4))
    axis.plot(result.time * 1.0e9, result.temperature[:, 0], color="#1f618d", lw=2.0)
    axis.axhline(result.material.melt_temp, color="#7d3c98", ls="--", lw=1.5)
    axis.set_xlabel("Time (ns)")
    axis.set_ylabel("Surface Temperature (K)")
    axis.set_title("Surface Temperature vs Time")
    axis.grid(alpha=0.25)
    figure.tight_layout()
    figure.savefig(path, dpi=200)
    plt.close(figure)
