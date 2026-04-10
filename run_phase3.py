from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the Phase 3 P-rich SiO2 (PSG)/Si stacked thermal model and re-drive phosphorus diffusion."
    )
    parser.add_argument("--output-dir", default="outputs/phase3/default_run")
    parser.add_argument("--average-power-w", type=float, default=30.0)
    parser.add_argument("--repetition-rate-hz", type=float, default=500000.0)
    parser.add_argument("--spot-shape", choices=["square_flat_top", "circular_flat_top"], default="square_flat_top")
    parser.add_argument("--square-side-um", type=float, default=95.0)
    parser.add_argument("--spot-diameter-um", type=float, default=117.85536026233771)
    parser.add_argument("--fluence-j-cm2", type=float, default=None)
    parser.add_argument("--pulse-fwhm-ns", type=float, default=10.0)
    parser.add_argument("--peak-time-ns", type=float, default=30.0)
    parser.add_argument("--surface-reflectance", type=float, default=0.09)
    parser.add_argument(
        "--texture-reflectance-multiplier",
        type=float,
        default=1.0,
        help="Multiplier applied to the flat-surface reflectance to approximate multi-bounce texture light trapping.",
    )
    parser.add_argument("--interface-transmission", type=float, default=0.68)
    parser.add_argument("--psg-absorption-depth-um", type=float, default=50.0)
    parser.add_argument("--si-absorption-depth-nm", type=float, default=1274.0)
    parser.add_argument("--psg-thickness-nm", type=float, default=150.0)
    parser.add_argument("--psg-rho", type=float, default=2200.0)
    parser.add_argument("--psg-cp", type=float, default=730.0)
    parser.add_argument("--psg-k", type=float, default=1.4)
    parser.add_argument("--si-thickness-um", type=float, default=8.0)
    parser.add_argument("--nz", type=int, default=600)
    parser.add_argument("--dt-ns", type=float, default=0.2)
    parser.add_argument("--t-end-ns", type=float, default=150.0)
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
    parser.add_argument(
        "--boundary-model",
        choices=["finite_source_cell", "robin_reservoir"],
        default="finite_source_cell",
    )
    parser.add_argument(
        "--source-exchange-mode",
        choices=["melt_only", "all_states"],
        default="all_states",
    )
    parser.add_argument("--solid-diffusivity-m2-s", type=float, default=0.0)
    parser.add_argument("--solid-prefactor-cm2-s", type=float, default=8.0e-4)
    parser.add_argument("--solid-activation-energy-ev", type=float, default=2.74)
    parser.add_argument("--liquid-prefactor-cm2-s", type=float, default=1.4e-3)
    parser.add_argument("--liquid-activation-energy-ev", type=float, default=0.183)
    parser.add_argument("--interface-liquid-threshold", type=float, default=0.01)
    parser.add_argument("--source-effective-thickness-nm", type=float, default=100.0)
    parser.add_argument("--interfacial-transport-length-nm", type=float, default=100.0)
    parser.add_argument("--initial-profile-kind", choices=["none", "erfc_emitter", "measured"], default="none")
    parser.add_argument("--initial-profile-csv", default="")
    parser.add_argument("--initial-surface-p-concentration-cm3", type=float, default=0.0)
    parser.add_argument("--initial-junction-depth-nm", type=float, default=0.0)
    parser.add_argument("--initial-inactive-surface-p-concentration-cm3", type=float, default=0.0)
    parser.add_argument("--initial-inactive-surface-thickness-nm", type=float, default=0.0)
    parser.add_argument(
        "--texture-interface-area-factor",
        type=float,
        default=None,
        help="Actual/projected interface area factor used for conformal PSG coverage on textured silicon.",
    )
    parser.add_argument(
        "--texture-pyramid-sidewall-angle-deg",
        type=float,
        default=None,
        help="If provided and --texture-interface-area-factor is omitted, derive the area factor as sec(angle).",
    )
    parser.add_argument(
        "--texture-notes",
        default=(
            "Texture enhancement is currently collapsed into an effective reflectance multiplier for optics and an "
            "actual/projected interface-area factor for PSG-to-Si mass transfer."
        ),
    )
    return parser


