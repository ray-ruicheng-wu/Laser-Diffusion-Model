from __future__ import annotations

from dataclasses import asdict, dataclass
import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from .phase1_thermal import (
    LaserPulse,
    MaterialProperties,
    SimulationResult,
    SubstrateDoping,
    SurfaceSourceLayer,
)
from .phase2_diffusion import DiffusionParameters, run_diffusion_with_state
from .phase3_stack_thermal import (
    PSGLayerProperties,
    StackDomain1D,
    StackOpticalProperties,
    StackSimulationResult,
    run_stack_simulation,
    silicon_subdomain_view,
)


@dataclass(slots=True)
class MultiShotParameters:
    shot_count: int = 1
    source_replenishment_mode: str = "carry"
    thermal_history_mode: str = "reuse_single_pulse"
    notes: str = (
        "Phase 4 multi-shot V1 reuses the same single-pulse thermal history for each shot and carries forward "
        "chemical state and, by default, the remaining source inventory."
    )


@dataclass(slots=True)
class MultiShotResult:
    thermal: SimulationResult
    diffusion_parameters: DiffusionParameters
    multishot_parameters: MultiShotParameters
    shot_index: np.ndarray
    per_shot_final_total_p_cm3: np.ndarray
    per_shot_final_active_origin_p_cm3: np.ndarray
    per_shot_final_inactive_origin_p_cm3: np.ndarray
    per_shot_final_injected_origin_p_cm3: np.ndarray
    per_shot_final_junction_depth_m: np.ndarray
    per_shot_peak_p_cm3: np.ndarray
    per_shot_injected_dose_cm2: np.ndarray
    per_shot_cumulative_injected_dose_cm2: np.ndarray
    per_shot_remaining_source_inventory_atoms_m2: np.ndarray
    per_shot_peak_surface_injection_flux_atoms_m2_s: np.ndarray
    per_shot_source_depletion_fraction: np.ndarray
    last_stack_thermal: StackSimulationResult | None = None
    per_shot_initial_silicon_surface_temperature_k: np.ndarray | None = None
    per_shot_peak_silicon_surface_temperature_k: np.ndarray | None = None
    per_shot_cycle_end_silicon_surface_temperature_k: np.ndarray | None = None
    per_shot_max_melt_depth_m: np.ndarray | None = None
    per_shot_max_liquid_fraction: np.ndarray | None = None


def _validate_multishot_parameters(multishot_params: MultiShotParameters) -> None:
    if multishot_params.shot_count <= 0:
        raise ValueError("shot_count must be positive.")
    if multishot_params.source_replenishment_mode not in {"carry", "reset_each_shot"}:
        raise ValueError(
            "source_replenishment_mode must be one of: carry, reset_each_shot"
        )
    if multishot_params.thermal_history_mode not in {"reuse_single_pulse", "accumulate"}:
        raise ValueError(
            "thermal_history_mode must be one of: reuse_single_pulse, accumulate"
        )


def _thermal_metrics(thermal: SimulationResult) -> dict[str, float]:
    return {
        "initial_silicon_surface_temperature_k": float(thermal.temperature[0, 0]),
        "peak_silicon_surface_temperature_k": float(np.max(thermal.temperature[:, 0])),
        "cycle_end_silicon_surface_temperature_k": float(thermal.temperature[-1, 0]),
        "max_melt_depth_m": float(np.max(thermal.melt_depth)),
        "max_liquid_fraction": float(np.max(thermal.liquid_fraction)),
    }


