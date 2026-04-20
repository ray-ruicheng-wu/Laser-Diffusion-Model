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


@dataclass(slots=True)
class PiecewiseMultiShotDualChannelActivationModel:
    initial_inactive_activation_fraction: float
    power_w: np.ndarray
    inactive_shot1_fraction: np.ndarray
    inactive_inf_fraction: np.ndarray
    inactive_n0_shots: np.ndarray
    injected_shot1_fraction: np.ndarray
    injected_inf_fraction: np.ndarray
    injected_reference_dose_cm2: np.ndarray
    injected_q0_cm2: np.ndarray

    def _interp(self, values: np.ndarray, power_w: float) -> float:
        if self.power_w.size == 0:
            raise ValueError("Multi-shot dual-channel activation model has no support points.")
        return float(
            np.interp(
                float(power_w),
                self.power_w,
                values,
                left=values[0],
                right=values[-1],
            )
        )

    def inactive_fraction_at_state(self, power_w: float, shot_index: int | float) -> float:
        eta1 = self._interp(self.inactive_shot1_fraction, power_w)
        eta_inf = self._interp(self.inactive_inf_fraction, power_w)
        n0 = max(self._interp(self.inactive_n0_shots, power_w), 1.0e-12)
        extra_shots = max(float(shot_index) - 1.0, 0.0)
        value = eta1 + (eta_inf - eta1) * (1.0 - np.exp(-extra_shots / n0))
        return min(1.0, max(0.0, float(value)))

    def injected_fraction_at_state(
        self,
        power_w: float,
        cumulative_injected_dose_cm2: float,
    ) -> float:
        eta1 = self._interp(self.injected_shot1_fraction, power_w)
        eta_inf = self._interp(self.injected_inf_fraction, power_w)
        q_ref = max(self._interp(self.injected_reference_dose_cm2, power_w), 0.0)
        q0 = self._interp(self.injected_q0_cm2, power_w)
        extra_dose = max(float(cumulative_injected_dose_cm2) - q_ref, 0.0)
        if q0 <= 0.0:
            value = eta_inf if extra_dose > 0.0 else eta1
        else:
            value = eta1 + (eta_inf - eta1) * (1.0 - np.exp(-extra_dose / q0))
        return min(1.0, max(0.0, float(value)))

    def fractions_at_state(
        self,
        power_w: float,
        shot_index: int | float,
        cumulative_injected_dose_cm2: float,
    ) -> tuple[float, float]:
        return (
            self.inactive_fraction_at_state(power_w, shot_index),
            self.injected_fraction_at_state(power_w, cumulative_injected_dose_cm2),
        )


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


def load_piecewise_multishot_dual_channel_activation_model_csv(
    path: str | Path,
    initial_inactive_activation_fraction: float,
) -> PiecewiseMultiShotDualChannelActivationModel:
    rows: list[tuple[float, float, float, float, float, float, float, float]] = []
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {
            "power_w",
            "eta_inactive_shot1",
            "eta_inactive_inf",
            "n0_inactive_shots",
            "eta_injected_shot1",
            "eta_injected_inf",
            "qref_injected_cm2",
            "q0_injected_cm2",
        }
        if not required.issubset(set(reader.fieldnames or [])):
            raise ValueError(
                "Multi-shot dual-channel activation CSV must contain columns: "
                "power_w,eta_inactive_shot1,eta_inactive_inf,n0_inactive_shots,"
                "eta_injected_shot1,eta_injected_inf,qref_injected_cm2,q0_injected_cm2"
            )
        for row in reader:
            rows.append(
                (
                    float(row["power_w"]),
                    float(row["eta_inactive_shot1"]),
                    float(row["eta_inactive_inf"]),
                    float(row["n0_inactive_shots"]),
                    float(row["eta_injected_shot1"]),
                    float(row["eta_injected_inf"]),
                    float(row["qref_injected_cm2"]),
                    float(row["q0_injected_cm2"]),
                )
            )

    if not rows:
        raise ValueError("Multi-shot dual-channel activation CSV is empty.")

    rows.sort(key=lambda item: item[0])
    power_w = np.asarray([item[0] for item in rows], dtype=float)
    inactive_shot1_fraction = np.asarray([item[1] for item in rows], dtype=float)
    inactive_inf_fraction = np.asarray([item[2] for item in rows], dtype=float)
    inactive_n0_shots = np.asarray([item[3] for item in rows], dtype=float)
    injected_shot1_fraction = np.asarray([item[4] for item in rows], dtype=float)
    injected_inf_fraction = np.asarray([item[5] for item in rows], dtype=float)
    injected_reference_dose_cm2 = np.asarray([item[6] for item in rows], dtype=float)
    injected_q0_cm2 = np.asarray([item[7] for item in rows], dtype=float)
    return PiecewiseMultiShotDualChannelActivationModel(
        initial_inactive_activation_fraction=float(initial_inactive_activation_fraction),
        power_w=power_w,
        inactive_shot1_fraction=inactive_shot1_fraction,
        inactive_inf_fraction=inactive_inf_fraction,
        inactive_n0_shots=inactive_n0_shots,
        injected_shot1_fraction=injected_shot1_fraction,
        injected_inf_fraction=injected_inf_fraction,
        injected_reference_dose_cm2=injected_reference_dose_cm2,
        injected_q0_cm2=injected_q0_cm2,
    )
