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

from laser_doping_sim import SubstrateDoping, SurfaceSourceLayer
from laser_doping_sim.phase1_thermal import LaserPulse, MaterialProperties
from laser_doping_sim.phase3_stack_thermal import (
    PSGLayerProperties,
    StackDomain1D,
    StackOpticalProperties,
    effective_surface_reflectance,
    run_stack_simulation,
    save_outputs as save_stack_outputs,
    silicon_subdomain_view,
)
from run_phase3 import _fluence_j_cm2, _texture_interface_area_factor


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run a single-pulse thermal simulation out to one full laser period so we can "
            "measure residual heating before the next pulse."
        )
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/phase3/single_cycle_cooling_check",
    )
    parser.add_argument("--powers-w", type=float, nargs="*", default=None)
    parser.add_argument("--power-start-w", type=float, default=30.0)
    parser.add_argument("--power-stop-w", type=float, default=90.0)
    parser.add_argument("--power-step-w", type=float, default=30.0)
    parser.add_argument("--repetition-rate-hz", type=float, default=500000.0)
    parser.add_argument("--spot-shape", choices=["square_flat_top", "circular_flat_top"], default="square_flat_top")
    parser.add_argument("--square-side-um", type=float, default=95.0)
    parser.add_argument("--spot-diameter-um", type=float, default=117.85536026233771)
    parser.add_argument("--fluence-j-cm2", type=float, default=None)
    parser.add_argument("--pulse-fwhm-ns", type=float, default=10.0)
    parser.add_argument("--peak-time-ns", type=float, default=30.0)
    parser.add_argument("--surface-reflectance", type=float, default=0.09)
    parser.add_argument("--texture-reflectance-multiplier", type=float, default=1.0)
    parser.add_argument("--interface-transmission", type=float, default=0.68)
    parser.add_argument("--psg-absorption-depth-um", type=float, default=50.0)
    parser.add_argument("--si-absorption-depth-nm", type=float, default=1274.0)
    parser.add_argument("--psg-thickness-nm", type=float, default=150.0)
    parser.add_argument("--psg-rho", type=float, default=2200.0)
    parser.add_argument("--psg-cp", type=float, default=730.0)
    parser.add_argument("--psg-k", type=float, default=1.4)
    parser.add_argument("--si-thickness-um", type=float, default=8.0)
    parser.add_argument("--nz", type=int, default=1200)
    parser.add_argument("--dt-ns", type=float, default=0.2)
    parser.add_argument(
        "--t-end-ns",
        type=float,
        default=None,
        help="If omitted, run to one full pulse period derived from repetition-rate-hz.",
    )
    parser.add_argument(
        "--sample-times-ns",
        type=float,
        nargs="+",
        default=[400.0],
        help="Extra time samples to record, in addition to the cycle end.",
    )
    parser.add_argument("--ambient-temp-k", type=float, default=300.0)
    parser.add_argument("--melt-temp-k", type=float, default=1687.0)
    parser.add_argument("--mushy-width-k", type=float, default=20.0)
    parser.add_argument("--bottom-bc", choices=["dirichlet", "neumann"], default="dirichlet")
    parser.add_argument("--source-kind", default="PSG")
    parser.add_argument("--source-dopant", default="P")
    parser.add_argument("--source-dopant-concentration-cm3", type=float, default=4.5913166904198945e21)
    parser.add_argument(
        "--source-notes",
        default=(
            "Single-cycle cooling check: PSG is treated as a P-rich SiO2 source layer "
            "only so the thermal stack matches the mainline Phase 3 cases."
        ),
    )
    parser.add_argument("--substrate-dopant", default="Ga")
    parser.add_argument("--substrate-dopant-concentration-cm3", type=float, default=1.0e16)
    parser.add_argument("--substrate-notes", default="Background acceptor concentration retained for metadata consistency.")
    parser.add_argument("--texture-interface-area-factor", type=float, default=None)
    parser.add_argument("--texture-pyramid-sidewall-angle-deg", type=float, default=None)
    return parser