def run_multishot_diffusion(
    thermal: SimulationResult,
    params: DiffusionParameters,
    multishot_params: MultiShotParameters | None = None,
) -> MultiShotResult:
    if multishot_params is None:
        multishot_params = MultiShotParameters()
    _validate_multishot_parameters(multishot_params)
    if multishot_params.thermal_history_mode != "reuse_single_pulse":
        raise ValueError(
            "run_multishot_diffusion only supports thermal_history_mode='reuse_single_pulse'. "
            "Use run_multishot_diffusion_with_thermal_history for accumulate mode."
        )

    shot_count = int(multishot_params.shot_count)
    shot_index = np.arange(1, shot_count + 1, dtype=int)
    depth_size = thermal.depth.size

    total_profiles = np.zeros((shot_count, depth_size), dtype=float)
    active_profiles = np.zeros_like(total_profiles)
    inactive_profiles = np.zeros_like(total_profiles)
    injected_profiles = np.zeros_like(total_profiles)
    junction_depth_m = np.zeros(shot_count, dtype=float)
    peak_p_cm3 = np.zeros(shot_count, dtype=float)
    injected_dose_cm2 = np.zeros(shot_count, dtype=float)
    cumulative_injected_dose_cm2 = np.zeros(shot_count, dtype=float)
    remaining_source_inventory_atoms_m2 = np.zeros(shot_count, dtype=float)
    peak_surface_injection_flux_atoms_m2_s = np.zeros(shot_count, dtype=float)
    source_depletion_fraction = np.zeros(shot_count, dtype=float)
    initial_silicon_surface_temperature_k = np.zeros(shot_count, dtype=float)
    peak_silicon_surface_temperature_k = np.zeros(shot_count, dtype=float)
    cycle_end_silicon_surface_temperature_k = np.zeros(shot_count, dtype=float)
    max_melt_depth_m = np.zeros(shot_count, dtype=float)
    max_liquid_fraction = np.zeros(shot_count, dtype=float)

    current_active_profile_cm3: np.ndarray | None = None
    current_inactive_profile_cm3: np.ndarray | None = None
    current_injected_profile_cm3: np.ndarray | None = None
    current_source_inventory_atoms_m2: float | None = None
    thermal_metrics = _thermal_metrics(thermal)

    for shot_idx in range(shot_count):
        if shot_idx == 0:
            initial_active_profile_cm3 = None
            initial_inactive_profile_cm3 = None
            initial_injected_profile_cm3 = None
            initial_source_inventory_atoms_m2 = None
        else:
            initial_active_profile_cm3 = current_active_profile_cm3
            initial_inactive_profile_cm3 = current_inactive_profile_cm3
            initial_injected_profile_cm3 = current_injected_profile_cm3
            if multishot_params.source_replenishment_mode == "carry":
                initial_source_inventory_atoms_m2 = current_source_inventory_atoms_m2
            else:
                initial_source_inventory_atoms_m2 = None

        shot_result = run_diffusion_with_state(
            thermal=thermal,
            params=params,
            initial_active_p_cm3=initial_active_profile_cm3,
            initial_inactive_p_cm3=initial_inactive_profile_cm3,
            initial_injected_p_cm3=initial_injected_profile_cm3,
            initial_source_inventory_atoms_m2=initial_source_inventory_atoms_m2,
        )
        total_profiles[shot_idx] = shot_result.concentration_p_cm3[-1]
        active_profiles[shot_idx] = (
            shot_result.final_active_origin_p_cm3
            if shot_result.final_active_origin_p_cm3 is not None
            else 0.0
        )
        inactive_profiles[shot_idx] = (
            shot_result.final_inactive_origin_p_cm3
            if shot_result.final_inactive_origin_p_cm3 is not None
            else 0.0
        )
        injected_profiles[shot_idx] = (
            shot_result.final_injected_origin_p_cm3
            if shot_result.final_injected_origin_p_cm3 is not None
            else 0.0
        )
        junction_depth_m[shot_idx] = float(shot_result.junction_depth_m[-1])
        peak_p_cm3[shot_idx] = float(np.max(total_profiles[shot_idx]))

        summary = _shot_summary_dict(shot_result)
        injected_dose_cm2[shot_idx] = float(summary["cumulative_injected_dose_cm2"])
        cumulative_injected_dose_cm2[shot_idx] = float(np.sum(injected_dose_cm2[: shot_idx + 1]))
        remaining_source_inventory_atoms_m2[shot_idx] = float(shot_result.source_inventory_atoms_m2[-1])
        peak_surface_injection_flux_atoms_m2_s[shot_idx] = float(summary["peak_surface_injection_flux_atoms_m2_s"])
        source_depletion_fraction[shot_idx] = float(summary["source_depletion_fraction"])
        initial_silicon_surface_temperature_k[shot_idx] = thermal_metrics["initial_silicon_surface_temperature_k"]
        peak_silicon_surface_temperature_k[shot_idx] = thermal_metrics["peak_silicon_surface_temperature_k"]
        cycle_end_silicon_surface_temperature_k[shot_idx] = thermal_metrics["cycle_end_silicon_surface_temperature_k"]
        max_melt_depth_m[shot_idx] = thermal_metrics["max_melt_depth_m"]
        max_liquid_fraction[shot_idx] = thermal_metrics["max_liquid_fraction"]

        current_active_profile_cm3 = active_profiles[shot_idx].copy()
        current_inactive_profile_cm3 = inactive_profiles[shot_idx].copy()
        current_injected_profile_cm3 = injected_profiles[shot_idx].copy()
        current_source_inventory_atoms_m2 = float(shot_result.source_inventory_atoms_m2[-1])

    return MultiShotResult(
        thermal=thermal,
        diffusion_parameters=params,
        multishot_parameters=multishot_params,
        shot_index=shot_index,
        per_shot_final_total_p_cm3=total_profiles,
        per_shot_final_active_origin_p_cm3=active_profiles,
        per_shot_final_inactive_origin_p_cm3=inactive_profiles,
        per_shot_final_injected_origin_p_cm3=injected_profiles,
        per_shot_final_junction_depth_m=junction_depth_m,
        per_shot_peak_p_cm3=peak_p_cm3,
        per_shot_injected_dose_cm2=injected_dose_cm2,
        per_shot_cumulative_injected_dose_cm2=cumulative_injected_dose_cm2,
        per_shot_remaining_source_inventory_atoms_m2=remaining_source_inventory_atoms_m2,
        per_shot_peak_surface_injection_flux_atoms_m2_s=peak_surface_injection_flux_atoms_m2_s,
        per_shot_source_depletion_fraction=source_depletion_fraction,
        last_stack_thermal=None,
        per_shot_initial_silicon_surface_temperature_k=initial_silicon_surface_temperature_k,
        per_shot_peak_silicon_surface_temperature_k=peak_silicon_surface_temperature_k,
        per_shot_cycle_end_silicon_surface_temperature_k=cycle_end_silicon_surface_temperature_k,
        per_shot_max_melt_depth_m=max_melt_depth_m,
        per_shot_max_liquid_fraction=max_liquid_fraction,
    )


