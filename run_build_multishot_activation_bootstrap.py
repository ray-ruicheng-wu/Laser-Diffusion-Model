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


DEFAULT_BASE_ACTIVATION_CSV = (
    "outputs/phase3/dual_channel_monotonic_segment_refit_48_60w_dt005_allstates/"
    "dual_channel_activation_model_monotonic_segment_refit.csv"
)
DEFAULT_POWER_SCAN_SUMMARY_CSV = (
    "outputs/phase3/power_scan_20_60w_dt005_measured_ctv_psg_eq_sims_allstates_rerun_20260413/"
    "power_scan_summary.csv"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Bootstrap a new multi-shot dual-channel activation parameter table from the current "
            "single-shot activation table and the single-shot chemistry scan."
        )
    )
    parser.add_argument("--base-activation-csv", default=DEFAULT_BASE_ACTIVATION_CSV)
    parser.add_argument("--power-scan-summary-csv", default=DEFAULT_POWER_SCAN_SUMMARY_CSV)
    parser.add_argument("--output-dir", default="outputs/phase4/multishot_activation_bootstrap")
    parser.add_argument(
        "--inactive-headroom-fraction",
        type=float,
        default=0.20,
        help="Fraction of remaining headroom to 1.0 used to define eta_inactive_inf from eta_inactive_shot1.",
    )
    parser.add_argument(
        "--inactive-n0-shots",
        type=float,
        default=3.0,
        help="Default characteristic shot count for inactive re-activation saturation.",
    )
    parser.add_argument(
        "--injected-inf-fraction-of-inactive",
        type=float,
        default=0.25,
        help="Set eta_injected_inf to this fraction of eta_inactive_inf, clipped above eta_injected_shot1.",
    )
    parser.add_argument(
        "--injected-q0-multiple",
        type=float,
        default=2.0,
        help="Set q0_injected_cm2 = max(q0_floor, injected_q0_multiple * qref_injected_cm2).",
    )
    parser.add_argument(
        "--injected-q0-floor-cm2",
        type=float,
        default=1.0e14,
        help="Minimum q0_injected_cm2 used when the single-shot injected dose is very small.",
    )
    parser.add_argument(
        "--preview-powers-w",
        type=float,
        nargs="*",
        default=[30.0, 60.0],
    )
    parser.add_argument("--preview-max-shots", type=int, default=10)
    return parser


def _load_single_shot_activation(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {
            "power_w",
            "effective_final_inactive_activation_fraction",
            "effective_final_injected_activation_fraction",
        }
        if not required.issubset(set(reader.fieldnames or [])):
            raise ValueError(
                "Base single-shot activation CSV must contain columns: "
                "power_w,effective_final_inactive_activation_fraction,effective_final_injected_activation_fraction"
            )
        for row in reader:
            rows.append(
                {
                    "power_w": float(row["power_w"]),
                    "eta_inactive_shot1": float(row["effective_final_inactive_activation_fraction"]),
                    "eta_injected_shot1": float(row["effective_final_injected_activation_fraction"]),
                    "regime": row.get("regime", ""),
                }
            )
    rows.sort(key=lambda item: item["power_w"])
    return rows


def _load_power_scan_summary(path: Path) -> dict[float, dict]:
    rows: dict[float, dict] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"power_w", "cumulative_injected_dose_cm2"}
        if not required.issubset(set(reader.fieldnames or [])):
            raise ValueError(
                "Power scan summary CSV must contain at least power_w and cumulative_injected_dose_cm2."
            )
        for row in reader:
            power_w = float(row["power_w"])
            rows[power_w] = {
                "cumulative_injected_dose_cm2": float(row["cumulative_injected_dose_cm2"]),
                "max_liquid_fraction": float(row.get("max_liquid_fraction") or 0.0),
            }
    return rows