def _power_values(args: argparse.Namespace) -> list[float]:
    if args.powers_w:
        return [float(power) for power in args.powers_w]
    if args.power_step_w <= 0.0:
        raise ValueError("power_step_w must be positive.")
    values: list[float] = []
    current = args.power_start_w
    epsilon = args.power_step_w * 1.0e-6
    while current <= args.power_stop_w + epsilon:
        values.append(round(current, 10))
        current += args.power_step_w
    return values


def _sample_at_time_ns(time_s: np.ndarray, values: np.ndarray, sample_time_ns: float) -> float:
    return float(np.interp(sample_time_ns * 1.0e-9, time_s, values))


def _cooling_fraction(ambient_k: float, peak_k: float, current_k: float) -> float:
    denominator = peak_k - ambient_k
    if denominator <= 0.0:
        return 1.0
    return float(np.clip((current_k - ambient_k) / denominator, 0.0, 1.0))


def _plot_case_surface_temperatures(
    time_s: np.ndarray,
    stack_surface_k: np.ndarray,
    si_surface_k: np.ndarray,
    ambient_k: float,
    cycle_end_ns: float,
    sample_times_ns: list[float],
    path: Path,
) -> None:
    figure, axis = plt.subplots(figsize=(8.5, 4.8))
    axis.plot(time_s * 1.0e9, stack_surface_k, lw=2.0, color="#c0392b", label="Stack surface")
    axis.plot(time_s * 1.0e9, si_surface_k, lw=2.0, color="#1e8449", label="Silicon surface")
    axis.axhline(ambient_k, lw=1.0, ls="--", color="black", label="Ambient")
    for sample_time_ns in sample_times_ns + [cycle_end_ns]:
        axis.axvline(sample_time_ns, lw=1.0, ls=":", color="#7f8c8d")
    axis.set_xlabel("Time (ns)")
    axis.set_ylabel("Temperature (K)")
    axis.set_title("Single-Cycle Surface Cooling Check")
    axis.grid(alpha=0.25)
    axis.legend()
    figure.tight_layout()
    figure.savefig(path, dpi=220)
    plt.close(figure)


def _plot_metric(
    powers_w: np.ndarray,
    values: np.ndarray,
    ylabel: str,
    title: str,
    path: Path,
    color: str,
) -> None:
    figure, axis = plt.subplots(figsize=(7.2, 4.4))
    axis.plot(powers_w, values, marker="o", lw=2.0, color=color)
    axis.set_xlabel("Average Power (W)")
    axis.set_ylabel(ylabel)
    axis.set_title(title)
    axis.grid(alpha=0.25)
    figure.tight_layout()
    figure.savefig(path, dpi=220)
    plt.close(figure)


