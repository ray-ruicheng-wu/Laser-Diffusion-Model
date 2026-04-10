from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from laser_doping_sim.phase1_thermal import (
    Domain1D,
    LaserPulse,
    MaterialProperties,
    SubstrateDoping,
    SurfaceSourceLayer,
    run_simulation,
    save_outputs,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the Phase 1 1D thermal simulation for laser melting in silicon."
    )
    parser.add_argument("--output-dir", default="outputs/phase1/default_run")
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
        default="Phase 2 source layer placeholder; not coupled into the Phase 1 thermal solve.",
    )
    parser.add_argument("--substrate-dopant", default="Ga")
    parser.add_argument("--substrate-dopant-concentration-cm3", type=float, default=1.0e16)
    parser.add_argument(
        "--substrate-notes",
        default="Background substrate doping placeholder; not coupled into the Phase 1 thermal solve.",
    )
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

    result = run_simulation(
        domain=domain,
        material=material,
        pulse=pulse,
        surface_source=source_layer,
        substrate_doping=substrate_doping,
    )
    output_path = save_outputs(result, ROOT / args.output_dir)

    with (output_path / "summary.json").open("r", encoding="utf-8") as handle:
        summary = json.load(handle)["metrics"]

    print(f"Saved outputs to: {output_path}")
    print(f"Peak surface temperature: {summary['peak_surface_temperature_k']:.1f} K")
    print(f"Max melt depth: {summary['max_melt_depth_m'] * 1.0e9:.1f} nm")
    if summary["melt_start_s"] is None:
        print("No melting detected. Increase fluence or tighten the pulse.")
    else:
        start_ns = summary["melt_start_s"] * 1.0e9
        end_ns = summary["melt_end_s"] * 1.0e9
        print(f"Melt window: {start_ns:.2f} ns to {end_ns:.2f} ns")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
