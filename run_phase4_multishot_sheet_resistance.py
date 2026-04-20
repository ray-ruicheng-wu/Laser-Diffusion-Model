from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from laser_doping_sim.activation_models import load_piecewise_multishot_dual_channel_activation_model_csv
from laser_doping_sim.measured_profiles import interpolate_profile_log_cm3, load_measured_initial_profile_csv
from laser_doping_sim.sheet_resistance import MasettiElectronMobilityModel, sheet_resistance_ohm_per_sq


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Apply a new multi-shot activation parameter table to a Phase 4 multi-shot chemistry run "
            "and estimate shot-by-shot sheet resistance."
        )
    )
    parser.add_argument("--phase4-dir", required=True)
    parser.add_argument("--activation-parameter-csv", required=True)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--initial-inactive-activation-fraction", type=float, default=0.06447924522684517)
    parser.add_argument("--measurement-temperature-k", type=float, default=300.0)
    return parser


def _resolve_from_root(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return ROOT / path


def _save_table(rows: list[dict], output_dir: Path, filename: str) -> Path:
    path = output_dir / filename
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return path


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


def main() -> int:
    args = build_parser().parse_args()
    phase4_dir = _resolve_from_root(args.phase4_dir)
    activation_parameter_csv = _resolve_from_root(args.activation_parameter_csv)
    output_dir = (
        _resolve_from_root(args.output_dir)
        if args.output_dir
        else phase4_dir / "multishot_rsh"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    summary = json.loads((phase4_dir / "summary.json").read_text(encoding="utf-8"))
    multishot_npz = np.load(phase4_dir / "multishot" / "phase4_multishot_results.npz")
    model = load_piecewise_multishot_dual_channel_activation_model_csv(
        activation_parameter_csv,
        initial_inactive_activation_fraction=args.initial_inactive_activation_fraction,
    )
    mobility_model = MasettiElectronMobilityModel(temperature_k=args.measurement_temperature_k)

    power_w = float(summary["laser_input"]["average_power_w"])
    background_ga_cm3 = float(summary["thermal"]["substrate_doping"]["concentration_cm3"])
    depth_m = np.asarray(multishot_npz["depth_m"], dtype=float)
    shot_index = np.asarray(multishot_npz["shot_index"], dtype=int)
    active_origin = np.asarray(multishot_npz["per_shot_final_active_origin_p_cm3"], dtype=float)
    inactive_origin = np.asarray(multishot_npz["per_shot_final_inactive_origin_p_cm3"], dtype=float)
    injected_origin = np.asarray(multishot_npz["per_shot_final_injected_origin_p_cm3"], dtype=float)
    cumulative_injected_dose_cm2 = np.asarray(multishot_npz["per_shot_cumulative_injected_dose_cm2"], dtype=float)

    initial_rsh_ohm_per_sq = None
    diffusion_params = summary["multishot"]["diffusion_parameters"]
    if diffusion_params.get("initial_profile_kind") == "measured" and diffusion_params.get("initial_profile_csv"):
        measured_profile = load_measured_initial_profile_csv(_resolve_from_root(diffusion_params["initial_profile_csv"]))
        depth_nm = depth_m * 1.0e9
        initial_active_donor_cm3 = (
            interpolate_profile_log_cm3(depth_nm, measured_profile.depth_nm, measured_profile.active_p_cm3)
            + args.initial_inactive_activation_fraction
            * interpolate_profile_log_cm3(depth_nm, measured_profile.depth_nm, measured_profile.inactive_p_cm3)
        )
        initial_rsh_ohm_per_sq = sheet_resistance_ohm_per_sq(
            depth_m,
            initial_active_donor_cm3,
            background_ga_cm3,
            mobility_model=mobility_model,
        )

    rows: list[dict] = []
    activation_rows: list[dict] = []
    for idx, shot in enumerate(shot_index):
        eta_inactive, eta_injected = model.fractions_at_state(
            power_w=power_w,
            shot_index=int(shot),
            cumulative_injected_dose_cm2=float(cumulative_injected_dose_cm2[idx]),
        )
        active_donor_cm3 = (
            active_origin[idx]
            + eta_inactive * inactive_origin[idx]
            + eta_injected * injected_origin[idx]
        )
        rsh_after = sheet_resistance_ohm_per_sq(
            depth_m,
            active_donor_cm3,
            background_ga_cm3,
            mobility_model=mobility_model,
        )
        rows.append(
            {
                "shot_index": int(shot),
                "power_w": power_w,
                "cumulative_injected_dose_cm2": float(cumulative_injected_dose_cm2[idx]),
                "effective_final_inactive_activation_fraction": float(eta_inactive),
                "effective_final_injected_activation_fraction": float(eta_injected),
                "rsh_init_ohm_per_sq": initial_rsh_ohm_per_sq,
                "rsh_after_ohm_per_sq": float(rsh_after),
                "final_active_origin_sheet_dose_cm2": float(np.trapezoid(active_origin[idx], depth_m * 1.0e2)),
                "final_inactive_origin_sheet_dose_cm2": float(np.trapezoid(inactive_origin[idx], depth_m * 1.0e2)),
                "final_injected_origin_sheet_dose_cm2": float(np.trapezoid(injected_origin[idx], depth_m * 1.0e2)),
                "active_donor_sheet_dose_cm2": float(np.trapezoid(active_donor_cm3, depth_m * 1.0e2)),
            }
        )
        activation_rows.append(
            {
                "power_w": power_w,
                "shot_index": int(shot),
                "cumulative_injected_dose_cm2": float(cumulative_injected_dose_cm2[idx]),
                "effective_final_inactive_activation_fraction": float(eta_inactive),
                "effective_final_injected_activation_fraction": float(eta_injected),
            }
        )

    summary_csv = _save_table(rows, output_dir, "multishot_sheet_resistance_summary.csv")
    activation_csv = _save_table(activation_rows, output_dir, "expanded_multishot_activation_table.csv")
    with (output_dir / "multishot_sheet_resistance_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(rows, handle, indent=2)

    shot_axis = np.asarray([row["shot_index"] for row in rows], dtype=int)
    _plot_metric(
        shot_axis,
        np.asarray([row["rsh_after_ohm_per_sq"] for row in rows], dtype=float),
        "Sheet Resistance (ohm/sq)",
        "Phase 4 Multi-Shot Rsh Estimate",
        output_dir / "rsh_vs_shot.png",
        "#ca6f1e",
    )
    _plot_metric(
        shot_axis,
        np.asarray([row["effective_final_inactive_activation_fraction"] for row in rows], dtype=float),
        "Inactive Activation Fraction",
        "Applied Inactive Activation vs Shot",
        output_dir / "inactive_activation_vs_shot.png",
        "#7d6608",
    )
    _plot_metric(
        shot_axis,
        np.asarray([row["effective_final_injected_activation_fraction"] for row in rows], dtype=float),
        "Injected Activation Fraction",
        "Applied Injected Activation vs Shot",
        output_dir / "injected_activation_vs_shot.png",
        "#1f618d",
    )

    manifest = {
        "phase4_dir": str(phase4_dir),
        "activation_parameter_csv": str(activation_parameter_csv),
        "output_dir": str(output_dir),
        "summary_csv": str(summary_csv),
        "expanded_activation_csv": str(activation_csv),
        "initial_inactive_activation_fraction": float(args.initial_inactive_activation_fraction),
        "measurement_temperature_k": float(args.measurement_temperature_k),
    }
    with (output_dir / "manifest.json").open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)

    print(f"Saved Phase 4 multi-shot Rsh summary to: {summary_csv}")
    print(f"Saved expanded activation table to: {activation_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
