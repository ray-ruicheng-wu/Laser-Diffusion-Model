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
from laser_doping_sim.phase2_diffusion import DiffusionParameters, run_diffusion, save_outputs as save_diffusion_outputs
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
        description="Run a Phase 3 power scan and summarize thermal/diffusion trends."
    )
    parser.add_argument("--output-dir", default="outputs/phase3/power_scan_60_90w")
    parser.add_argument("--power-start-w", type=float, default=60.0)
    parser.add_argument("--power-stop-w", type=float, default=90.0)
    parser.add_argument("--power-step-w", type=float, default=5.0)
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
    parser.add_argument("--t-end-ns", type=float, default=400.0)
    parser.add_argument("--ambient-temp-k", type=float, default=300.0)
    parser.add_argument("--melt-temp-k", type=float, default=1687.0)
    parser.add_argument("--mushy-width-k", type=float, default=20.0)
    parser.add_argument("--bottom-bc", choices=["dirichlet", "neumann"], default="dirichlet")
    parser.add_argument("--source-kind", default="PSG")
    parser.add_argument("--source-dopant", default="P")
    parser.add_argument("--source-dopant-concentration-cm3", type=float, default=2.0e21)
    parser.add_argument(
        "--source-notes",
        default=(
            "Phase 3 surface source is phosphosilicate glass, modeled as a P2O5-SiO2 glass and collapsed into an "
            "effective phosphorus-rich SiO2 source layer."
        ),
    )
    parser.add_argument("--substrate-dopant", default="Ga")
    parser.add_argument("--substrate-dopant-concentration-cm3", type=float, default=1.0e16)
    parser.add_argument("--substrate-notes", default="Background acceptor concentration used to define junction depth.")
    parser.add_argument("--boundary-model", choices=["finite_source_cell", "robin_reservoir"], default="finite_source_cell")
    parser.add_argument("--source-exchange-mode", choices=["melt_only", "all_states"], default="all_states")
    parser.add_argument("--solid-diffusivity-m2-s", type=float, default=0.0)
    parser.add_argument("--solid-prefactor-cm2-s", type=float, default=8.0e-4)
    parser.add_argument("--solid-activation-energy-ev", type=float, default=2.74)
    parser.add_argument("--liquid-prefactor-cm2-s", type=float, default=1.4e-3)
    parser.add_argument("--liquid-activation-energy-ev", type=float, default=0.183)
    parser.add_argument("--interface-liquid-threshold", type=float, default=0.01)
    parser.add_argument("--source-effective-thickness-nm", type=float, default=100.0)
    parser.add_argument("--interfacial-transport-length-nm", type=float, default=100.0)
    parser.add_argument("--initial-profile-kind", choices=["none", "erfc_emitter", "measured"], default="erfc_emitter")
    parser.add_argument("--initial-profile-csv", default="")
    parser.add_argument("--initial-surface-p-concentration-cm3", type=float, default=3.5e20)
    parser.add_argument("--initial-junction-depth-nm", type=float, default=300.0)
    parser.add_argument("--initial-inactive-surface-p-concentration-cm3", type=float, default=5.0e20)
    parser.add_argument("--initial-inactive-surface-thickness-nm", type=float, default=30.0)
    parser.add_argument("--texture-interface-area-factor", type=float, default=None)
    parser.add_argument("--texture-pyramid-sidewall-angle-deg", type=float, default=None)
    return parser


def _power_values(start_w: float, stop_w: float, step_w: float) -> list[float]:
    if step_w <= 0.0:
        raise ValueError("power_step_w must be positive.")
    values: list[float] = []
    current = start_w
    epsilon = step_w * 1.0e-6
    while current <= stop_w + epsilon:
        values.append(round(current, 10))
        current += step_w
    return values