def run_multishot_diffusion_with_thermal_history(
    stack_domain: StackDomain1D,
    silicon_material: MaterialProperties,
    psg_material: PSGLayerProperties,
    pulse: LaserPulse,
    optics: StackOpticalProperties,
    params: DiffusionParameters,
    multishot_params: MultiShotParameters | None = None,
    surface_source: SurfaceSourceLayer | None = None,
    substrate_doping: SubstrateDoping | None = None,
) -> MultiShotResult:
    if multishot_params is None:
        multishot_params = MultiShotParameters(thermal_history_mode="accumulate")
    _validate_multishot_parameters(multishot_params)
    if multishot_params.thermal_history_mode != "accumulate":
        raise ValueError(
            "run_multishot_diffusion_with_thermal_history requires "
            "thermal_history_mode='accumulate'."
        )

    shot_count = int(multishot_params.shot_count)
    shot_index = np.arange(1, shot_count + 1, dtype=int)

    current_stack_temperature_profile_k: np.ndarray | None = None
    current_active_profile_cm3: np.ndarray | None = None
    current_inactive_profile_cm3: np.ndarray | None = None
    current_injected_profile_cm3: np.ndarray | None = None
    current_source_inventory_atoms_m2: float | None = None

    total_profiles: np.ndarray | None = None
    active_profiles: np.ndarray | None = None
    inactive_profiles: np.ndarray | None = None
    injected_profiles: np.ndarray | None = None
    junction_depth_m = np.zeros(shot_count, dtype=float)
    peak_p_cm3 = np.zeros(shot_count, dtype=float)
    injected_dose_cm2 = np.zeros(shot_count, dtype=float)
    cumulative_injected_dose_cm2 = np.zeros(shot_count, dtype=float)
    remaining_source_inventory_atoms_m2 = np.zeros(shot_count, dtype=float)
    peak_surface_injection_flux_atoms_m2_s = np.zeros(shot_count, dtype=float)
    source_depletion_fraction = np.zeros(shot_count, dtype=float)
    initial_silicon_surface_temperature_k = np.zeros(shot_count, dtype=float)
    peak_silicon_surface_temperature_k = np.zeros(shot_count, dtype=float)
    cycle_end_silicon_surface_temperature_k = np.zeros(shot_count, dtype=float)
    max_melt_depth_m = np.zeros(shot_count, dtype=float)
    max_liquid_fraction = np.zeros(shot_count, dtype=float)

    last_silicon_view: SimulationResult | None = None
    last_stack_result: StackSimulationResult | None = None

    for shot_idx in range(shot_count):
        stack_result = run_stack_simulation(
            domain=stack_domain,
            silicon_material=silicon_material,
            psg_material=psg_material,
            pulse=pulse,
            optics=optics,
            surface_source=surface_source,
            substrate_doping=substrate_doping,
            initial_temperature_profile_k=current_stack_temperature_profile_k,
        )
        silicon_view = silicon_subdomain_view(stack_result)
        if total_profiles is None:
            depth_size = silicon_view.depth.size
            total_profiles = np.zeros((shot_count, depth_size), dtype=float)
            active_profiles = np.zeros_like(total_profiles)
            inactive_profiles = np.zeros_like(total_profiles)
            injected_profiles = np.zeros_like(total_profiles)

        if shot_idx == 0:
            initial_active_profile_cm3 = None
            initial_inactive_profile_cm3 = None
            initial_injected_profile_cm3 = None
            initial_source_inventory_atoms_m2 = None
        else:
            initial_active_profile_cm3 = current_active_profile_cm3
            initial_inactive_profile_cm3 = current_inactive_profile_cm3
            initial_injected_profile_cm3 = current_injected_profile_cm3
            if multishot_params.source_replenishment_mode == "carry":
                initial_source_inventory_atoms_m2 = current_source_inventory_atoms_m2
            else:
                initial_source_inventory_atoms_m2 = None

        shot_result = run_diffusion_with_state(
            thermal=silicon_view,
            params=params,
            initial_active_p_cm3=initial_active_profile_cm3,
            initial_inactive_p_cm3=initial_inactive_profile_cm3,
            initial_injected_p_cm3=initial_injected_profile_cm3,
            initial_source_inventory_atoms_m2=initial_source_inventory_atoms_m2,
        )
        total_profiles[shot_idx] = shot_result.concentration_p_cm3[-1]
        active_profiles[shot_idx] = (
            shot_result.final_active_origin_p_cm3
            if shot_result.final_active_origin_p_cm3 is not None
            else 0.0
        )
        inactive_profiles[shot_idx] = (
            shot_result.final_inactive_origin_p_cm3
            if shot_result.final_inactive_origin_p_cm3 is not None
            else 0.0
        )
        injected_profiles[shot_idx] = (
            shot_result.final_injected_origin_p_cm3
            if shot_result.final_injected_origin_p_cm3 is not None
            else 0.0
        )
        junction_depth_m[shot_idx] = float(shot_result.junction_depth_m[-1])
        peak_p_cm3[shot_idx] = float(np.max(total_profiles[shot_idx]))

        summary = _shot_summary_dict(shot_result)
        injected_dose_cm2[shot_idx] = float(summary["cumulative_injected_dose_cm2"])
        cumulative_injected_dose_cm2[shot_idx] = float(np.sum(injected_dose_cm2[: shot_idx + 1]))
        remaining_source_inventory_atoms_m2[shot_idx] = float(shot_result.source_inventory_atoms_m2[-1])
        peak_surface_injection_flux_atoms_m2_s[shot_idx] = float(summary["peak_surface_injection_flux_atoms_m2_s"])
        source_depletion_fraction[shot_idx] = float(summary["source_depletion_fraction"])

        thermal_metrics = _thermal_metrics(silicon_view)
        initial_silicon_surface_temperature_k[shot_idx] = thermal_metrics["initial_silicon_surface_temperature_k"]
        peak_silicon_surface_temperature_k[shot_idx] = thermal_metrics["peak_silicon_surface_temperature_k"]
        cycle_end_silicon_surface_temperature_k[shot_idx] = thermal_metrics["cycle_end_silicon_surface_temperature_k"]
        max_melt_depth_m[shot_idx] = thermal_metrics["max_melt_depth_m"]
        max_liquid_fraction[shot_idx] = thermal_metrics["max_liquid_fraction"]

        current_stack_temperature_profile_k = stack_result.temperature[-1].copy()
        current_active_profile_cm3 = active_profiles[shot_idx].copy()
        current_inactive_profile_cm3 = inactive_profiles[shot_idx].copy()
        current_injected_profile_cm3 = injected_profiles[shot_idx].copy()
        current_source_inventory_atoms_m2 = float(shot_result.source_inventory_atoms_m2[-1])
        last_silicon_view = silicon_view
        last_stack_result = stack_result

    if (
        total_profiles is None
        or active_profiles is None
        or inactive_profiles is None
        or injected_profiles is None
        or last_silicon_view is None
    ):
        raise RuntimeError("Multi-shot thermal-history run did not produce any profiles.")

    return MultiShotResult(
        thermal=last_silicon_view,
        diffusion_parameters=params,
        multishot_parameters=multishot_params,
        shot_index=shot_index,
        per_shot_final_total_p_cm3=total_profiles,
        per_shot_final_active_origin_p_cm3=active_profiles,
        per_shot_final_inactive_origin_p_cm3=inactive_profiles,
        per_shot_final_injected_origin_p_cm3=injected_profiles,
        per_shot_final_junction_depth_m=junction_depth_m,
        per_shot_peak_p_cm3=peak_p_cm3,
        per_shot_injected_dose_cm2=injected_dose_cm2,
        per_shot_cumulative_injected_dose_cm2=cumulative_injected_dose_cm2,
        per_shot_remaining_source_inventory_atoms_m2=remaining_source_inventory_atoms_m2,
        per_shot_peak_surface_injection_flux_atoms_m2_s=peak_surface_injection_flux_atoms_m2_s,
        per_shot_source_depletion_fraction=source_depletion_fraction,
        last_stack_thermal=last_stack_result,
        per_shot_initial_silicon_surface_temperature_k=initial_silicon_surface_temperature_k,
        per_shot_peak_silicon_surface_temperature_k=peak_silicon_surface_temperature_k,
        per_shot_cycle_end_silicon_surface_temperature_k=cycle_end_silicon_surface_temperature_k,
        per_shot_max_melt_depth_m=max_melt_depth_m,
        per_shot_max_liquid_fraction=max_liquid_fraction,
    )


