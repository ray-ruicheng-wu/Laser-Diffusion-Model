from __future__ import annotations

import argparse
from dataclasses import replace
import csv
import json
from pathlib import Path
import sys
import tempfile

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from laser_doping_sim.phase1_thermal import (  # noqa: E402
    Domain1D,
    LaserPulse,
    MaterialProperties,
    SubstrateDoping,
    SurfaceSourceLayer,
)
from laser_doping_sim.phase2_diffusion import DiffusionParameters, run_diffusion  # noqa: E402
from laser_doping_sim.phase3_stack_thermal import (  # noqa: E402
    PSGLayerProperties,
    StackDomain1D,
    StackOpticalProperties,
    StackSimulationResult,
    silicon_subdomain_view,
)
from laser_doping_sim.activation_models import (  # noqa: E402
    PiecewiseLinearDualChannelActivationModel,
    PiecewiseLinearNonactiveActivationModel,
    load_piecewise_dual_channel_activation_model_csv,
    load_piecewise_nonactive_activation_model_csv,
)
from laser_doping_sim.measured_profiles import (  # noqa: E402
    MeasuredInitialProfile,
    load_measured_initial_profile_csv,
    save_measured_initial_profile_csv,
)
from laser_doping_sim.sheet_resistance import (  # noqa: E402
    MasettiElectronMobilityModel,
    conductivity_profile_s_per_cm,
    sheet_resistance_ohm_per_sq,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Post-process selected Phase 3 cases into sheet-resistance estimates.",
    )
    parser.add_argument(
        "--case-dirs",
        nargs="+",
        required=True,
        help="Case directories containing summary.json, thermal/, and diffusion/ outputs.",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/phase3/sheet_resistance_inactive5pct",
    )
    parser.add_argument(
        "--inactive-activation-fraction",
        type=float,
        default=0.0,
        help=(
            "Electrical activation fraction for the initial inactive-P contribution before "
            "laser processing. Also used as the baseline initial inactive activation when "
            "a piecewise non-active-pool activation model is enabled."
        ),
    )
    parser.add_argument(
        "--final-inactive-activation-fraction",
        type=float,
        default=0.0,
        help="Electrical activation fraction applied to the redistributed initial inactive-P contribution after laser processing.",
    )
    parser.add_argument(
        "--injected-activation-fraction",
        type=float,
        default=1.0,
        help="Electrical activation fraction assumed for source-injected phosphorus after laser processing.",
    )
    parser.add_argument(
        "--measurement-temperature-k",
        type=float,
        default=300.0,
        help="Measurement temperature for the Masetti mobility model.",
    )
    parser.add_argument(
        "--activation-model",
        choices=("fixed_fractions", "piecewise_nonactive_pool", "piecewise_dual_channel"),
        default="fixed_fractions",
        help=(
            "Activation post-processing model. "
            "'fixed_fractions' uses independent inactive/injected activation fractions. "
            "'piecewise_nonactive_pool' uses one empirical power-dependent activation "
            "fraction for the final non-active pool (redistributed inactive + injected P). "
            "'piecewise_dual_channel' uses separate empirical power-dependent activation "
            "fractions for redistributed initial inactive P and source-injected P."
        ),
    )
    parser.add_argument(
        "--activation-table-csv",
        default=None,
        help=(
            "CSV table for the piecewise_nonactive_pool or piecewise_dual_channel activation "
            "models. For piecewise_nonactive_pool, required columns are "
            "power_w,effective_final_nonactive_activation_fraction. For "
            "piecewise_dual_channel, required columns are "
            "power_w,effective_final_inactive_activation_fraction,"
            "effective_final_injected_activation_fraction."
        ),
    )
    return parser


def _stack_result_from_case(case_dir: Path) -> StackSimulationResult:
    with (case_dir / "summary.json").open("r", encoding="utf-8") as handle:
        summary = json.load(handle)
    arrays = np.load(case_dir / "thermal" / "phase3_stack_results.npz")
    thermal = summary["thermal"]
    return StackSimulationResult(
        time=arrays["time_s"],
        depth=arrays["depth_m"],
        temperature=arrays["temperature_k"],
        liquid_fraction=arrays["liquid_fraction"],
        melt_depth=arrays["melt_depth_m"],
        laser_flux=arrays["laser_flux_w_per_m2"],
        surface_source=SurfaceSourceLayer(**thermal["surface_source"]),
        substrate_doping=SubstrateDoping(**thermal["substrate_doping"]),
        silicon_material=MaterialProperties(**thermal["silicon_material"]),
        psg_material=PSGLayerProperties(**thermal["psg_material"]),
        optics=StackOpticalProperties(**thermal["optics"]),
        pulse=LaserPulse(**thermal["pulse"]),
        domain=StackDomain1D(**thermal["domain"]),
    )


