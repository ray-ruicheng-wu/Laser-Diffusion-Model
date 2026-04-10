from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from laser_doping_sim.measured_profiles import (  # noqa: E402
    build_measured_initial_profile,
    save_measured_initial_profile_csv,
    save_measured_profile_plot,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert RAW ECV/SIMS files into a unified measured initial profile CSV.")
    parser.add_argument("--ecv-csv", default="inputs/raw_measurements/CTV-ECV-RAW.csv")
    parser.add_argument("--sims-xlsx", default="inputs/raw_measurements/CTV-SIMS-RAW.xlsx")
    parser.add_argument("--sims-location", default="CTV")
    parser.add_argument("--output-csv", default="inputs/measured_profiles/ctv_measured_initial_profile.csv")
    parser.add_argument("--output-plot", default="inputs/measured_profiles/ctv_measured_initial_profile.png")
    parser.add_argument("--output-summary", default="inputs/measured_profiles/ctv_measured_initial_profile_summary.json")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    ecv_path = ROOT / args.ecv_csv
    sims_path = ROOT / args.sims_xlsx
    if not ecv_path.exists() and Path(args.ecv_csv).as_posix() == "inputs/raw_measurements/CTV-ECV-RAW.csv":
        ecv_path = ROOT / "CTV-ECV-RAW.csv"
    if not sims_path.exists() and Path(args.sims_xlsx).as_posix() == "inputs/raw_measurements/CTV-SIMS-RAW.xlsx":
        sims_path = ROOT / "CTV-SIMS-RAW.xlsx"

    profile = build_measured_initial_profile(
        ecv_csv_path=ecv_path,
        sims_xlsx_path=sims_path,
        sims_location=args.sims_location,
    )
    csv_path = save_measured_initial_profile_csv(profile, ROOT / args.output_csv)
    plot_path = save_measured_profile_plot(profile, ROOT / args.output_plot)

    summary = {
        "ecv_csv": str(ecv_path),
        "sims_xlsx": str(sims_path),
        "sims_location": args.sims_location,
        "output_csv": str(csv_path),
        "output_plot": str(plot_path),
        "n_points": int(profile.depth_nm.size),
        "surface_total_p_cm3": float(profile.total_p_cm3[0]),
        "surface_active_p_cm3": float(profile.active_p_cm3[0]),
        "surface_inactive_p_cm3": float(profile.inactive_p_cm3[0]),
        "max_depth_nm": float(profile.depth_nm[-1]),
    }
    summary_path = ROOT / args.output_summary
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Saved measured profile CSV to: {csv_path}")
    print(f"Saved measured profile plot to: {plot_path}")
    print(f"Saved measured profile summary to: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
