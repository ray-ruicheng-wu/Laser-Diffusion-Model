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
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import run_sheet_resistance_cases as rsh_cases  # noqa: E402
from laser_doping_sim.activation_models import (  # noqa: E402
    load_piecewise_dual_channel_activation_model_csv,
)
from laser_doping_sim.sheet_resistance import (  # noqa: E402
    MasettiElectronMobilityModel,
    sheet_resistance_ohm_per_sq,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Refit a high-power segment of the dual-channel activation model with a "
            "monotonic empirical Rsh target built from measured anchor points. This "
            "version uses fine-time-step thermal cases and, by default, attributes the "
            "segment correction to initial inactive re-activation only."
        )
    )
    parser.add_argument(
        "--case-dirs",
        nargs="+",
        required=True,
        help="Phase 3 case directories used in the segment refit.",
    )
    parser.add_argument(
        "--measured-rsh-csv",
        required=True,
        help="CSV containing columns power_w and measured_rsh_after_ohm_per_sq.",
    )
    parser.add_argument(
        "--base-activation-csv",
        required=True,
        help="Existing dual-channel activation CSV used below the refit segment.",
    )
    parser.add_argument(
        "--initial-inactive-activation-fraction",
        type=float,
        required=True,
        help="Initial inactive activation fraction used when loading the base activation table.",
    )
    parser.add_argument(
        "--measurement-temperature-k",
        type=float,
        default=300.0,
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Output directory for the refitted activation model and diagnostics.",
    )
    return parser


def _load_measured_rsh(path: Path) -> dict[float, float]:
    values: dict[float, float] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"power_w", "measured_rsh_after_ohm_per_sq"}
        if not required.issubset(set(reader.fieldnames or [])):
            raise ValueError(
                "Measured Rsh CSV must contain power_w and measured_rsh_after_ohm_per_sq."
            )
        for row in reader:
            measured_value = row.get("measured_rsh_after_ohm_per_sq", "")
            if measured_value is None or measured_value == "":
                continue
            values[float(row["power_w"])] = float(measured_value)
    return values


def _write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _target_rsh_by_power(sorted_powers: list[float], measured_rsh: dict[float, float]) -> dict[float, float]:
    targets: dict[float, float] = {}
    measured_powers = sorted(power for power in measured_rsh if power in sorted_powers)
    if len(measured_powers) < 2:
        raise ValueError("At least two measured Rsh anchor powers are required inside the refit segment.")

    for power_w in sorted_powers:
        if power_w in measured_rsh:
            targets[power_w] = measured_rsh[power_w]
            continue

        lower_candidates = [power for power in measured_powers if power < power_w]
        upper_candidates = [power for power in measured_powers if power > power_w]
        if not lower_candidates or not upper_candidates:
            raise ValueError(
                f"Cannot interpolate target Rsh for {power_w} W without bracketing measured anchors."
            )
        lower = max(lower_candidates)
        upper = min(upper_candidates)
        alpha = (power_w - lower) / (upper - lower)
        targets[power_w] = (1.0 - alpha) * measured_rsh[lower] + alpha * measured_rsh[upper]
    return targets


def _solve_inactive_fraction_for_target(
    depth_m: np.ndarray,
    final_active_cm3: np.ndarray,
    final_inactive_cm3: np.ndarray,
    background_ga_cm3: float,
    target_rsh_ohm_sq: float,
    mobility_model: MasettiElectronMobilityModel,
) -> tuple[float, float]:
    def modeled_rsh(inactive_fraction: float) -> float:
        profile = final_active_cm3 + inactive_fraction * final_inactive_cm3
        return sheet_resistance_ohm_per_sq(
            depth_m,
            profile,
            background_ga_cm3,
            mobility_model=mobility_model,
        )

    rsh_at_zero = modeled_rsh(0.0)
    rsh_at_one = modeled_rsh(1.0)

    if target_rsh_ohm_sq >= rsh_at_zero:
        return 0.0, rsh_at_zero
    if target_rsh_ohm_sq <= rsh_at_one:
        return 1.0, rsh_at_one

    lo = 0.0
    hi = 1.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        value = modeled_rsh(mid)
        if value > target_rsh_ohm_sq:
            lo = mid
        else:
            hi = mid

    inactive_fraction = 0.5 * (lo + hi)
    return inactive_fraction, modeled_rsh(inactive_fraction)