def _shot_summary_dict(result) -> dict:
    metrics_path = {
        "peak_surface_injection_flux_atoms_m2_s": float(np.max(result.surface_injection_flux_atoms_m2_s)),
        "cumulative_injected_dose_cm2": float(np.trapezoid(result.surface_injection_flux_atoms_m2_s, result.thermal.time) / 1.0e4),
        "source_depletion_fraction": (
            0.0
            if result.source_inventory_atoms_m2[0] <= 0.0
            else float(
                max(
                    0.0,
                    (result.source_inventory_atoms_m2[0] - result.source_inventory_atoms_m2[-1])
                    / result.source_inventory_atoms_m2[0],
                )
            )
        ),
    }
    return metrics_path


def _result_rows(result: MultiShotResult) -> list[dict]:
    depth_cm = result.thermal.depth * 1.0e2
    rows: list[dict] = []
    for idx, shot_number in enumerate(result.shot_index):
        row = {
            "shot_index": int(shot_number),
            "final_peak_p_cm3": float(result.per_shot_peak_p_cm3[idx]),
            "final_junction_depth_nm": float(result.per_shot_final_junction_depth_m[idx] * 1.0e9),
            "shot_injected_dose_cm2": float(result.per_shot_injected_dose_cm2[idx]),
            "cumulative_injected_dose_cm2": float(result.per_shot_cumulative_injected_dose_cm2[idx]),
            "remaining_source_inventory_atoms_m2": float(result.per_shot_remaining_source_inventory_atoms_m2[idx]),
            "peak_surface_injection_flux_atoms_m2_s": float(result.per_shot_peak_surface_injection_flux_atoms_m2_s[idx]),
            "source_depletion_fraction": float(result.per_shot_source_depletion_fraction[idx]),
            "final_total_sheet_dose_cm2": float(np.trapezoid(result.per_shot_final_total_p_cm3[idx], depth_cm)),
            "final_active_origin_sheet_dose_cm2": float(
                np.trapezoid(result.per_shot_final_active_origin_p_cm3[idx], depth_cm)
            ),
            "final_inactive_origin_sheet_dose_cm2": float(
                np.trapezoid(result.per_shot_final_inactive_origin_p_cm3[idx], depth_cm)
            ),
            "final_injected_origin_sheet_dose_cm2": float(
                np.trapezoid(result.per_shot_final_injected_origin_p_cm3[idx], depth_cm)
            ),
        }
        if result.per_shot_initial_silicon_surface_temperature_k is not None:
            row["initial_silicon_surface_temperature_k"] = float(
                result.per_shot_initial_silicon_surface_temperature_k[idx]
            )
        if result.per_shot_peak_silicon_surface_temperature_k is not None:
            row["peak_silicon_surface_temperature_k"] = float(
                result.per_shot_peak_silicon_surface_temperature_k[idx]
            )
        if result.per_shot_cycle_end_silicon_surface_temperature_k is not None:
            row["cycle_end_silicon_surface_temperature_k"] = float(
                result.per_shot_cycle_end_silicon_surface_temperature_k[idx]
            )
        if result.per_shot_max_melt_depth_m is not None:
            row["max_melt_depth_nm"] = float(result.per_shot_max_melt_depth_m[idx] * 1.0e9)
        if result.per_shot_max_liquid_fraction is not None:
            row["max_liquid_fraction"] = float(result.per_shot_max_liquid_fraction[idx])
        rows.append(row)
    return rows


