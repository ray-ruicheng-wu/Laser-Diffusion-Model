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
from laser_doping_sim.sheet_resistance import (  # noqa: E402
    MasettiElectronMobilityModel,
    sheet_resistance_ohm_per_sq,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Calibrate a dual-channel activation model that separates "
            "post-laser re-activation of initial inactive phosphorus from "
            "activation of injected phosphorus."
        )
    )
    parser.add_argument(
        "--case-dirs",
        nargs="+",
        required=True,
        help="Phase 3 case directories to calibrate against.",
    )
    parser.add_argument(
        "--measured-rsh-csv",
        required=True,
        help=(
            "CSV containing columns power_w, measured_rsh_before_ohm_per_sq "
            "and measured_rsh_after_ohm_per_sq."
        ),
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Output directory for the calibrated dual-channel activation model.",
    )
    parser.add_argument(
        "--measurement-temperature-k",
        type=float,
        default=300.0,
    )
    parser.add_argument(
        "--injection-threshold-cm2",
        type=float,
        default=1.0e14,
        help=(
            "Powers with final injected dose below this threshold are treated as "
            "inactive-re-activation-only calibration points."
        ),
    )
    parser.add_argument(
        "--target-initial-rsh-ohm-per-sq",
        type=float,
        default=None,
        help=(
            "Optional explicit target initial sheet resistance. If omitted, the "
            "mean of available measured initial Rsh values is used."
        ),
    )
    return parser


def _load_measured_rsh(path: Path) -> dict[float, dict[str, float | None]]:
    rows: dict[float, dict[str, float | None]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"power_w", "measured_rsh_after_ohm_per_sq"}
        if not required.issubset(set(reader.fieldnames or [])):
            raise ValueError(
                "Measured Rsh CSV must contain at least power_w and "
                "measured_rsh_after_ohm_per_sq."
            )
        for row in reader:
            power_w = float(row["power_w"])
            before_raw = (row.get("measured_rsh_before_ohm_per_sq") or "").strip()
            rows[power_w] = {
                "measured_rsh_before_ohm_per_sq": float(before_raw) if before_raw else None,
                "measured_rsh_after_ohm_per_sq": float(row["measured_rsh_after_ohm_per_sq"]),
            }
    return rows


def _integrate_sheet_dose_cm2(depth_m: np.ndarray, concentration_cm3: np.ndarray) -> float:
    return float(np.trapezoid(concentration_cm3, depth_m * 1.0e2))


def _solve_activation_fraction(
    depth_m: np.ndarray,
    fixed_active_cm3: np.ndarray,
    scalable_component_cm3: np.ndarray,
    background_ga_cm3: float,
    mobility_model: MasettiElectronMobilityModel,
    target_rsh_ohm_per_sq: float,
) -> tuple[float, float, bool]:
    def rsh_for_fraction(fraction: float) -> float:
        profile = fixed_active_cm3 + fraction * scalable_component_cm3
        return sheet_resistance_ohm_per_sq(
            depth_m,
            profile,
            background_ga_cm3,
            mobility_model=mobility_model,
        )

    rsh_at_zero = rsh_for_fraction(0.0)
    rsh_at_one = rsh_for_fraction(1.0)

    if target_rsh_ohm_per_sq >= rsh_at_zero:
        return 0.0, rsh_at_zero, True
    if target_rsh_ohm_per_sq <= rsh_at_one:
        return 1.0, rsh_at_one, True

    low = 0.0
    high = 1.0
    for _ in range(80):
        mid = 0.5 * (low + high)
        rsh_mid = rsh_for_fraction(mid)
        if rsh_mid > target_rsh_ohm_per_sq:
            low = mid
        else:
            high = mid
    fraction = 0.5 * (low + high)
    return fraction, rsh_for_fraction(fraction), False


def _interp_hold(points_power: np.ndarray, points_value: np.ndarray, power_w: float) -> float:
    return float(np.interp(power_w, points_power, points_value, left=points_value[0], right=points_value[-1]))