def _run_single_power(
    args: argparse.Namespace,
    power_w: float,
    cycle_end_ns: float,
    output_root: Path,
) -> dict:
    fluence_j_cm2, pulse_energy_j, spot_area_cm2 = _fluence_j_cm2(
        average_power_w=power_w,
        repetition_rate_hz=args.repetition_rate_hz,
        spot_shape=args.spot_shape,
        square_side_um=args.square_side_um,
        spot_diameter_um=args.spot_diameter_um,
        fluence_override_j_cm2=args.fluence_j_cm2,
    )
    _texture_interface_area_factor(
        texture_interface_area_factor=args.texture_interface_area_factor,
        texture_pyramid_sidewall_angle_deg=args.texture_pyramid_sidewall_angle_deg,
    )

    silicon_material = MaterialProperties(
        melt_temp=args.melt_temp_k,
        mushy_width=args.mushy_width_k,
    )
    psg_material = PSGLayerProperties(
        rho=args.psg_rho,
        cp=args.psg_cp,
        k=args.psg_k,
        thickness=args.psg_thickness_nm * 1.0e-9,
    )
    optics = StackOpticalProperties(
        surface_reflectance=args.surface_reflectance,
        texture_reflectance_multiplier=args.texture_reflectance_multiplier,
        interface_transmission=args.interface_transmission,
        psg_absorption_depth=args.psg_absorption_depth_um * 1.0e-6,
        si_absorption_depth=args.si_absorption_depth_nm * 1.0e-9,
    )
    pulse = LaserPulse(
        fluence=fluence_j_cm2 * 1.0e4,
        pulse_fwhm=args.pulse_fwhm_ns * 1.0e-9,
        peak_time=args.peak_time_ns * 1.0e-9,
        absorptivity=1.0 - effective_surface_reflectance(optics),
        absorption_depth=args.si_absorption_depth_nm * 1.0e-9,
    )
    domain = StackDomain1D(
        silicon_thickness=args.si_thickness_um * 1.0e-6,
        nz=args.nz,
        dt=args.dt_ns * 1.0e-9,
        t_end=cycle_end_ns * 1.0e-9,
        ambient_temp=args.ambient_temp_k,
        bottom_bc=args.bottom_bc,
    )
    source_layer = SurfaceSourceLayer(
        kind=args.source_kind,
        dopant=args.source_dopant,
        dopant_concentration_cm3=args.source_dopant_concentration_cm3,
        notes=args.source_notes,
    )
    substrate_doping = SubstrateDoping(
        species=args.substrate_dopant,
        concentration_cm3=args.substrate_dopant_concentration_cm3,
        notes=args.substrate_notes,
    )

    case_dir = output_root / f"p{int(round(power_w))}w"
    result = run_stack_simulation(
        domain=domain,
        silicon_material=silicon_material,
        psg_material=psg_material,
        pulse=pulse,
        optics=optics,
        surface_source=source_layer,
        substrate_doping=substrate_doping,
    )
    thermal_output = save_stack_outputs(result, case_dir / "thermal")
    silicon_view = silicon_subdomain_view(result)

    stack_surface_k = result.temperature[:, 0]
    si_surface_k = silicon_view.temperature[:, 0]
    peak_stack_surface_k = float(np.max(stack_surface_k))
    peak_si_surface_k = float(np.max(si_surface_k))
    cycle_end_stack_surface_k = float(stack_surface_k[-1])
    cycle_end_si_surface_k = float(si_surface_k[-1])

    melted = result.melt_depth > 0.0
    melt_start_ns = float(result.time[melted][0] * 1.0e9) if np.any(melted) else None
    melt_end_ns = float(result.time[melted][-1] * 1.0e9) if np.any(melted) else None

    row = {
        "power_w": float(power_w),
        "repetition_rate_hz": float(args.repetition_rate_hz),
        "cycle_end_ns": float(cycle_end_ns),
        "dt_ns": float(args.dt_ns),
        "pulse_energy_uj": float(pulse_energy_j * 1.0e6),
        "fluence_j_cm2": float(fluence_j_cm2),
        "spot_area_cm2": float(spot_area_cm2),
        "ambient_temp_k": float(args.ambient_temp_k),
        "peak_stack_surface_temperature_k": peak_stack_surface_k,
        "peak_silicon_surface_temperature_k": peak_si_surface_k,
        "max_melt_depth_nm": float(np.max(result.melt_depth) * 1.0e9),
        "melt_start_ns": melt_start_ns,
        "melt_end_ns": melt_end_ns,
        "cycle_end_stack_surface_temperature_k": cycle_end_stack_surface_k,
        "cycle_end_silicon_surface_temperature_k": cycle_end_si_surface_k,
        "cycle_end_stack_residual_k": float(cycle_end_stack_surface_k - args.ambient_temp_k),
        "cycle_end_silicon_residual_k": float(cycle_end_si_surface_k - args.ambient_temp_k),
        "cycle_end_stack_cooling_fraction_of_peak": _cooling_fraction(
            args.ambient_temp_k,
            peak_stack_surface_k,
            cycle_end_stack_surface_k,
        ),
        "cycle_end_silicon_cooling_fraction_of_peak": _cooling_fraction(
            args.ambient_temp_k,
            peak_si_surface_k,
            cycle_end_si_surface_k,
        ),
    }

    for sample_time_ns in args.sample_times_ns:
        sample_label = str(int(round(sample_time_ns)))
        row[f"stack_surface_temp_{sample_label}ns_k"] = _sample_at_time_ns(
            result.time,
            stack_surface_k,
            sample_time_ns,
        )
        row[f"silicon_surface_temp_{sample_label}ns_k"] = _sample_at_time_ns(
            result.time,
            si_surface_k,
            sample_time_ns,
        )

    _plot_case_surface_temperatures(
        time_s=result.time,
        stack_surface_k=stack_surface_k,
        si_surface_k=si_surface_k,
        ambient_k=args.ambient_temp_k,
        cycle_end_ns=cycle_end_ns,
        sample_times_ns=[float(value) for value in args.sample_times_ns],
        path=thermal_output / "surface_temperature_cycle_check.png",
    )

    return row


