# 60-90W Power Scan Report

## 1. Scan Scope

This scan uses the current Phase 3 project baseline:

1. `532 nm`
2. `500 kHz`
3. `95 um` square flat-top
4. `9%` surface reflectance
5. `PSG` finite source with `finite_source_cell + melt_only`
6. Base active emitter:
   - surface `P = 3.5e20 cm^-3`
   - junction depth `300 nm`
7. Initial inactive surface `P` layer:
   - thickness `30 nm`
   - concentration `5e20 cm^-3`

Primary scan output:

- [power_scan_summary.csv](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/power_scan_60_90w_dt01/power_scan_summary.csv)
- [power_vs_peak_temperature.png](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/power_scan_60_90w_dt01/power_vs_peak_temperature.png)
- [power_vs_melt_depth.png](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/power_scan_60_90w_dt01/power_vs_melt_depth.png)
- [power_vs_junction_depth.png](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/power_scan_60_90w_dt01/power_vs_junction_depth.png)
- [power_vs_final_peak_p.png](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/power_scan_60_90w_dt01/power_vs_final_peak_p.png)
- [power_vs_final_net_donor_sheet_dose.png](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/power_scan_60_90w_dt01/power_vs_final_net_donor_sheet_dose.png)

## 2. Official Readout

The scan was first run with `dt = 0.2 ns`, but that version showed non-physical high-power inversion between `85 W` and `90 W`.

That version is not the formal readout.

The current formal scan is:

- `outputs/phase3/power_scan_60_90w_dt01`

because:

1. it removes the `85W/90W` inversion
2. it is more numerically stable
3. it passed review-line re-check as the current publishable scan baseline

## 3. Result Table

| Power | Fluence | Peak Si Surface T | Max Liquid Fraction | Max Melt Depth | Final Peak P | Final Junction Depth |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `60 W` | `1.330 J/cm^2` | `1678.6 K` | `0.161` | `0 nm` | `8.594e20 cm^-3` | `302.4 nm` |
| `65 W` | `1.440 J/cm^2` | `1678.1 K` | `0.145` | `0 nm` | `8.578e20 cm^-3` | `305.0 nm` |
| `70 W` | `1.551 J/cm^2` | `1681.0 K` | `0.265` | `0 nm` | `8.075e20 cm^-3` | `312.1 nm` |
| `75 W` | `1.662 J/cm^2` | `1682.2 K` | `0.317` | `0 nm` | `7.942e20 cm^-3` | `320.2 nm` |
| `80 W` | `1.773 J/cm^2` | `1683.2 K` | `0.364` | `0 nm` | `7.957e20 cm^-3` | `330.2 nm` |
| `85 W` | `1.884 J/cm^2` | `1685.1 K` | `0.453` | `0 nm` | `8.136e20 cm^-3` | `344.7 nm` |
| `90 W` | `1.994 J/cm^2` | `1690.1 K` | `0.700` | `346.2 nm` | `8.593e20 cm^-3` | `371.4 nm` |

## 4. Main Interpretation

Current interpretation:

1. `60-85 W` sits in a near-threshold regime.
2. `90 W` is the first point in this scan that shows a clear nonzero melt depth.
3. The threshold for obvious remelt-assisted junction extension is therefore currently between `85 W` and `90 W`.

This agrees with the literature-level intuition that precursor-assisted phosphorus laser doping becomes much more effective once silicon clearly enters the molten regime.

## 5. Important Caveat

There is still one model-interpretation risk in the current code:

1. `max_melt_depth` is counted with a stricter melt criterion.
2. `melt_only` source injection is gated with `interface_liquid_threshold = 0.01`.

So the current implementation can produce:

- `no formal melt depth`
- but still `nonzero source injection`
- and therefore a slow junction increase in the `60-85 W` range

Review line judged this as numerically self-consistent for the current code.

Research line judged that the trend is physically plausible as a near-threshold regime, but also flagged that this naming/threshold mismatch should be cleaned up in a future refinement.

## 6. Best Next Step

The most valuable follow-up scan is:

1. `85-90 W`
2. smaller power step, e.g. `1-2 W`
3. at least one finer time-step check, e.g. `dt = 0.05 ns`

That will tighten the current estimate of the remelt threshold.