def _profile_shots_to_plot(shot_count: int, requested: list[int] | None) -> list[int]:
    if requested:
        clean = sorted({int(value) for value in requested if 1 <= int(value) <= shot_count})
        if clean:
            return clean
    mid = max(1, int(np.ceil(shot_count / 2.0)))
    return sorted({1, mid, shot_count})


def _plot_metric(
    shot_index: np.ndarray,
    values: np.ndarray,
    ylabel: str,
    title: str,
    path: Path,
    color: str,
) -> None:
    figure, axis = plt.subplots(figsize=(7.4, 4.4))
    axis.plot(shot_index, values, marker="o", lw=2.0, color=color)
    axis.set_xlabel("Shot Index")
    axis.set_ylabel(ylabel)
    axis.set_title(title)
    axis.grid(alpha=0.25)
    figure.tight_layout()
    figure.savefig(path, dpi=220)
    plt.close(figure)


def _plot_total_profiles(
    result: MultiShotResult,
    selected_shots: list[int],
    path: Path,
) -> None:
    figure, axis = plt.subplots(figsize=(8.4, 4.8))
    depth_um = result.thermal.depth * 1.0e6
    background = float(result.thermal.substrate_doping.concentration_cm3)
    colors = ["#5d6d7e", "#117864", "#ca6f1e", "#7d3c98", "#1f618d"]

    for color_index, shot_number in enumerate(selected_shots):
        idx = shot_number - 1
        axis.semilogy(
            depth_um,
            np.maximum(result.per_shot_final_total_p_cm3[idx], 1.0e10),
            lw=2.0,
            color=colors[color_index % len(colors)],
            label=f"Shot {shot_number}",
        )
    axis.axhline(background, color="#cb4335", ls="--", lw=1.3, label="Ga background")
    axis.set_xlabel("Depth in Si (um)")
    axis.set_ylabel("Concentration (cm^-3)")
    axis.set_title("Multi-Shot: Final Total P Profiles")
    axis.grid(alpha=0.25)
    axis.legend()
    figure.tight_layout()
    figure.savefig(path, dpi=220)
    plt.close(figure)