def _save_summary(rows: list[dict], output_root: Path) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    csv_path = output_root / "single_cycle_cooling_summary.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    json_path = output_root / "single_cycle_cooling_summary.json"
    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(rows, handle, indent=2)

    powers = np.array([row["power_w"] for row in rows], dtype=float)
    _plot_metric(
        powers,
        np.array([row["peak_silicon_surface_temperature_k"] for row in rows], dtype=float),
        "Peak Si Surface Temperature (K)",
        "Single-Cycle Check: Peak Silicon Surface Temperature",
        output_root / "power_vs_peak_si_surface_temperature.png",
        "#b03a2e",
    )
    _plot_metric(
        powers,
        np.array([row["cycle_end_silicon_residual_k"] for row in rows], dtype=float),
        "Cycle-End Si Residual Temperature (K)",
        "Single-Cycle Check: Residual Silicon Heating at Next Pulse",
        output_root / "power_vs_cycle_end_si_residual.png",
        "#1e8449",
    )
    _plot_metric(
        powers,
        np.array([row["max_melt_depth_nm"] for row in rows], dtype=float),
        "Max Melt Depth (nm)",
        "Single-Cycle Check: Melt Depth",
        output_root / "power_vs_max_melt_depth.png",
        "#2471a3",
    )


def main() -> int:
    args = build_parser().parse_args()
    powers = _power_values(args)
    output_root = ROOT / args.output_dir
    output_root.mkdir(parents=True, exist_ok=True)

    if args.repetition_rate_hz <= 0.0:
        raise ValueError("repetition_rate_hz must be positive.")
    cycle_end_ns = args.t_end_ns if args.t_end_ns is not None else 1.0e9 / args.repetition_rate_hz

    rows = [
        _run_single_power(
            args=args,
            power_w=power_w,
            cycle_end_ns=cycle_end_ns,
            output_root=output_root,
        )
        for power_w in powers
    ]
    rows.sort(key=lambda row: row["power_w"])
    _save_summary(rows, output_root)

    manifest = {
        "output_dir": str(output_root),
        "powers_w": [float(power) for power in powers],
        "repetition_rate_hz": float(args.repetition_rate_hz),
        "derived_cycle_end_ns": float(cycle_end_ns),
        "sample_times_ns": [float(value) for value in args.sample_times_ns],
        "notes": (
            "This tool extends the single-pulse thermal solve to one full pulse period so we can "
            "inspect residual heating before a second pulse arrives."
        ),
    }
    with (output_root / "single_cycle_cooling_manifest.json").open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)

    print(f"Saved single-cycle cooling check to: {output_root}")
    print(f"Cycle end used: {cycle_end_ns:.3f} ns")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
