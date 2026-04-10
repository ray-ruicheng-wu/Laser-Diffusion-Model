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
from scipy.optimize import least_squares


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
            "Refit the high-power tail of the dual-channel activation model by "
            "anchoring to the low-power curve at a boundary power and solving a "
            "linear rollover for inactive re-activation plus a linear ramp for "
            "injected-P activation."
        )
    )
    parser.add_argument(
        "--case-dirs",
        nargs="+",
        required=True,
        help="Phase 3 case directories used in the high-power refit, including the boundary case.",
    )
    parser.add_argument(
        "--measured-rsh-csv",
        required=True,
        help="CSV containing columns power_w and measured_rsh_after_ohm_per_sq.",
    )
    parser.add_argument(
        "--base-activation-csv",
        required=True,
        help="Existing dual-channel activation CSV used as the low-power anchor model.",
    )
    parser.add_argument(
        "--initial-inactive-activation-fraction",
        type=float,
        required=True,
        help="Initial inactive activation fraction used when loading the base activation table.",
    )
    parser.add_argument(
        "--boundary-power-w",
        type=float,
        default=48.0,
        help="Power at which the low-power dual-channel model is held fixed and the high-power refit begins.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Output directory for the refitted activation model and diagnostics.",
    )
    parser.add_argument(
        "--measurement-temperature-k",
        type=float,
        default=300.0,
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
            values[float(row["power_w"])] = float(row["measured_rsh_after_ohm_per_sq"])
    return values


def _rerun_components(case_dir: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float]:
    (
        depth_m,
        _initial_active_cm3,
        _initial_inactive_cm3,
        final_active_component_cm3,
        background_ga_cm3,
        final_inactive_component_cm3,
        final_injected_component_cm3,
    ) = rsh_cases._rerun_component_profiles(case_dir)
    return (
        depth_m,
        final_active_component_cm3,
        final_inactive_component_cm3,
        final_injected_component_cm3,
        background_ga_cm3,
    )


def _write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


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

    boundary_power_w = float(args.boundary_power_w)
    if boundary_power_w not in case_powers:
        raise ValueError("Boundary power case must be included in --case-dirs.")

    fit_powers = sorted(power for power in case_powers if power > boundary_power_w)
    if not fit_powers:
        raise ValueError("At least one high-power case above boundary_power_w is required.")
    if any(power not in measured_rsh for power in fit_powers):
        missing = [power for power in fit_powers if power not in measured_rsh]
        raise ValueError(f"Missing measured Rsh entries for powers: {missing}")

    end_power_w = float(max(fit_powers))
    span_w = end_power_w - boundary_power_w
    if span_w <= 0.0:
        raise ValueError("End power must be above the boundary power.")

    components = {
        power: _rerun_components(case_dir)
        for power, case_dir in sorted(case_powers.items())
    }

    boundary_inactive_fraction = base_model.inactive_fraction_at_power(boundary_power_w)

    def inactive_fraction_at_power(power_w: float, inactive_end_fraction: float) -> float:
        if power_w <= boundary_power_w:
            return base_model.inactive_fraction_at_power(power_w)
        alpha = (power_w - boundary_power_w) / span_w
        return float((1.0 - alpha) * boundary_inactive_fraction + alpha * inactive_end_fraction)

    def injected_fraction_at_power(power_w: float, injected_end_fraction: float) -> float:
        if power_w <= boundary_power_w:
            return base_model.injected_fraction_at_power(power_w)
        alpha = (power_w - boundary_power_w) / span_w
        return float(alpha * injected_end_fraction)

    def modeled_rsh(power_w: float, inactive_end_fraction: float, injected_end_fraction: float) -> float:
        depth_m, final_active_cm3, final_inactive_cm3, final_injected_cm3, background_ga_cm3 = components[power_w]
        profile = (
            final_active_cm3
            + inactive_fraction_at_power(power_w, inactive_end_fraction) * final_inactive_cm3
            + injected_fraction_at_power(power_w, injected_end_fraction) * final_injected_cm3
        )
        return sheet_resistance_ohm_per_sq(
            depth_m,
            profile,
            background_ga_cm3,
            mobility_model=mobility_model,
        )

    def residuals(x: np.ndarray) -> np.ndarray:
        inactive_end_fraction = float(x[0])
        injected_end_fraction = float(x[1])
        return np.asarray(
            [
                modeled_rsh(power_w, inactive_end_fraction, injected_end_fraction) - measured_rsh[power_w]
                for power_w in fit_powers
            ],
            dtype=float,
        )

    solution = least_squares(
        residuals,
        x0=np.array([min(boundary_inactive_fraction, 0.5), 0.05], dtype=float),
        bounds=(0.0, 1.0),
    )
    inactive_end_fraction = float(solution.x[0])
    injected_end_fraction = float(solution.x[1])

    base_rows: list[dict] = []
    with (ROOT / args.base_activation_csv).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            power_w = float(row["power_w"])
            if power_w <= boundary_power_w:
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

    refit_rows = []
    for power_w in fit_powers:
        refit_rows.append(
            {
                "power_w": power_w,
                "effective_final_inactive_activation_fraction": inactive_fraction_at_power(
                    power_w, inactive_end_fraction
                ),
                "effective_final_injected_activation_fraction": injected_fraction_at_power(
                    power_w, injected_end_fraction
                ),
                "regime": "high_power_refit",
            }
        )

    combined_rows = sorted(base_rows + refit_rows, key=lambda row: row["power_w"])

    model_csv = output_dir / "dual_channel_activation_model_refit.csv"
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

    comparison_rows = []
    for power_w in sorted(case_powers):
        inactive_fraction = (
            base_model.inactive_fraction_at_power(power_w)
            if power_w <= boundary_power_w
            else inactive_fraction_at_power(power_w, inactive_end_fraction)
        )
        injected_fraction = (
            base_model.injected_fraction_at_power(power_w)
            if power_w <= boundary_power_w
            else injected_fraction_at_power(power_w, injected_end_fraction)
        )
        modeled = modeled_rsh(power_w, inactive_end_fraction, injected_end_fraction)
        comparison_rows.append(
            {
                "power_w": power_w,
                "measured_rsh_after_ohm_per_sq": measured_rsh.get(power_w),
                "modeled_rsh_after_ohm_per_sq": modeled,
                "effective_final_inactive_activation_fraction": inactive_fraction,
                "effective_final_injected_activation_fraction": injected_fraction,
            }
        )

    comparison_csv = output_dir / "measured_vs_modeled_rsh_refit.csv"
    _write_csv(
        comparison_csv,
        comparison_rows,
        [
            "power_w",
            "measured_rsh_after_ohm_per_sq",
            "modeled_rsh_after_ohm_per_sq",
            "effective_final_inactive_activation_fraction",
            "effective_final_injected_activation_fraction",
        ],
    )

    summary = {
        "boundary_power_w": boundary_power_w,
        "boundary_inactive_fraction": boundary_inactive_fraction,
        "fit_powers_w": fit_powers,
        "high_power_inactive_end_fraction": inactive_end_fraction,
        "high_power_injected_end_fraction": injected_end_fraction,
        "solution_cost": float(solution.cost),
        "solution_success": bool(solution.success),
        "model_csv": str(model_csv),
        "comparison_csv": str(comparison_csv),
    }
    with (output_dir / "high_power_refit_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)

    powers = np.array([row["power_w"] for row in combined_rows], dtype=float)
    inactive_values = np.array(
        [row["effective_final_inactive_activation_fraction"] for row in combined_rows],
        dtype=float,
    )
    injected_values = np.array(
        [row["effective_final_injected_activation_fraction"] for row in combined_rows],
        dtype=float,
    )
    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    ax.plot(powers, inactive_values, marker="o", lw=2.0, label="Inactive re-activation")
    ax.plot(powers, injected_values, marker="o", lw=2.0, label="Injected P activation")
    ax.set_xlabel("Average Power (W)")
    ax.set_ylabel("Activation Fraction")
    ax.set_title("Refit Dual-Channel Activation Model")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "dual_channel_activation_refit.png", dpi=220)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    fit_plot_powers = np.array([row["power_w"] for row in comparison_rows], dtype=float)
    measured_values = np.array([row["measured_rsh_after_ohm_per_sq"] for row in comparison_rows], dtype=float)
    modeled_values = np.array([row["modeled_rsh_after_ohm_per_sq"] for row in comparison_rows], dtype=float)
    ax.plot(fit_plot_powers, measured_values, marker="o", lw=2.0, label="Measured Rsh")
    ax.plot(fit_plot_powers, modeled_values, marker="o", lw=2.0, label="Refit model Rsh")
    ax.set_xlabel("Average Power (W)")
    ax.set_ylabel("Sheet Resistance (ohm/sq)")
    ax.set_title("High-Power Dual-Channel Refit")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "measured_vs_refit_rsh.png", dpi=220)
    plt.close(fig)

    print(f"Saved high-power refit to: {output_dir}")
    print(f"High-power inactive end fraction: {inactive_end_fraction:.6f}")
    print(f"High-power injected end fraction: {injected_end_fraction:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