def main() -> int:
    args = build_parser().parse_args()
    output_dir = ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    measured_rsh = _load_measured_rsh(ROOT / args.measured_rsh_csv)
    base_model = load_piecewise_dual_channel_activation_model_csv(
        ROOT / args.base_activation_csv,
        initial_inactive_activation_fraction=args.initial_inactive_activation_fraction,
    )
    mobility_model = MasettiElectronMobilityModel(temperature_k=args.measurement_temperature_k)

    case_dirs = [ROOT / case_dir for case_dir in args.case_dirs]
    case_powers: dict[float, Path] = {}
    for case_dir in case_dirs:
        power_w = rsh_cases._power_from_case(case_dir)
        if power_w is None:
            raise ValueError(f"Could not determine power for case {case_dir}.")
        case_powers[float(power_w)] = case_dir

    fit_powers = sorted(case_powers)
    target_rsh = _target_rsh_by_power(fit_powers, measured_rsh)

    component_cache: dict[float, tuple[np.ndarray, np.ndarray, np.ndarray, float]] = {}
    for power_w, case_dir in case_powers.items():
        (
            depth_m,
            _initial_active_cm3,
            _initial_inactive_cm3,
            final_active_component_cm3,
            background_ga_cm3,
            final_inactive_component_cm3,
            _final_injected_component_cm3,
        ) = rsh_cases._rerun_component_profiles(case_dir)
        component_cache[power_w] = (
            depth_m,
            final_active_component_cm3,
            final_inactive_component_cm3,
            background_ga_cm3,
        )

    refit_rows: list[dict] = []
    comparison_rows: list[dict] = []
    for power_w in fit_powers:
        depth_m, final_active_cm3, final_inactive_cm3, background_ga_cm3 = component_cache[power_w]
        inactive_fraction, modeled_rsh = _solve_inactive_fraction_for_target(
            depth_m=depth_m,
            final_active_cm3=final_active_cm3,
            final_inactive_cm3=final_inactive_cm3,
            background_ga_cm3=background_ga_cm3,
            target_rsh_ohm_sq=target_rsh[power_w],
            mobility_model=mobility_model,
        )
        refit_rows.append(
            {
                "power_w": power_w,
                "effective_final_inactive_activation_fraction": inactive_fraction,
                "effective_final_injected_activation_fraction": 0.0,
                "regime": "monotonic_segment_refit_inactive_only",
            }
        )
        comparison_rows.append(
            {
                "power_w": power_w,
                "target_rsh_after_ohm_per_sq": target_rsh[power_w],
                "measured_rsh_after_ohm_per_sq": measured_rsh.get(power_w),
                "modeled_rsh_after_ohm_per_sq": modeled_rsh,
                "effective_final_inactive_activation_fraction": inactive_fraction,
                "effective_final_injected_activation_fraction": 0.0,
            }
        )

    base_rows: list[dict] = []
    first_fit_power = fit_powers[0]
    with (ROOT / args.base_activation_csv).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            power_w = float(row["power_w"])
            if power_w < first_fit_power:
                base_rows.append(
                    {
                        "power_w": power_w,
                        "effective_final_inactive_activation_fraction": float(
                            row["effective_final_inactive_activation_fraction"]
                        ),
                        "effective_final_injected_activation_fraction": float(
                            row["effective_final_injected_activation_fraction"]
                        ),
                        "regime": row.get("regime", "base_model"),
                    }
                )

    combined_rows = sorted(base_rows + refit_rows, key=lambda row: row["power_w"])

    model_csv = output_dir / "dual_channel_activation_model_monotonic_segment_refit.csv"
    _write_csv(
        model_csv,
        combined_rows,
        [
            "power_w",
            "effective_final_inactive_activation_fraction",
            "effective_final_injected_activation_fraction",
            "regime",
        ],
    )

    comparison_csv = output_dir / "target_vs_modeled_rsh_monotonic_segment_refit.csv"
    _write_csv(
        comparison_csv,
        comparison_rows,
        [
            "power_w",
            "target_rsh_after_ohm_per_sq",
            "measured_rsh_after_ohm_per_sq",
            "modeled_rsh_after_ohm_per_sq",
            "effective_final_inactive_activation_fraction",
            "effective_final_injected_activation_fraction",
        ],
    )

    summary = {
        "fit_powers_w": fit_powers,
        "target_rsh_after_ohm_per_sq": target_rsh,
        "model_csv": str(model_csv),
        "comparison_csv": str(comparison_csv),
        "assumptions": {
            "high_power_segment_target_construction": (
                "Measured Rsh anchors inside the segment are used directly. Missing powers are assigned a monotonic "
                "target by linear interpolation between bracketing measured anchors."
            ),
            "high_power_segment_injected_activation_fraction": 0.0,
            "high_power_segment_interpretation": (
                "This refit attributes the 48-60 W segment correction to redistributed initial inactive phosphorus "
                "only. Injected phosphorus remains chemically present but is not counted as electrically active in "
                "this empirical segment closure."
            ),
        },
    }
    with (output_dir / "monotonic_segment_refit_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)

    powers = np.array([row["power_w"] for row in comparison_rows], dtype=float)
    targets = np.array([row["target_rsh_after_ohm_per_sq"] for row in comparison_rows], dtype=float)
    modeled = np.array([row["modeled_rsh_after_ohm_per_sq"] for row in comparison_rows], dtype=float)
    measured_values = np.array(
        [
            np.nan if row["measured_rsh_after_ohm_per_sq"] is None else float(row["measured_rsh_after_ohm_per_sq"])
            for row in comparison_rows
        ],
        dtype=float,
    )

    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    ax.plot(powers, targets, marker="o", linewidth=2.0, label="Monotonic target Rsh")
    ax.plot(powers, modeled, marker="s", linewidth=2.0, label="Modeled Rsh")
    if np.isfinite(measured_values).any():
        mask = np.isfinite(measured_values)
        ax.scatter(powers[mask], measured_values[mask], s=60, marker="D", label="Measured Rsh anchors")
    ax.set_xlabel("Laser power (W)")
    ax.set_ylabel("Sheet resistance after laser (ohm/sq)")
    ax.set_title("Monotonic Segment Refit for High-Power Dual-Channel Model")
    ax.grid(True, linestyle="--", alpha=0.35)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "monotonic_segment_refit_rsh.png", dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    inactive_values = np.array(
        [row["effective_final_inactive_activation_fraction"] for row in refit_rows],
        dtype=float,
    )
    ax.plot(powers, inactive_values, marker="o", linewidth=2.0, label="Inactive re-activation")
    ax.set_xlabel("Laser power (W)")
    ax.set_ylabel("Activation fraction")
    ax.set_ylim(0.0, 1.05)
    ax.set_title("Monotonic Segment Refit: Effective Inactive Re-Activation")
    ax.grid(True, linestyle="--", alpha=0.35)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "monotonic_segment_refit_activation.png", dpi=200)
    plt.close(fig)

    print(f"Saved monotonic segment refit to: {output_dir}")
    print(f"Model CSV: {model_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
