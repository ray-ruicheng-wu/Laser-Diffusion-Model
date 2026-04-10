from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from laser_doping_sim import (
    Domain1D,
    LaserPulse,
    MaterialProperties,
    SubstrateDoping,
    SurfaceSourceLayer,
)
from laser_doping_sim.phase1_thermal import run_simulation as run_thermal_simulation
from laser_doping_sim.phase2_diffusion import (
    DiffusionParameters,
    run_diffusion,
    save_outputs,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the Phase 2 P diffusion simulation driven by the Phase 1 thermal history."
    )
    parser.add_argument("--output-dir", default="outputs/phase2/default_run")
    parser.add_argument("--fluence-j-cm2", type=float, default=0.55)
    parser.add_argument("--pulse-fwhm-ns", type=float, default=10.0)
    parser.add_argument("--peak-time-ns", type=float, default=30.0)
    parser.add_argument("--absorption-depth-nm", type=float, default=80.0)
    parser.add_argument("--absorptivity", type=float, default=0.72)
    parser.add_argument("--thickness-um", type=float, default=8.0)
    parser.add_argument("--nz", type=int, default=500)
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
        default="Phase 2 finite PSG source used for liquid-phase phosphorus diffusion.",
    )
    parser.add_argument("--substrate-dopant", default="Ga")
    parser.add_argument("--substrate-dopant-concentration-cm3", type=float, default=1.0e16)
    parser.add_argument(
        "--substrate-notes",
        default="Background acceptor concentration used to define junction depth.",
    )
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
    parser.add_argument("--initial-profile-kind", choices=["none", "erfc_emitter"], default="none")
    parser.add_argument("--initial-surface-p-concentration-cm3", type=float, default=0.0)
    parser.add_argument("--initial-junction-depth-nm", type=float, default=0.0)
    parser.add_argument("--initial-inactive-surface-p-concentration-cm3", type=float, default=0.0)
    parser.add_argument("--initial-inactive-surface-thickness-nm", type=float, default=0.0)
    return parser


def main() -> int:
    args = build_parser().parse_args()

    material = MaterialProperties(
        melt_temp=args.melt_temp_k,
        mushy_width=args.mushy_width_k,
    )
    pulse = LaserPulse(
        fluence=args.fluence_j_cm2 * 1.0e4,
        pulse_fwhm=args.pulse_fwhm_ns * 1.0e-9,
        peak_time=args.peak_time_ns * 1.0e-9,
        absorptivity=args.absorptivity,
        absorption_depth=args.absorption_depth_nm * 1.0e-9,
    )
    domain = Domain1D(
        thickness=args.thickness_um * 1.0e-6,
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
        initial_surface_concentration_cm3=args.initial_surface_p_concentration_cm3,
        initial_junction_depth_m=args.initial_junction_depth_nm * 1.0e-9,
        initial_inactive_surface_p_concentration_cm3=args.initial_inactive_surface_p_concentration_cm3,
        initial_inactive_surface_thickness_m=args.initial_inactive_surface_thickness_nm * 1.0e-9,
    )

    thermal = run_thermal_simulation(
        domain=domain,
        material=material,
        pulse=pulse,
        surface_source=source_layer,
        substrate_doping=substrate_doping,
    )
    diffusion = run_diffusion(thermal, params=diffusion_params)
    output_path = save_outputs(diffusion, ROOT / args.output_dir)

    with (output_path / "summary.json").open("r", encoding="utf-8") as handle:
        summary = json.load(handle)["metrics"]

    print(f"Saved outputs to: {output_path}")
    print(f"Final peak P concentration: {summary['final_peak_p_concentration_cm3']:.3e} cm^-3")
    print(f"Final doping depth: {summary['final_junction_depth_m'] * 1.0e9:.1f} nm")
    print(f"Max doping depth: {summary['max_junction_depth_m'] * 1.0e9:.1f} nm")
    print(f"Final mass-balance error: {summary['final_mass_balance_error_atoms_m2']:.3e} atoms/m^2")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