def _plot_final_components(result: MultiShotResult, path: Path) -> None:
    figure, axis = plt.subplots(figsize=(8.4, 4.8))
    depth_um = result.thermal.depth * 1.0e6
    final_index = -1
    axis.semilogy(
        depth_um,
        np.maximum(result.per_shot_final_total_p_cm3[final_index], 1.0e10),
        lw=2.2,
        color="#117864",
        label="Final total P",
    )
    axis.semilogy(
        depth_um,
        np.maximum(result.per_shot_final_active_origin_p_cm3[final_index], 1.0e10),
        lw=1.8,
        ls="--",
        color="#7d6608",
        label="Active-origin P",
    )
    axis.semilogy(
        depth_um,
        np.maximum(result.per_shot_final_inactive_origin_p_cm3[final_index], 1.0e10),
        lw=1.8,
        ls=":",
        color="#1f618d",
        label="Inactive-origin P",
    )
    axis.semilogy(
        depth_um,
        np.maximum(result.per_shot_final_injected_origin_p_cm3[final_index], 1.0e10),
        lw=1.8,
        ls="-.",
        color="#ca6f1e",
        label="Injected-origin P",
    )
    axis.axhline(
        float(result.thermal.substrate_doping.concentration_cm3),
        color="#cb4335",
        ls="--",
        lw=1.3,
        label="Ga background",
    )
    axis.set_xlabel("Depth in Si (um)")
    axis.set_ylabel("Concentration (cm^-3)")
    axis.set_title("Multi-Shot: Final Shot Component Profiles")
    axis.grid(alpha=0.25)
    axis.legend()
    figure.tight_layout()
    figure.savefig(path, dpi=220)
    plt.close(figure)


