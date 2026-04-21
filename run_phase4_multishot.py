from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from laser_doping_sim import SubstrateDoping, SurfaceSourceLayer
from laser_doping_sim.phase1_thermal import LaserPulse, MaterialProperties
from laser_doping_sim.phase2_diffusion import DiffusionParameters
from laser_doping_sim.phase3_stack_thermal import (
    PSGLayerProperties,
    StackDomain1D,
    StackOpticalProperties,
    effective_surface_reflectance,
    run_stack_simulation,
    save_outputs as save_stack_outputs,
    silicon_subdomain_view,
)
from laser_doping_sim.phase4_multishot import (
    MultiShotParameters,
    run_multishot_diffusion,
    run_multishot_diffusion_with_thermal_history,
    save_outputs as save_multishot_outputs,
)
from run_phase3 import _fluence_j_cm2, _texture_interface_area_factor


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run Phase 4 multi-shot V1: reuse the same single-pulse thermal history each shot while "
            "carrying forward the chemical P state and source inventory."
        )
    )
    parser.add_argument("--output-dir", default="outputs/phase4/multishot_v1_default")
    parser.add_argument("--average-power-w", type=float, default=60.0)
    parser.add_argument("--shots", type=int, default=5)
    parser.add_argument(
        "--thermal-history-mode",
        choices=["reuse_single_pulse", "accumulate"],
        default="reuse_single_pulse",
        help=(
            "reuse_single_pulse = reuse one single-pulse thermal history every shot; "
            "accumulate = carry the cycle-end temperature field into the next shot."
        ),
    )
    parser.add_argument(
        "--source-replenishment-mode",
        choices=["carry", "reset_each_shot"],
        default="carry",
        help="carry = same local PSG source depletes shot-to-shot; reset_each_shot = source inventory resets before each shot.",
    )
    parser.add_argument("--profile-shots", type=int, nargs="*", default=None)
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
    parser.add_argument("--dt-ns", type=float, default=0.05)
    parser.add_argument("--t-end-ns", type=float, default=400.0)
    parser.add_argument(
        "--cycle-end-ns",
        type=float,
        default=None,
        help=(
            "Only used for thermal-history-mode=accumulate. If omitted, the shot cycle runs to one full pulse period "
            "derived from repetition-rate-hz."
        ),
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
            "Phase 4 multi-shot V1 keeps the PSG source as a P-rich SiO2 reservoir and, by default, "
            "lets the same local source inventory deplete shot-to-shot."
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
    parser.add_argument("--initial-profile-kind", choices=["none", "erfc_emitter", "measured"], default="measured")
    parser.add_argument("--initial-profile-csv", default="inputs/measured_profiles/ctv_measured_initial_profile.csv")
    parser.add_argument("--initial-surface-p-concentration-cm3", type=float, default=3.5e20)
    parser.add_argument("--initial-junction-depth-nm", type=float, default=300.0)
    parser.add_argument("--initial-inactive-surface-p-concentration-cm3", type=float, default=5.0e20)
    parser.add_argument("--initial-inactive-surface-thickness-nm", type=float, default=30.0)
    parser.add_argument("--texture-interface-area-factor", type=float, default=None)
    parser.add_argument("--texture-pyramid-sidewall-angle-deg", type=float, default=None)
    parser.add_argument(
        "--fast-output",
        action="store_true",
        help=(
            "Write the core csv/json/npz outputs but skip plots and use uncompressed npz saves "
            "to reduce post-processing time."
        ),
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output_root = ROOT / args.output_dir
    output_root.mkdir(parents=True, exist_ok=True)

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
    multishot_params = MultiShotParameters(
        shot_count=args.shots,
        source_replenishment_mode=args.source_replenishment_mode,
        thermal_history_mode=args.thermal_history_mode,
    )
    thermal_output = None
    if args.thermal_history_mode == "reuse_single_pulse":
        stack_result = run_stack_simulation(
            domain=domain,
            silicon_material=silicon_material,
            psg_material=psg_material,
            pulse=pulse,
            optics=optics,
            surface_source=source_layer,
            substrate_doping=substrate_doping,
        )
        thermal_output = save_stack_outputs(stack_result, output_root / "thermal", fast_output=args.fast_output)
        silicon_view = silicon_subdomain_view(stack_result)
        multishot_result = run_multishot_diffusion(
            thermal=silicon_view,
            params=diffusion_params,
            multishot_params=multishot_params,
        )
    else:
        pulse_period_ns = 1.0e9 / args.repetition_rate_hz
        cycle_end_ns = args.cycle_end_ns if args.cycle_end_ns is not None else pulse_period_ns
        cycle_domain = StackDomain1D(
            silicon_thickness=args.si_thickness_um * 1.0e-6,
            nz=args.nz,
            dt=args.dt_ns * 1.0e-9,
            t_end=cycle_end_ns * 1.0e-9,
            ambient_temp=args.ambient_temp_k,
            bottom_bc=args.bottom_bc,
        )
        multishot_result = run_multishot_diffusion_with_thermal_history(
            stack_domain=cycle_domain,
            silicon_material=silicon_material,
            psg_material=psg_material,
            pulse=pulse,
            optics=optics,
            params=diffusion_params,
            multishot_params=multishot_params,
            surface_source=source_layer,
            substrate_doping=substrate_doping,
        )
        if multishot_result.last_stack_thermal is not None:
            thermal_output = save_stack_outputs(
                multishot_result.last_stack_thermal,
                output_root / "thermal_last_shot",
                fast_output=args.fast_output,
            )
    multishot_output = save_multishot_outputs(
        multishot_result,
        output_root / "multishot",
        profile_shots=args.profile_shots,
        fast_output=args.fast_output,
    )

    thermal_summary = (
        json.loads((thermal_output / "summary.json").read_text(encoding="utf-8"))
        if thermal_output is not None
        else {
            "mode": args.thermal_history_mode,
            "notes": "See the Phase 4 multishot summary for shot-by-shot thermal metrics.",
        }
    )
    multishot_summary = json.loads((multishot_output / "summary.json").read_text(encoding="utf-8"))
    combined_summary = {
        "output_dir": str(output_root),
        "laser_input": {
            "average_power_w": args.average_power_w,
            "repetition_rate_hz": args.repetition_rate_hz,
            "pulse_energy_j": pulse_energy_j,
            "spot_shape": args.spot_shape,
            "square_side_um": args.square_side_um,
            "spot_diameter_um": args.spot_diameter_um,
            "spot_area_cm2": spot_area_cm2,
            "fluence_j_cm2": fluence_j_cm2,
            "fast_output": args.fast_output,
        },
        "texture": {
            "reflectance_multiplier": args.texture_reflectance_multiplier,
            "flat_surface_reflectance": args.surface_reflectance,
            "effective_surface_reflectance": effective_surface_reflectance(optics),
            "interface_area_factor": texture_area_factor,
            "pyramid_sidewall_angle_deg": args.texture_pyramid_sidewall_angle_deg,
        },
        "thermal": thermal_summary,
        "multishot": multishot_summary,
    }
    if args.thermal_history_mode == "accumulate":
        combined_summary["laser_input"]["pulse_period_ns"] = 1.0e9 / args.repetition_rate_hz
        combined_summary["laser_input"]["cycle_end_ns"] = (
            args.cycle_end_ns if args.cycle_end_ns is not None else 1.0e9 / args.repetition_rate_hz
        )
    with (output_root / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(combined_summary, handle, indent=2)

    print(f"Saved Phase 4 multi-shot output to: {output_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