def _bootstrap_rows(
    base_rows: list[dict],
    scan_rows: dict[float, dict],
    inactive_headroom_fraction: float,
    inactive_n0_shots: float,
    injected_inf_fraction_of_inactive: float,
    injected_q0_multiple: float,
    injected_q0_floor_cm2: float,
) -> list[dict]:
    rows: list[dict] = []
    for row in base_rows:
        power_w = row["power_w"]
        if power_w not in scan_rows:
            continue
        eta_inactive_shot1 = float(np.clip(row["eta_inactive_shot1"], 0.0, 1.0))
        eta_injected_shot1 = float(np.clip(row["eta_injected_shot1"], 0.0, 1.0))
        qref_injected_cm2 = max(float(scan_rows[power_w]["cumulative_injected_dose_cm2"]), 0.0)
        eta_inactive_inf = float(
            np.clip(
                eta_inactive_shot1 + inactive_headroom_fraction * (1.0 - eta_inactive_shot1),
                eta_inactive_shot1,
                1.0,
            )
        )
        eta_injected_inf = float(
            np.clip(
                max(eta_injected_shot1, injected_inf_fraction_of_inactive * eta_inactive_inf),
                eta_injected_shot1,
                1.0,
            )
        )
        q0_injected_cm2 = float(max(injected_q0_floor_cm2, injected_q0_multiple * qref_injected_cm2))
        rows.append(
            {
                "power_w": power_w,
                "eta_inactive_shot1": eta_inactive_shot1,
                "eta_inactive_inf": eta_inactive_inf,
                "n0_inactive_shots": float(inactive_n0_shots),
                "eta_injected_shot1": eta_injected_shot1,
                "eta_injected_inf": eta_injected_inf,
                "qref_injected_cm2": qref_injected_cm2,
                "q0_injected_cm2": q0_injected_cm2,
                "notes": (
                    "Bootstrap from single-shot activation table plus single-shot chemistry scan. "
                    "Shot1 values are inherited exactly from the old table."
                ),
            }
        )
    if not rows:
        raise ValueError("No overlapping powers found between the single-shot activation table and power scan summary.")
    rows.sort(key=lambda item: item["power_w"])
    return rows


def _interp(values_x: np.ndarray, values_y: np.ndarray, x: float) -> float:
    return float(np.interp(float(x), values_x, values_y, left=values_y[0], right=values_y[-1]))


def _inactive_fraction(row: dict, shot_index: int) -> float:
    extra_shots = max(int(shot_index) - 1, 0)
    n0 = max(float(row["n0_inactive_shots"]), 1.0e-12)
    eta1 = float(row["eta_inactive_shot1"])
    eta_inf = float(row["eta_inactive_inf"])
    return float(np.clip(eta1 + (eta_inf - eta1) * (1.0 - np.exp(-extra_shots / n0)), 0.0, 1.0))


def _injected_fraction(row: dict, cumulative_injected_dose_cm2: float) -> float:
    eta1 = float(row["eta_injected_shot1"])
    eta_inf = float(row["eta_injected_inf"])
    qref = max(float(row["qref_injected_cm2"]), 0.0)
    q0 = float(row["q0_injected_cm2"])
    extra_dose = max(float(cumulative_injected_dose_cm2) - qref, 0.0)
    if q0 <= 0.0:
        return eta_inf if extra_dose > 0.0 else eta1
    return float(np.clip(eta1 + (eta_inf - eta1) * (1.0 - np.exp(-extra_dose / q0)), 0.0, 1.0))