def save_outputs(
    result: MultiShotResult,
    output_dir: str | Path,
    profile_shots: list[int] | None = None,
    fast_output: bool = False,
) -> Path:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    npz_payload = {
        "shot_index": result.shot_index,
        "depth_m": result.thermal.depth,
        "per_shot_final_total_p_cm3": result.per_shot_final_total_p_cm3,
        "per_shot_final_active_origin_p_cm3": result.per_shot_final_active_origin_p_cm3,
        "per_shot_final_inactive_origin_p_cm3": result.per_shot_final_inactive_origin_p_cm3,
        "per_shot_final_injected_origin_p_cm3": result.per_shot_final_injected_origin_p_cm3,
        "per_shot_final_junction_depth_m": result.per_shot_final_junction_depth_m,
        "per_shot_peak_p_cm3": result.per_shot_peak_p_cm3,
        "per_shot_injected_dose_cm2": result.per_shot_injected_dose_cm2,
        "per_shot_cumulative_injected_dose_cm2": result.per_shot_cumulative_injected_dose_cm2,
        "per_shot_remaining_source_inventory_atoms_m2": result.per_shot_remaining_source_inventory_atoms_m2,
        "per_shot_peak_surface_injection_flux_atoms_m2_s": result.per_shot_peak_surface_injection_flux_atoms_m2_s,
        "per_shot_source_depletion_fraction": result.per_shot_source_depletion_fraction,
    }
    if result.per_shot_initial_silicon_surface_temperature_k is not None:
        npz_payload["per_shot_initial_silicon_surface_temperature_k"] = (
            result.per_shot_initial_silicon_surface_temperature_k
        )
    if result.per_shot_peak_silicon_surface_temperature_k is not None:
        npz_payload["per_shot_peak_silicon_surface_temperature_k"] = (
            result.per_shot_peak_silicon_surface_temperature_k
        )
    if result.per_shot_cycle_end_silicon_surface_temperature_k is not None:
        npz_payload["per_shot_cycle_end_silicon_surface_temperature_k"] = (
            result.per_shot_cycle_end_silicon_surface_temperature_k
        )
    if result.per_shot_max_melt_depth_m is not None:
        npz_payload["per_shot_max_melt_depth_m"] = result.per_shot_max_melt_depth_m
    if result.per_shot_max_liquid_fraction is not None:
        npz_payload["per_shot_max_liquid_fraction"] = result.per_shot_max_liquid_fraction
    npz_path = output_path / "phase4_multishot_results.npz"
    if fast_output:
        np.savez(npz_path, **npz_payload)
    else:
        np.savez_compressed(npz_path, **npz_payload)

    rows = _result_rows(result)
    csv_path = output_path / "multishot_summary.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "multishot_parameters": asdict(result.multishot_parameters),
        "diffusion_parameters": asdict(result.diffusion_parameters),
        "final_shot": rows[-1],
        "shot_count": int(result.multishot_parameters.shot_count),
        "source_replenishment_mode": result.multishot_parameters.source_replenishment_mode,
        "thermal_history_mode": result.multishot_parameters.thermal_history_mode,
        "output_mode": "fast" if fast_output else "full",
    }
    with (output_path / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)

    if not fast_output:
        selected_shots = _profile_shots_to_plot(int(result.multishot_parameters.shot_count), profile_shots)
        _plot_metric(
            result.shot_index,
            result.per_shot_final_junction_depth_m * 1.0e9,
            "Final Junction Depth (nm)",
            "Multi-Shot: Junction Depth After Each Shot",
            output_path / "junction_depth_vs_shot.png",
            "#2471a3",
        )
        _plot_metric(
            result.shot_index,
            result.per_shot_injected_dose_cm2,
            "Shot Injected Dose (cm^-2)",
            "Multi-Shot: Injected Dose Per Shot",
            output_path / "injected_dose_per_shot.png",
            "#ca6f1e",
        )
        _plot_metric(
            result.shot_index,
            result.per_shot_cumulative_injected_dose_cm2,
            "Cumulative Injected Dose (cm^-2)",
            "Multi-Shot: Cumulative Injected Dose",
            output_path / "cumulative_injected_dose_vs_shot.png",
            "#7d3c98",
        )
        _plot_metric(
            result.shot_index,
            result.per_shot_remaining_source_inventory_atoms_m2,
            "Remaining Source Inventory (atoms/m^2)",
            "Multi-Shot: Remaining PSG Source Inventory",
            output_path / "remaining_source_inventory_vs_shot.png",
            "#af601a",
        )
        if result.per_shot_peak_silicon_surface_temperature_k is not None:
            _plot_metric(
                result.shot_index,
                result.per_shot_peak_silicon_surface_temperature_k,
                "Peak Si Surface Temperature (K)",
                "Multi-Shot: Peak Silicon Surface Temperature",
                output_path / "peak_silicon_surface_temperature_vs_shot.png",
                "#1e8449",
            )
        if result.per_shot_cycle_end_silicon_surface_temperature_k is not None:
            _plot_metric(
                result.shot_index,
                result.per_shot_cycle_end_silicon_surface_temperature_k,
                "Cycle-End Si Surface Temperature (K)",
                "Multi-Shot: Cycle-End Silicon Surface Temperature",
                output_path / "cycle_end_silicon_surface_temperature_vs_shot.png",
                "#7d3c98",
            )
        if result.per_shot_max_melt_depth_m is not None:
            _plot_metric(
                result.shot_index,
                result.per_shot_max_melt_depth_m * 1.0e9,
                "Max Melt Depth (nm)",
                "Multi-Shot: Max Melt Depth Per Shot",
                output_path / "max_melt_depth_vs_shot.png",
                "#2471a3",
            )
        _plot_total_profiles(
            result,
            selected_shots=selected_shots,
            path=output_path / "total_p_profiles_selected_shots.png",
        )
        _plot_final_components(
            result,
            path=output_path / "final_component_profiles.png",
        )
    return output_path
