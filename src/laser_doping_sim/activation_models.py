from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(slots=True)
class PiecewiseLinearNonactiveActivationModel:
    initial_inactive_activation_fraction: float
    power_w: np.ndarray
    final_nonactive_activation_fraction: np.ndarray

    def fraction_at_power(self, power_w: float) -> float:
        if self.power_w.size == 0:
            raise ValueError("Activation model has no support points.")
        value = float(
            np.interp(
                float(power_w),
                self.power_w,
                self.final_nonactive_activation_fraction,
                left=self.final_nonactive_activation_fraction[0],
                right=self.final_nonactive_activation_fraction[-1],
            )
        )
        return min(1.0, max(0.0, value))


@dataclass(slots=True)
class PiecewiseLinearDualChannelActivationModel:
    initial_inactive_activation_fraction: float
    power_w: np.ndarray
    final_inactive_activation_fraction: np.ndarray
    final_injected_activation_fraction: np.ndarray

    def inactive_fraction_at_power(self, power_w: float) -> float:
        if self.power_w.size == 0:
            raise ValueError("Dual-channel activation model has no support points.")
        value = float(
            np.interp(
                float(power_w),
                self.power_w,
                self.final_inactive_activation_fraction,
                left=self.final_inactive_activation_fraction[0],
                right=self.final_inactive_activation_fraction[-1],
            )
        )
        return min(1.0, max(0.0, value))

    def injected_fraction_at_power(self, power_w: float) -> float:
        if self.power_w.size == 0:
            raise ValueError("Dual-channel activation model has no support points.")
        value = float(
            np.interp(
                float(power_w),
                self.power_w,
                self.final_injected_activation_fraction,
                left=self.final_injected_activation_fraction[0],
                right=self.final_injected_activation_fraction[-1],
            )
        )
        return min(1.0, max(0.0, value))


def load_piecewise_nonactive_activation_model_csv(
    path: str | Path,
    initial_inactive_activation_fraction: float,
) -> PiecewiseLinearNonactiveActivationModel:
    rows: list[tuple[float, float]] = []
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"power_w", "effective_final_nonactive_activation_fraction"}
        if not required.issubset(set(reader.fieldnames or [])):
            raise ValueError(
                "Activation model CSV must contain columns: "
                "power_w,effective_final_nonactive_activation_fraction"
            )
        for row in reader:
            rows.append(
                (
                    float(row["power_w"]),
                    float(row["effective_final_nonactive_activation_fraction"]),
                )
            )

    if not rows:
        raise ValueError("Activation model CSV is empty.")

    rows.sort(key=lambda item: item[0])
    power_w = np.asarray([item[0] for item in rows], dtype=float)
    final_nonactive_activation_fraction = np.asarray([item[1] for item in rows], dtype=float)
    return PiecewiseLinearNonactiveActivationModel(
        initial_inactive_activation_fraction=float(initial_inactive_activation_fraction),
        power_w=power_w,
        final_nonactive_activation_fraction=final_nonactive_activation_fraction,
    )


def load_piecewise_dual_channel_activation_model_csv(
    path: str | Path,
    initial_inactive_activation_fraction: float,
) -> PiecewiseLinearDualChannelActivationModel:
    rows: list[tuple[float, float, float]] = []
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {
            "power_w",
            "effective_final_inactive_activation_fraction",
            "effective_final_injected_activation_fraction",
        }
        if not required.issubset(set(reader.fieldnames or [])):
            raise ValueError(
                "Dual-channel activation model CSV must contain columns: "
                "power_w,effective_final_inactive_activation_fraction,"
                "effective_final_injected_activation_fraction"
            )
        for row in reader:
            rows.append(
                (
                    float(row["power_w"]),
                    float(row["effective_final_inactive_activation_fraction"]),
                    float(row["effective_final_injected_activation_fraction"]),
                )
            )

    if not rows:
        raise ValueError("Dual-channel activation model CSV is empty.")

    rows.sort(key=lambda item: item[0])
    power_w = np.asarray([item[0] for item in rows], dtype=float)
    final_inactive_activation_fraction = np.asarray([item[1] for item in rows], dtype=float)
    final_injected_activation_fraction = np.asarray([item[2] for item in rows], dtype=float)
    return PiecewiseLinearDualChannelActivationModel(
        initial_inactive_activation_fraction=float(initial_inactive_activation_fraction),
        power_w=power_w,
        final_inactive_activation_fraction=final_inactive_activation_fraction,
        final_injected_activation_fraction=final_injected_activation_fraction,
    )
