from __future__ import annotations

from dataclasses import asdict, dataclass
import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from .phase1_thermal import SimulationResult
from .phase2_diffusion import DiffusionParameters, run_diffusion_with_state


@dataclass(slots=True)
class MultiShotParameters:
    shot_count: int = 1
    source_replenishment_mode: str = "carry"
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


def run_multishot_diffusion(
    thermal: SimulationResult,
    params: DiffusionParameters,
    multishot_params: MultiShotParameters | None = None,
) -> MultiShotResult:
    if multishot_params is None:
        multishot_params = MultiShotParameters()

    if multishot_params.shot_count <= 0:
        raise ValueError("shot_count must be positive.")
    if multishot_params.source_replenishment_mode not in {"carry", "reset_each_shot"}:
        raise ValueError(
            "source_replenishment_mode must be one of: carry, reset_each_shot"
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

    current_active_profile_cm3: np.ndarray | None = None
    current_inactive_profile_cm3: np.ndarray | None = None
    current_injected_profile_cm3: np.ndarray | None = None
    current_source_inventory_atoms_m2: float | None = None

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
        rows.append(
            {
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
        )
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
    axis.set_title("Multi-Shot V1: Final Total P Profiles")
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
    axis.set_title("Multi-Shot V1: Final Shot Component Profiles")
    axis.grid(alpha=0.25)
    axis.legend()
    figure.tight_layout()
    figure.savefig(path, dpi=220)
    plt.close(figure)


def save_outputs(
    result: MultiShotResult,
    output_dir: str | Path,
    profile_shots: list[int] | None = None,
) -> Path:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    np.savez_compressed(
        output_path / "phase4_multishot_results.npz",
        shot_index=result.shot_index,
        depth_m=result.thermal.depth,
        per_shot_final_total_p_cm3=result.per_shot_final_total_p_cm3,
        per_shot_final_active_origin_p_cm3=result.per_shot_final_active_origin_p_cm3,
        per_shot_final_inactive_origin_p_cm3=result.per_shot_final_inactive_origin_p_cm3,
        per_shot_final_injected_origin_p_cm3=result.per_shot_final_injected_origin_p_cm3,
        per_shot_final_junction_depth_m=result.per_shot_final_junction_depth_m,
        per_shot_peak_p_cm3=result.per_shot_peak_p_cm3,
        per_shot_injected_dose_cm2=result.per_shot_injected_dose_cm2,
        per_shot_cumulative_injected_dose_cm2=result.per_shot_cumulative_injected_dose_cm2,
        per_shot_remaining_source_inventory_atoms_m2=result.per_shot_remaining_source_inventory_atoms_m2,
        per_shot_peak_surface_injection_flux_atoms_m2_s=result.per_shot_peak_surface_injection_flux_atoms_m2_s,
        per_shot_source_depletion_fraction=result.per_shot_source_depletion_fraction,
    )

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
    }
    with (output_path / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)

    selected_shots = _profile_shots_to_plot(int(result.multishot_parameters.shot_count), profile_shots)
    _plot_metric(
        result.shot_index,
        result.per_shot_final_junction_depth_m * 1.0e9,
        "Final Junction Depth (nm)",
        "Multi-Shot V1: Junction Depth After Each Shot",
        output_path / "junction_depth_vs_shot.png",
        "#2471a3",
    )
    _plot_metric(
        result.shot_index,
        result.per_shot_injected_dose_cm2,
        "Shot Injected Dose (cm^-2)",
        "Multi-Shot V1: Injected Dose Per Shot",
        output_path / "injected_dose_per_shot.png",
        "#ca6f1e",
    )
    _plot_metric(
        result.shot_index,
        result.per_shot_cumulative_injected_dose_cm2,
        "Cumulative Injected Dose (cm^-2)",
        "Multi-Shot V1: Cumulative Injected Dose",
        output_path / "cumulative_injected_dose_vs_shot.png",
        "#7d3c98",
    )
    _plot_metric(
        result.shot_index,
        result.per_shot_remaining_source_inventory_atoms_m2,
        "Remaining Source Inventory (atoms/m^2)",
        "Multi-Shot V1: Remaining PSG Source Inventory",
        output_path / "remaining_source_inventory_vs_shot.png",
        "#af601a",
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