def _fluence_j_cm2(
    average_power_w: float,
    repetition_rate_hz: float,
    spot_shape: str,
    square_side_um: float,
    spot_diameter_um: float,
    fluence_override_j_cm2: float | None,
) -> tuple[float, float, float]:
    if repetition_rate_hz <= 0.0:
        raise ValueError("repetition_rate_hz must be positive.")
    pulse_energy_j = average_power_w / repetition_rate_hz
    if fluence_override_j_cm2 is not None:
        if spot_shape == "square_flat_top":
            if square_side_um <= 0.0:
                raise ValueError("square_side_um must be positive.")
            spot_area_cm2 = (square_side_um * 1.0e-4) ** 2
        else:
            if spot_diameter_um <= 0.0:
                raise ValueError("spot_diameter_um must be positive.")
            radius_cm = 0.5 * spot_diameter_um * 1.0e-4
            spot_area_cm2 = np.pi * radius_cm**2
        return fluence_override_j_cm2, pulse_energy_j, spot_area_cm2

    if spot_shape == "square_flat_top":
        if square_side_um <= 0.0:
            raise ValueError("square_side_um must be positive when fluence is not overridden.")
        spot_area_cm2 = (square_side_um * 1.0e-4) ** 2
    else:
        if spot_diameter_um <= 0.0:
            raise ValueError("spot_diameter_um must be positive when fluence is not overridden.")
        radius_cm = 0.5 * spot_diameter_um * 1.0e-4
        spot_area_cm2 = np.pi * radius_cm**2
    return pulse_energy_j / spot_area_cm2, pulse_energy_j, spot_area_cm2


def _texture_interface_area_factor(
    texture_interface_area_factor: float | None,
    texture_pyramid_sidewall_angle_deg: float | None,
) -> float:
    if texture_interface_area_factor is not None:
        if texture_interface_area_factor <= 0.0:
            raise ValueError("texture_interface_area_factor must be positive.")
        return texture_interface_area_factor

    if texture_pyramid_sidewall_angle_deg is None:
        return 1.0

    if not 0.0 <= texture_pyramid_sidewall_angle_deg < 89.9:
        raise ValueError("texture_pyramid_sidewall_angle_deg must lie in [0, 89.9).")

    angle_rad = np.deg2rad(texture_pyramid_sidewall_angle_deg)
    return float(1.0 / np.cos(angle_rad))


def main() -> int:
    args = build_parser().parse_args()
    fluence_j_cm2, pulse_energy_j, spot_area_cm2 = _fluence_j_cm2(
        average_power_w=args.average_power_w,
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

    stack_result = run_stack_simulation(
        domain=domain,
        silicon_material=silicon_material,
        psg_material=psg_material,
        pulse=pulse,
        optics=optics,
        surface_source=source_layer,
        substrate_doping=substrate_doping,
    )

    output_root = ROOT / args.output_dir
    thermal_output = save_stack_outputs(stack_result, output_root / "thermal")

    silicon_view = silicon_subdomain_view(stack_result)
    diffusion_result = run_diffusion(silicon_view, params=diffusion_params)
    diffusion_output = save_diffusion_outputs(diffusion_result, output_root / "diffusion")

    with (thermal_output / "summary.json").open("r", encoding="utf-8") as handle:
        thermal_summary = json.load(handle)
    with (diffusion_output / "summary.json").open("r", encoding="utf-8") as handle:
        diffusion_summary = json.load(handle)

    combined_summary = {
        "phase3_output_dir": str(output_root),
        "thermal_output_dir": str(thermal_output),
        "diffusion_output_dir": str(diffusion_output),
        "laser_input": {
            "average_power_w": args.average_power_w,
            "repetition_rate_hz": args.repetition_rate_hz,
            "pulse_energy_j": pulse_energy_j,
            "spot_shape": args.spot_shape,
            "square_side_um": args.square_side_um,
            "spot_diameter_um": args.spot_diameter_um,
            "spot_area_cm2": spot_area_cm2,
            "fluence_j_cm2": fluence_j_cm2,
            "fluence_mode": "override" if args.fluence_j_cm2 is not None else "derived_from_power_and_spot",
            "one_dimensional_interpretation": (
                "In the current 1D depth-only model, the lateral flat-top square spot only enters through its area "
                "when converting average power to single-pulse fluence."
            ),
        },
        "texture": {
            "reflectance_multiplier": args.texture_reflectance_multiplier,
            "flat_surface_reflectance": args.surface_reflectance,
            "effective_surface_reflectance": effective_surface_reflectance(optics),
            "interface_area_factor": texture_area_factor,
            "pyramid_sidewall_angle_deg": args.texture_pyramid_sidewall_angle_deg,
            "notes": args.texture_notes,
        },
        "thermal": thermal_summary,
        "diffusion": diffusion_summary,
    }
    with (output_root / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(combined_summary, handle, indent=2)

    thermal_metrics = thermal_summary["metrics"]
    diffusion_metrics = diffusion_summary["metrics"]

    print(f"Saved outputs to: {output_root}")
    print(f"Pulse energy: {pulse_energy_j * 1.0e6:.2f} uJ")
    print(f"Fluence: {fluence_j_cm2:.3f} J/cm^2")
    print(f"Peak silicon surface temperature: {thermal_metrics['peak_silicon_surface_temperature_k']:.1f} K")
    print(f"Max silicon melt depth: {thermal_metrics['max_melt_depth_m'] * 1.0e9:.1f} nm")
    print(f"Final peak P concentration: {diffusion_metrics['final_peak_p_concentration_cm3']:.3e} cm^-3")
    print(f"Final doping depth: {diffusion_metrics['final_junction_depth_m'] * 1.0e9:.1f} nm")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