def _diffusion_params_from_case(case_dir: Path) -> DiffusionParameters:
    with (case_dir / "summary.json").open("r", encoding="utf-8") as handle:
        summary = json.load(handle)
    return DiffusionParameters(**summary["diffusion"]["diffusion_parameters"])


def _power_from_case(case_dir: Path) -> float | None:
    with (case_dir / "summary.json").open("r", encoding="utf-8") as handle:
        summary = json.load(handle)
    return summary.get("laser_input", {}).get("average_power_w")


def _rerun_component_profiles(
    case_dir: Path,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float]:
    stack_result = _stack_result_from_case(case_dir)
    params = _diffusion_params_from_case(case_dir)
    stored = np.load(case_dir / "diffusion" / "phase2_results.npz")
    final_total_cm3 = stored["concentration_p_cm3"][-1]
    initial_active_cm3 = stored["initial_active_p_cm3"]
    initial_inactive_cm3 = stored["initial_inactive_p_cm3"]

    no_source_stack = replace(
        stack_result,
        surface_source=replace(stack_result.surface_source, dopant_concentration_cm3=0.0),
    )
    silicon_thermal = silicon_subdomain_view(no_source_stack)

    if params.initial_profile_kind == "measured":
        measured_profile = load_measured_initial_profile_csv(params.initial_profile_csv)
        active_profile = MeasuredInitialProfile(
            depth_nm=measured_profile.depth_nm,
            total_p_cm3=measured_profile.active_p_cm3,
            active_p_cm3=measured_profile.active_p_cm3,
            inactive_p_cm3=np.zeros_like(measured_profile.inactive_p_cm3),
        )
        inactive_profile = MeasuredInitialProfile(
            depth_nm=measured_profile.depth_nm,
            total_p_cm3=measured_profile.inactive_p_cm3,
            active_p_cm3=np.zeros_like(measured_profile.active_p_cm3),
            inactive_p_cm3=measured_profile.inactive_p_cm3,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            active_csv = save_measured_initial_profile_csv(active_profile, tmpdir_path / "active_only.csv")
            inactive_csv = save_measured_initial_profile_csv(inactive_profile, tmpdir_path / "inactive_only.csv")
            active_only = run_diffusion(
                silicon_thermal,
                params=replace(
                    params,
                    initial_profile_csv=str(active_csv),
                ),
            )
            inactive_only = run_diffusion(
                silicon_thermal,
                params=replace(
                    params,
                    initial_profile_csv=str(inactive_csv),
                ),
            )
    else:
        active_only = run_diffusion(
            silicon_thermal,
            params=replace(
                params,
                initial_inactive_surface_p_concentration_cm3=0.0,
                initial_inactive_surface_thickness_m=0.0,
            ),
        )
        inactive_only = run_diffusion(
            silicon_thermal,
            params=replace(
                params,
                initial_profile_kind="none",
                initial_surface_concentration_cm3=0.0,
                initial_junction_depth_m=0.0,
            ),
        )
    final_active_component_cm3 = active_only.concentration_p_cm3[-1]
    final_inactive_component_cm3 = inactive_only.concentration_p_cm3[-1]
    final_injected_component_cm3 = np.maximum(
        final_total_cm3 - final_active_component_cm3 - final_inactive_component_cm3,
        0.0,
    )
    background_ga_cm3 = float(stack_result.substrate_doping.concentration_cm3)
    return (
        silicon_thermal.depth,
        initial_active_cm3,
        initial_inactive_cm3,
        final_active_component_cm3 + 0.0,
        background_ga_cm3,
        final_inactive_component_cm3,
        final_injected_component_cm3,
    )


def _case_sheet_resistance_summary(
    case_dir: Path,
    inactive_activation_fraction: float,
    final_inactive_activation_fraction: float,
    injected_activation_fraction: float,
    activation_model_name: str,
    piecewise_nonactive_pool_model: PiecewiseLinearNonactiveActivationModel | None,
    piecewise_dual_channel_model: PiecewiseLinearDualChannelActivationModel | None,
    mobility_model: MasettiElectronMobilityModel,
) -> dict:
    (
        depth_m,
        initial_active_cm3,
        initial_inactive_cm3,
        final_active_component_cm3,
        background_ga_cm3,
        final_inactive_component_cm3,
        final_injected_component_cm3,
    ) = _rerun_component_profiles(case_dir)
    power_w = _power_from_case(case_dir)

    applied_initial_inactive_activation_fraction = inactive_activation_fraction
    applied_final_inactive_activation_fraction = final_inactive_activation_fraction
    applied_injected_activation_fraction = injected_activation_fraction
    applied_final_nonactive_pool_activation_fraction = np.nan

    if activation_model_name == "piecewise_nonactive_pool":
        if piecewise_nonactive_pool_model is None:
            raise ValueError("piecewise_nonactive_pool mode requires an activation model table.")
        if power_w is None:
            raise ValueError(
                f"Case directory {case_dir} does not expose average laser power, which is required "
                "for the piecewise non-active-pool activation model."
            )
        applied_initial_inactive_activation_fraction = (
            piecewise_nonactive_pool_model.initial_inactive_activation_fraction
        )
        applied_final_nonactive_pool_activation_fraction = (
            piecewise_nonactive_pool_model.fraction_at_power(power_w)
        )
        initial_active_donor_cm3 = (
            initial_active_cm3
            + applied_initial_inactive_activation_fraction * initial_inactive_cm3
        )
        final_active_donor_cm3 = (
            final_active_component_cm3
            + applied_final_nonactive_pool_activation_fraction
            * (final_inactive_component_cm3 + final_injected_component_cm3)
        )
        applied_final_inactive_activation_fraction = applied_final_nonactive_pool_activation_fraction
        applied_injected_activation_fraction = applied_final_nonactive_pool_activation_fraction
    elif activation_model_name == "piecewise_dual_channel":
        if piecewise_dual_channel_model is None:
            raise ValueError("piecewise_dual_channel mode requires an activation model table.")
        if power_w is None:
            raise ValueError(
                f"Case directory {case_dir} does not expose average laser power, which is required "
                "for the piecewise dual-channel activation model."
            )
        applied_initial_inactive_activation_fraction = (
            piecewise_dual_channel_model.initial_inactive_activation_fraction
        )
        applied_final_inactive_activation_fraction = piecewise_dual_channel_model.inactive_fraction_at_power(power_w)
        applied_injected_activation_fraction = piecewise_dual_channel_model.injected_fraction_at_power(power_w)
        initial_active_donor_cm3 = (
            initial_active_cm3
            + applied_initial_inactive_activation_fraction * initial_inactive_cm3
        )
        final_active_donor_cm3 = (
            final_active_component_cm3
            + applied_final_inactive_activation_fraction * final_inactive_component_cm3
            + applied_injected_activation_fraction * final_injected_component_cm3
        )
    else:
        initial_active_donor_cm3 = (
            initial_active_cm3
            + applied_initial_inactive_activation_fraction * initial_inactive_cm3
        )
        final_active_donor_cm3 = (
            final_active_component_cm3
            + applied_final_inactive_activation_fraction * final_inactive_component_cm3
            + applied_injected_activation_fraction * final_injected_component_cm3
        )

    rsh_init = sheet_resistance_ohm_per_sq(
        depth_m,
        initial_active_donor_cm3,
        background_ga_cm3,
        mobility_model=mobility_model,
    )
    rsh_after = sheet_resistance_ohm_per_sq(
        depth_m,
        final_active_donor_cm3,
        background_ga_cm3,
        mobility_model=mobility_model,
    )

    initial_conductivity = conductivity_profile_s_per_cm(
        initial_active_donor_cm3,
        background_ga_cm3,
        mobility_model=mobility_model,
    )
    final_conductivity = conductivity_profile_s_per_cm(
        final_active_donor_cm3,
        background_ga_cm3,
        mobility_model=mobility_model,
    )

    return {
        "case_dir": str(case_dir),
        "power_w": power_w,
        "activation_model": activation_model_name,
        "inactive_activation_fraction": applied_initial_inactive_activation_fraction,
        "final_inactive_activation_fraction": applied_final_inactive_activation_fraction,
        "injected_activation_fraction": applied_injected_activation_fraction,
        "final_nonactive_pool_activation_fraction": applied_final_nonactive_pool_activation_fraction,
        "measurement_temperature_k": mobility_model.temperature_k,
        "background_ga_concentration_cm3": background_ga_cm3,
        "rsh_init_ohm_per_sq": rsh_init,
        "rsh_af_ohm_per_sq": rsh_after,
        "rsh_change_percent": 100.0 * (rsh_after - rsh_init) / rsh_init if np.isfinite(rsh_init) and rsh_init > 0.0 else np.nan,
        "initial_active_sheet_dose_cm2": float(np.trapezoid(initial_active_cm3, depth_m * 1.0e2)),
        "initial_inactive_sheet_dose_cm2": float(np.trapezoid(initial_inactive_cm3, depth_m * 1.0e2)),
        "final_active_component_sheet_dose_cm2": float(np.trapezoid(final_active_component_cm3, depth_m * 1.0e2)),
        "final_inactive_component_sheet_dose_cm2": float(np.trapezoid(final_inactive_component_cm3, depth_m * 1.0e2)),
        "final_injected_component_sheet_dose_cm2": float(np.trapezoid(final_injected_component_cm3, depth_m * 1.0e2)),
        "peak_initial_conductivity_s_per_cm": float(np.max(initial_conductivity)),
        "peak_final_conductivity_s_per_cm": float(np.max(final_conductivity)),
    }


def _save_outputs(rows: list[dict], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = output_dir / "sheet_resistance_summary.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    json_path = output_dir / "sheet_resistance_summary.json"
    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(rows, handle, indent=2)

    labels = [f"{int(round(row['power_w']))} W" if row["power_w"] is not None else Path(row["case_dir"]).name for row in rows]
    init_values = np.array([row["rsh_init_ohm_per_sq"] for row in rows], dtype=float)
    final_values = np.array([row["rsh_af_ohm_per_sq"] for row in rows], dtype=float)
    x = np.arange(len(rows), dtype=float)
    width = 0.36

    figure, axis = plt.subplots(figsize=(8.0, 4.8))
    axis.bar(x - width / 2.0, init_values, width=width, color="#5d6d7e", label="Rsh init")
    axis.bar(x + width / 2.0, final_values, width=width, color="#ca6f1e", label="Rsh af")
    axis.set_xticks(x)
    axis.set_xticklabels(labels)
    axis.set_ylabel("Sheet Resistance (ohm/sq)")
    axis.set_title("Sheet Resistance from Initial/Final Activation Assumptions")
    axis.grid(axis="y", alpha=0.25)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_dir / "sheet_resistance_bar_chart.png", dpi=220)
    plt.close(figure)


def main() -> int:
    args = build_parser().parse_args()
    output_dir = ROOT / args.output_dir
    mobility_model = MasettiElectronMobilityModel(temperature_k=args.measurement_temperature_k)
    piecewise_nonactive_pool_model = None
    piecewise_dual_channel_model = None
    if args.activation_model == "piecewise_nonactive_pool":
        if not args.activation_table_csv:
            raise SystemExit(
                "--activation-table-csv is required when --activation-model=piecewise_nonactive_pool"
            )
        piecewise_nonactive_pool_model = load_piecewise_nonactive_activation_model_csv(
            ROOT / args.activation_table_csv,
            initial_inactive_activation_fraction=args.inactive_activation_fraction,
        )
    elif args.activation_model == "piecewise_dual_channel":
        if not args.activation_table_csv:
            raise SystemExit(
                "--activation-table-csv is required when --activation-model=piecewise_dual_channel"
            )
        piecewise_dual_channel_model = load_piecewise_dual_channel_activation_model_csv(
            ROOT / args.activation_table_csv,
            initial_inactive_activation_fraction=args.inactive_activation_fraction,
        )
    rows = [
        _case_sheet_resistance_summary(
            case_dir=ROOT / case_dir,
            inactive_activation_fraction=args.inactive_activation_fraction,
            final_inactive_activation_fraction=args.final_inactive_activation_fraction,
            injected_activation_fraction=args.injected_activation_fraction,
            activation_model_name=args.activation_model,
            piecewise_nonactive_pool_model=piecewise_nonactive_pool_model,
            piecewise_dual_channel_model=piecewise_dual_channel_model,
            mobility_model=mobility_model,
        )
        for case_dir in args.case_dirs
    ]
    rows.sort(key=lambda row: (row["power_w"] is None, row["power_w"]))
    _save_outputs(rows, output_dir)
    print(f"Saved sheet-resistance summary to: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