def _save_rows(rows: list[dict], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "multishot_dual_channel_params.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    with (output_dir / "multishot_dual_channel_params.json").open("w", encoding="utf-8") as handle:
        json.dump(rows, handle, indent=2)
    return csv_path


def _save_preview(rows: list[dict], preview_powers_w: list[float], preview_max_shots: int, output_dir: Path) -> None:
    power_axis = np.array([row["power_w"] for row in rows], dtype=float)
    inactive_shot1 = np.array([row["eta_inactive_shot1"] for row in rows], dtype=float)
    inactive_inf = np.array([row["eta_inactive_inf"] for row in rows], dtype=float)
    qref = np.array([row["qref_injected_cm2"] for row in rows], dtype=float)
    q0 = np.array([row["q0_injected_cm2"] for row in rows], dtype=float)
    injected_inf = np.array([row["eta_injected_inf"] for row in rows], dtype=float)

    figure, axis = plt.subplots(figsize=(8.0, 4.8))
    axis.plot(power_axis, inactive_shot1, lw=2.0, color="#7d6608", label="eta_inactive_shot1")
    axis.plot(power_axis, inactive_inf, lw=2.0, color="#117864", label="eta_inactive_inf")
    axis.plot(power_axis, injected_inf, lw=2.0, color="#ca6f1e", label="eta_injected_inf")
    axis.set_xlabel("Power (W)")
    axis.set_ylabel("Activation Fraction")
    axis.set_title("Bootstrapped Multi-Shot Activation Parameter Curves")
    axis.grid(alpha=0.25)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_dir / "bootstrapped_multishot_activation_vs_power.png", dpi=220)
    plt.close(figure)

    if not preview_powers_w:
        return

    figure, axis = plt.subplots(figsize=(8.2, 4.8))
    shot_index = np.arange(1, preview_max_shots + 1, dtype=int)
    colors = ["#2471a3", "#ca6f1e", "#117864", "#7d3c98"]
    for color_index, preview_power_w in enumerate(preview_powers_w):
        row = {
            "eta_inactive_shot1": _interp(power_axis, inactive_shot1, preview_power_w),
            "eta_inactive_inf": _interp(power_axis, inactive_inf, preview_power_w),
            "n0_inactive_shots": _interp(power_axis, np.array([row["n0_inactive_shots"] for row in rows], dtype=float), preview_power_w),
            "eta_injected_shot1": _interp(power_axis, np.array([row["eta_injected_shot1"] for row in rows], dtype=float), preview_power_w),
            "eta_injected_inf": _interp(power_axis, injected_inf, preview_power_w),
            "qref_injected_cm2": _interp(power_axis, qref, preview_power_w),
            "q0_injected_cm2": _interp(power_axis, q0, preview_power_w),
        }
        inactive_curve = np.array([_inactive_fraction(row, int(shot)) for shot in shot_index], dtype=float)
        cumulative_dose = row["qref_injected_cm2"] * shot_index.astype(float)
        injected_curve = np.array([_injected_fraction(row, dose) for dose in cumulative_dose], dtype=float)
        axis.plot(
            shot_index,
            inactive_curve,
            lw=2.0,
            color=colors[color_index % len(colors)],
            label=f"{preview_power_w:.0f} W inactive",
        )
        axis.plot(
            shot_index,
            injected_curve,
            lw=2.0,
            ls="--",
            color=colors[color_index % len(colors)],
            label=f"{preview_power_w:.0f} W injected",
        )
    axis.set_xlabel("Shot Index")
    axis.set_ylabel("Activation Fraction")
    axis.set_title("Bootstrapped Multi-Shot Activation Preview")
    axis.grid(alpha=0.25)
    axis.legend(ncol=2)
    figure.tight_layout()
    figure.savefig(output_dir / "bootstrapped_multishot_activation_preview_vs_shot.png", dpi=220)
    plt.close(figure)


def main() -> int:
    args = build_parser().parse_args()
    output_dir = ROOT / args.output_dir
    base_rows = _load_single_shot_activation(ROOT / args.base_activation_csv)
    scan_rows = _load_power_scan_summary(ROOT / args.power_scan_summary_csv)
    rows = _bootstrap_rows(
        base_rows=base_rows,
        scan_rows=scan_rows,
        inactive_headroom_fraction=args.inactive_headroom_fraction,
        inactive_n0_shots=args.inactive_n0_shots,
        injected_inf_fraction_of_inactive=args.injected_inf_fraction_of_inactive,
        injected_q0_multiple=args.injected_q0_multiple,
        injected_q0_floor_cm2=args.injected_q0_floor_cm2,
    )
    csv_path = _save_rows(rows, output_dir)
    _save_preview(
        rows=rows,
        preview_powers_w=[float(value) for value in args.preview_powers_w],
        preview_max_shots=args.preview_max_shots,
        output_dir=output_dir,
    )

    manifest = {
        "base_activation_csv": str(ROOT / args.base_activation_csv),
        "power_scan_summary_csv": str(ROOT / args.power_scan_summary_csv),
        "output_csv": str(csv_path),
        "inactive_headroom_fraction": float(args.inactive_headroom_fraction),
        "inactive_n0_shots": float(args.inactive_n0_shots),
        "injected_inf_fraction_of_inactive": float(args.injected_inf_fraction_of_inactive),
        "injected_q0_multiple": float(args.injected_q0_multiple),
        "injected_q0_floor_cm2": float(args.injected_q0_floor_cm2),
    }
    with (output_dir / "bootstrap_manifest.json").open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)

    print(f"Saved multi-shot activation bootstrap table to: {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
