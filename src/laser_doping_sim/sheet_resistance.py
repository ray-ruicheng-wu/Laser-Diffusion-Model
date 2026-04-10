from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.constants import e as elementary_charge


@dataclass(slots=True)
class MasettiElectronMobilityModel:
    temperature_k: float = 300.0
    mu_max_cm2_v_s: float = 1417.0
    mu_min1_cm2_v_s: float = 52.2
    mu_min2_cm2_v_s: float = 52.2
    mu_1_cm2_v_s: float = 43.4
    c_r_cm3: float = 9.68e16
    c_s_cm3: float = 3.43e20
    alpha: float = 0.68
    beta: float = 2.0
    p_c_cm3: float = 0.0


def masetti_electron_mobility_cm2_v_s(
    ionized_impurity_cm3: np.ndarray,
    model: MasettiElectronMobilityModel | None = None,
) -> np.ndarray:
    """Return the 300 K Masetti electron mobility in single-crystal silicon.

    The parameter set follows the widely used phosphorus-doped silicon form of
    the Masetti et al. model. The input is the total ionized impurity
    concentration, not the net donor concentration.
    """

    coefficients = model or MasettiElectronMobilityModel()
    concentration_cm3 = np.maximum(np.asarray(ionized_impurity_cm3, dtype=float), 1.0)
    return (
        coefficients.mu_min1_cm2_v_s * np.exp(-coefficients.p_c_cm3 / concentration_cm3)
        + (coefficients.mu_max_cm2_v_s - coefficients.mu_min2_cm2_v_s)
        / (1.0 + np.power(concentration_cm3 / coefficients.c_r_cm3, coefficients.alpha))
        - coefficients.mu_1_cm2_v_s
        / (1.0 + np.power(coefficients.c_s_cm3 / concentration_cm3, coefficients.beta))
    )


def majority_electron_density_cm3(
    active_donor_cm3: np.ndarray,
    acceptor_cm3: np.ndarray | float,
) -> np.ndarray:
    return np.maximum(np.asarray(active_donor_cm3, dtype=float) - np.asarray(acceptor_cm3, dtype=float), 0.0)


def ionized_impurity_density_cm3(
    active_donor_cm3: np.ndarray,
    acceptor_cm3: np.ndarray | float,
) -> np.ndarray:
    return np.maximum(np.asarray(active_donor_cm3, dtype=float), 0.0) + np.maximum(
        np.asarray(acceptor_cm3, dtype=float), 0.0
    )


def conductivity_profile_s_per_cm(
    active_donor_cm3: np.ndarray,
    acceptor_cm3: np.ndarray | float,
    mobility_model: MasettiElectronMobilityModel | None = None,
) -> np.ndarray:
    majority_electrons = majority_electron_density_cm3(active_donor_cm3, acceptor_cm3)
    ionized_impurities = ionized_impurity_density_cm3(active_donor_cm3, acceptor_cm3)
    mobility_cm2_v_s = masetti_electron_mobility_cm2_v_s(ionized_impurities, mobility_model)
    return elementary_charge * mobility_cm2_v_s * majority_electrons


def sheet_conductance_s_per_sq(
    depth_m: np.ndarray,
    conductivity_s_per_cm: np.ndarray,
) -> float:
    depth_cm = np.asarray(depth_m, dtype=float) * 1.0e2
    conductivity = np.asarray(conductivity_s_per_cm, dtype=float)
    return float(np.trapezoid(conductivity, depth_cm))


def sheet_resistance_ohm_per_sq(
    depth_m: np.ndarray,
    active_donor_cm3: np.ndarray,
    acceptor_cm3: np.ndarray | float,
    mobility_model: MasettiElectronMobilityModel | None = None,
) -> float:
    conductance = sheet_conductance_s_per_sq(
        depth_m,
        conductivity_profile_s_per_cm(active_donor_cm3, acceptor_cm3, mobility_model),
    )
    if conductance <= 0.0:
        return float("inf")
    return 1.0 / conductance