def _run_single_power(args: argparse.Namespace, power_w: float, output_root: Path) -> dict:
    fluence_j_cm2, pulse_energy_j, spot_area_cm2 = _fluence_j_cm2(
        average_power_w=power_w,
        repetition_rate_hz=args.repetition_rate_hz,
        spot_shape=args.spot_shape,
        square_side_um=args.square_side_um,
        spot_diameter_um=args.spot_diameter_um,
        fluence_override_j_cm2=args.fluence_j_cm2,
    )
    texture_area_factor = _texture_interface_area_factor(
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
        t_end=args.t_end_ns * 1.0e-9,
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
    diffusion_params = DiffusionParameters(
        boundary_model=args.boundary_model,
        source_exchange_mode=args.source_exchange_mode,
        solid_diffusivity_m2_s=args.solid_diffusivity_m2_s,
        solid_prefactor_cm2_s=args.solid_prefactor_cm2_s,
        solid_activation_energy_ev=args.solid_activation_energy_ev,
        liquid_prefactor_cm2_s=args.liquid_prefactor_cm2_s,
        liquid_activation_energy_ev=args.liquid_activation_energy_ev,
        interface_liquid_threshold=args.interface_liquid_threshold,
        source_effective_thickness_m=args.source_effective_thickness_nm * 1.0e-9,
        interfacial_transport_length_m=args.interfacial_transport_length_nm * 1.0e-9,
        initial_profile_kind=args.initial_profile_kind,
        initial_profile_csv=args.initial_profile_csv,
        initial_surface_concentration_cm3=args.initial_surface_p_concentration_cm3,
        initial_junction_depth_m=args.initial_junction_depth_nm * 1.0e-9,
        initial_inactive_surface_p_concentration_cm3=args.initial_inactive_surface_p_concentration_cm3,
        initial_inactive_surface_thickness_m=args.initial_inactive_surface_thickness_nm * 1.0e-9,
        texture_interface_area_factor=texture_area_factor,
    )

    case_dir = output_root / f"p{int(round(power_w))}w"
    stack_result = run_stack_simulation(
        domain=domain,
        silicon_material=silicon_material,
        psg_material=psg_material,
        pulse=pulse,
        optics=optics,
        surface_source=source_layer,
        substrate_doping=substrate_doping,
    )
    thermal_output = save_stack_outputs(stack_result, case_dir / "thermal")
    silicon_view = silicon_subdomain_view(stack_result)
    diffusion_result = run_diffusion(silicon_view, params=diffusion_params)
    diffusion_output = save_diffusion_outputs(diffusion_result, case_dir / "diffusion")

    with (thermal_output / "summary.json").open("r", encoding="utf-8") as handle:
        thermal_summary = json.load(handle)
    with (diffusion_output / "summary.json").open("r", encoding="utf-8") as handle:
        diffusion_summary = json.load(handle)

    combined_summary = {
        "phase3_output_dir": str(case_dir),
        "thermal_output_dir": str(thermal_output),
        "diffusion_output_dir": str(diffusion_output),
        "laser_input": {
            "average_power_w": power_w,
            "repetition_rate_hz": args.repetition_rate_hz,
            "pulse_energy_j": pulse_energy_j,
            "spot_shape": args.spot_shape,
            "square_side_um": args.square_side_um,
            "spot_diameter_um": args.spot_diameter_um,
            "spot_area_cm2": spot_area_cm2,
            "fluence_j_cm2": fluence_j_cm2,
            "fluence_mode": "override" if args.fluence_j_cm2 is not None else "derived_from_power_and_spot",
        },
        "texture": {
            "reflectance_multiplier": args.texture_reflectance_multiplier,
            "flat_surface_reflectance": args.surface_reflectance,
            "effective_surface_reflectance": effective_surface_reflectance(optics),
            "interface_area_factor": texture_area_factor,
            "pyramid_sidewall_angle_deg": args.texture_pyramid_sidewall_angle_deg,
        },
        "thermal": thermal_summary,
        "diffusion": diffusion_summary,
    }
    with (case_dir / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(combined_summary, handle, indent=2)

    metrics = {
        "power_w": power_w,
        "pulse_energy_uj": pulse_energy_j * 1.0e6,
        "fluence_j_cm2": fluence_j_cm2,
        "effective_surface_reflectance": effective_surface_reflectance(optics),
        "texture_interface_area_factor": texture_area_factor,
        "peak_si_surface_temperature_k": thermal_summary["metrics"]["peak_silicon_surface_temperature_k"],
        "max_liquid_fraction": thermal_summary["metrics"]["max_liquid_fraction"],
        "max_melt_depth_nm": thermal_summary["metrics"]["max_melt_depth_m"] * 1.0e9,
        "melt_start_ns": (
            thermal_summary["metrics"]["melt_start_s"] * 1.0e9
            if thermal_summary["metrics"]["melt_start_s"] is not None
            else None
        ),
        "melt_end_ns": (
            thermal_summary["metrics"]["melt_end_s"] * 1.0e9
            if thermal_summary["metrics"]["melt_end_s"] is not None
            else None
        ),
        "final_peak_p_cm3": diffusion_summary["metrics"]["final_peak_p_concentration_cm3"],
        "final_junction_depth_nm": diffusion_summary["metrics"]["final_junction_depth_m"] * 1.0e9,
        "initial_active_sheet_dose_cm2": diffusion_summary["metrics"].get("initial_active_sheet_dose_cm2"),
        "initial_inactive_sheet_dose_cm2": diffusion_summary["metrics"].get("initial_inactive_sheet_dose_cm2"),
        "final_chemical_net_donor_sheet_dose_cm2": diffusion_summary["metrics"]["final_net_donor_sheet_dose_cm2"],
        "peak_surface_injection_flux_atoms_m2_s": diffusion_summary["metrics"]["peak_surface_injection_flux_atoms_m2_s"],
        "cumulative_injected_dose_cm2": diffusion_summary["metrics"]["cumulative_injected_dose_cm2"],
        "source_depletion_fraction": diffusion_summary["metrics"]["source_depletion_fraction"],
        "melt_gate_active_fraction": diffusion_summary["metrics"]["melt_gate_active_fraction"],
        "case_dir": str(case_dir),
    }
    return metrics


def _save_scan_table(rows: list[dict], output_root: Path) -> Path:
    csv_path = output_root / "power_scan_summary.csv"
    if not rows:
        return csv_path
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    with (output_root / "power_scan_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(rows, handle, indent=2)
    return csv_path


def _plot_metric(
    powers: np.ndarray,
    values: np.ndarray,
    ylabel: str,
    title: str,
    path: Path,
    color: str,
    log_y: bool = False,
) -> None:
    figure, axis = plt.subplots(figsize=(7.5, 4.5))
    axis.plot(powers, values, marker="o", lw=2.0, color=color)
    axis.set_xlabel("Average Power (W)")
    axis.set_ylabel(ylabel)
    axis.set_title(title)
    axis.grid(alpha=0.25)
    if log_y:
        axis.set_yscale("log")
    figure.tight_layout()
    figure.savefig(path, dpi=200)
    plt.close(figure)


def _save_scan_plots(rows: list[dict], output_root: Path) -> None:
    powers = np.array([row["power_w"] for row in rows], dtype=float)
    _plot_metric(
        powers,
        np.array([row["peak_si_surface_temperature_k"] for row in rows], dtype=float),
        "Peak Si Surface Temperature (K)",
        "Power Scan: Peak Si Surface Temperature",
        output_root / "power_vs_peak_temperature.png",
        "#b03a2e",
    )
    _plot_metric(
        powers,
        np.maximum(np.array([row["max_melt_depth_nm"] for row in rows], dtype=float), 1.0e-3),
        "Max Melt Depth (nm)",
        "Power Scan: Melt Depth",
        output_root / "power_vs_melt_depth.png",
        "#7d3c98",
        log_y=True,
    )
    _plot_metric(
        powers,
        np.array([row["final_peak_p_cm3"] for row in rows], dtype=float),
        "Final Peak P (cm^-3)",
        "Power Scan: Final Peak P Concentration",
        output_root / "power_vs_final_peak_p.png",
        "#117864",
        log_y=True,
    )
    _plot_metric(
        powers,
        np.array([row["final_junction_depth_nm"] for row in rows], dtype=float),
        "Final Junction Depth (nm)",
        "Power Scan: Final Junction Depth",
        output_root / "power_vs_junction_depth.png",
        "#2471a3",
    )
    _plot_metric(
        powers,
        np.maximum(np.array([row["final_chemical_net_donor_sheet_dose_cm2"] for row in rows], dtype=float), 1.0e10),
        "Final Chemical Net Donor Sheet Dose (cm^-2)",
        "Power Scan: Final Chemical Net Donor Sheet Dose",
        output_root / "power_vs_final_net_donor_sheet_dose.png",
        "#ca6f1e",
        log_y=True,
    )


def main() -> int:
    args = build_parser().parse_args()
    output_root = ROOT / args.output_dir
    output_root.mkdir(parents=True, exist_ok=True)

    powers = _power_values(args.power_start_w, args.power_stop_w, args.power_step_w)
    rows: list[dict] = []
    for power_w in powers:
        rows.append(_run_single_power(args, power_w, output_root))

    _save_scan_table(rows, output_root)
    _save_scan_plots(rows, output_root)

    summary = {
        "output_dir": str(output_root),
        "power_start_w": args.power_start_w,
        "power_stop_w": args.power_stop_w,
        "power_step_w": args.power_step_w,
        "powers_w": powers,
        "n_cases": len(rows),
        "defaults": {
            "initial_profile_kind": args.initial_profile_kind,
            "initial_surface_p_concentration_cm3": args.initial_surface_p_concentration_cm3,
            "initial_junction_depth_nm": args.initial_junction_depth_nm,
            "initial_inactive_surface_p_concentration_cm3": args.initial_inactive_surface_p_concentration_cm3,
            "initial_inactive_surface_thickness_nm": args.initial_inactive_surface_thickness_nm,
            "surface_reflectance": args.surface_reflectance,
            "boundary_model": args.boundary_model,
            "source_exchange_mode": args.source_exchange_mode,
            "nz": args.nz,
            "t_end_ns": args.t_end_ns,
        },
    }
    with (output_root / "scan_manifest.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)

    print(f"Saved power scan to: {output_root}")
    print(f"Scanned powers: {', '.join(f'{power:.0f} W' for power in powers)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