def main() -> int:
    args = build_parser().parse_args()
    output_dir = ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    mobility_model = MasettiElectronMobilityModel(temperature_k=args.measurement_temperature_k)
    measured = _load_measured_rsh(ROOT / args.measured_rsh_csv)

    case_records: list[dict] = []
    base_initial: dict | None = None

    for case_dir_raw in args.case_dirs:
        case_dir = ROOT / case_dir_raw
        (
            depth_m,
            initial_active_cm3,
            initial_inactive_cm3,
            final_active_component_cm3,
            background_ga_cm3,
            final_inactive_component_cm3,
            final_injected_component_cm3,
        ) = rsh_cases._rerun_component_profiles(case_dir)
        power_w = rsh_cases._power_from_case(case_dir)
        if power_w is None:
            raise ValueError(f"Could not determine power for case {case_dir}.")
        if power_w not in measured:
            raise ValueError(f"No measured Rsh row found for power {power_w} W.")

        initial_injected_component_cm3 = np.zeros_like(initial_inactive_cm3)
        record = {
            "case_dir": str(case_dir),
            "power_w": float(power_w),
            "depth_m": depth_m,
            "background_ga_cm3": background_ga_cm3,
            "initial_active_cm3": initial_active_cm3,
            "initial_inactive_cm3": initial_inactive_cm3,
            "initial_injected_component_cm3": initial_injected_component_cm3,
            "final_active_component_cm3": final_active_component_cm3,
            "final_inactive_component_cm3": final_inactive_component_cm3,
            "final_injected_component_cm3": final_injected_component_cm3,
            "final_injected_component_sheet_dose_cm2": _integrate_sheet_dose_cm2(
                depth_m, final_injected_component_cm3
            ),
            "measured_rsh_before_ohm_per_sq": measured[power_w]["measured_rsh_before_ohm_per_sq"],
            "measured_rsh_after_ohm_per_sq": measured[power_w]["measured_rsh_after_ohm_per_sq"],
        }
        case_records.append(record)
        if base_initial is None:
            base_initial = record

    case_records.sort(key=lambda row: row["power_w"])
    if base_initial is None:
        raise ValueError("No case records were generated.")

    if args.target_initial_rsh_ohm_per_sq is not None:
        target_initial_rsh = float(args.target_initial_rsh_ohm_per_sq)
    else:
        initial_measurements = [
            row["measured_rsh_before_ohm_per_sq"]
            for row in case_records
            if row["measured_rsh_before_ohm_per_sq"] is not None
        ]
        if not initial_measurements:
            raise ValueError("No measured initial Rsh values were provided.")
        target_initial_rsh = float(np.mean(initial_measurements))

    f_init, modeled_initial_rsh, init_clamped = _solve_activation_fraction(
        depth_m=base_initial["depth_m"],
        fixed_active_cm3=base_initial["initial_active_cm3"],
        scalable_component_cm3=base_initial["initial_inactive_cm3"],
        background_ga_cm3=base_initial["background_ga_cm3"],
        mobility_model=mobility_model,
        target_rsh_ohm_per_sq=target_initial_rsh,
    )

    low_records = [
        row for row in case_records if row["final_injected_component_sheet_dose_cm2"] <= args.injection_threshold_cm2
    ]
    high_records = [
        row for row in case_records if row["final_injected_component_sheet_dose_cm2"] > args.injection_threshold_cm2
    ]
    if not low_records:
        raise ValueError("No low-injection cases found for inactive-only calibration.")

    inactive_support_power: list[float] = []
    inactive_support_fraction: list[float] = []
    calibration_rows: list[dict] = []

    for row in low_records:
        fraction_inactive, modeled_rsh_after, clamped = _solve_activation_fraction(
            depth_m=row["depth_m"],
            fixed_active_cm3=row["final_active_component_cm3"],
            scalable_component_cm3=row["final_inactive_component_cm3"],
            background_ga_cm3=row["background_ga_cm3"],
            mobility_model=mobility_model,
            target_rsh_ohm_per_sq=row["measured_rsh_after_ohm_per_sq"],
        )
        inactive_support_power.append(row["power_w"])
        inactive_support_fraction.append(fraction_inactive)
        calibration_rows.append(
            {
                "power_w": row["power_w"],
                "regime": "inactive_only_fit",
                "measured_rsh_before_ohm_per_sq": row["measured_rsh_before_ohm_per_sq"],
                "measured_rsh_after_ohm_per_sq": row["measured_rsh_after_ohm_per_sq"],
                "final_injected_component_sheet_dose_cm2": row["final_injected_component_sheet_dose_cm2"],
                "effective_final_inactive_activation_fraction": fraction_inactive,
                "effective_final_injected_activation_fraction": 0.0,
                "modeled_rsh_after_ohm_per_sq": modeled_rsh_after,
                "clamped_to_bounds": clamped,
            }
        )

    inactive_support_power_arr = np.asarray(inactive_support_power, dtype=float)
    inactive_support_fraction_arr = np.asarray(inactive_support_fraction, dtype=float)

    for row in high_records:
        inactive_fraction = _interp_hold(
            inactive_support_power_arr,
            inactive_support_fraction_arr,
            row["power_w"],
        )
        fixed_active_cm3 = (
            row["final_active_component_cm3"]
            + inactive_fraction * row["final_inactive_component_cm3"]
        )
        fraction_injected, modeled_rsh_after, clamped = _solve_activation_fraction(
            depth_m=row["depth_m"],
            fixed_active_cm3=fixed_active_cm3,
            scalable_component_cm3=row["final_injected_component_cm3"],
            background_ga_cm3=row["background_ga_cm3"],
            mobility_model=mobility_model,
            target_rsh_ohm_per_sq=row["measured_rsh_after_ohm_per_sq"],
        )
        calibration_rows.append(
            {
                "power_w": row["power_w"],
                "regime": "injected_fit_with_inactive_curve",
                "measured_rsh_before_ohm_per_sq": row["measured_rsh_before_ohm_per_sq"],
                "measured_rsh_after_ohm_per_sq": row["measured_rsh_after_ohm_per_sq"],
                "final_injected_component_sheet_dose_cm2": row["final_injected_component_sheet_dose_cm2"],
                "effective_final_inactive_activation_fraction": inactive_fraction,
                "effective_final_injected_activation_fraction": fraction_injected,
                "modeled_rsh_after_ohm_per_sq": modeled_rsh_after,
                "clamped_to_bounds": clamped,
            }
        )

    calibration_rows.sort(key=lambda item: item["power_w"])

    activation_csv = output_dir / "dual_channel_activation_model.csv"
    with activation_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "power_w",
                "effective_final_inactive_activation_fraction",
                "effective_final_injected_activation_fraction",
                "regime",
                "measured_rsh_before_ohm_per_sq",
                "final_injected_component_sheet_dose_cm2",
                "measured_rsh_after_ohm_per_sq",
                "modeled_rsh_after_ohm_per_sq",
                "clamped_to_bounds",
            ],
        )
        writer.writeheader()
        writer.writerows(calibration_rows)

    summary = {
        "target_initial_rsh_ohm_per_sq": target_initial_rsh,
        "modeled_initial_rsh_ohm_per_sq": modeled_initial_rsh,
        "initial_inactive_activation_fraction": f_init,
        "initial_fraction_clamped_to_bounds": init_clamped,
        "injection_threshold_cm2": args.injection_threshold_cm2,
        "low_injection_powers_w": [row["power_w"] for row in low_records],
        "high_injection_powers_w": [row["power_w"] for row in high_records],
        "activation_model_csv": str(activation_csv),
    }
    with (output_dir / "calibration_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)

    comparison_csv = output_dir / "measured_vs_modeled_rsh.csv"
    with comparison_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "power_w",
                "measured_rsh_before_ohm_per_sq",
                "target_initial_rsh_ohm_per_sq",
                "modeled_initial_rsh_ohm_per_sq",
                "measured_rsh_after_ohm_per_sq",
                "modeled_rsh_after_ohm_per_sq",
                "effective_final_inactive_activation_fraction",
                "effective_final_injected_activation_fraction",
                "regime",
                "final_injected_component_sheet_dose_cm2",
            ],
        )
        writer.writeheader()
        for row in calibration_rows:
            writer.writerow(
                {
                    "power_w": row["power_w"],
                    "measured_rsh_before_ohm_per_sq": measured[row["power_w"]]["measured_rsh_before_ohm_per_sq"],
                    "target_initial_rsh_ohm_per_sq": target_initial_rsh,
                    "modeled_initial_rsh_ohm_per_sq": modeled_initial_rsh,
                    "measured_rsh_after_ohm_per_sq": row["measured_rsh_after_ohm_per_sq"],
                    "modeled_rsh_after_ohm_per_sq": row["modeled_rsh_after_ohm_per_sq"],
                    "effective_final_inactive_activation_fraction": row["effective_final_inactive_activation_fraction"],
                    "effective_final_injected_activation_fraction": row["effective_final_injected_activation_fraction"],
                    "regime": row["regime"],
                    "final_injected_component_sheet_dose_cm2": row["final_injected_component_sheet_dose_cm2"],
                }
            )

    figure, axis = plt.subplots(figsize=(8.0, 4.8))
    powers = [row["power_w"] for row in calibration_rows]
    axis.plot(
        powers,
        [row["effective_final_inactive_activation_fraction"] for row in calibration_rows],
        marker="o",
        label="Inactive re-activation fraction",
    )
    axis.plot(
        powers,
        [row["effective_final_injected_activation_fraction"] for row in calibration_rows],
        marker="s",
        label="Injected-P activation fraction",
    )
    axis.set_xlabel("Average Laser Power (W)")
    axis.set_ylabel("Activation fraction")
    axis.set_title("Dual-Channel Activation Calibration")
    axis.set_ylim(bottom=0.0)
    axis.grid(alpha=0.25)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_dir / "dual_channel_activation_fractions.png", dpi=220)
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(8.0, 4.8))
    axis.plot(
        powers,
        [row["measured_rsh_after_ohm_per_sq"] for row in calibration_rows],
        marker="o",
        label="Measured Rsh after laser",
    )
    axis.plot(
        powers,
        [row["modeled_rsh_after_ohm_per_sq"] for row in calibration_rows],
        marker="s",
        linestyle="--",
        label="Dual-channel modeled Rsh after laser",
    )
    axis.set_xlabel("Average Laser Power (W)")
    axis.set_ylabel("Sheet resistance (ohm/sq)")
    axis.set_title("Measured vs Dual-Channel Activation Model")
    axis.grid(alpha=0.25)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_dir / "measured_vs_dual_channel_rsh.png", dpi=220)
    plt.close(figure)

    print(f"Saved dual-channel activation calibration to: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
