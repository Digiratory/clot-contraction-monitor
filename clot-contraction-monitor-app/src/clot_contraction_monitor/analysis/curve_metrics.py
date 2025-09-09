"""Curve parameter computation module for batched analysis of contraction curves."""

import logging
import warnings
from typing import Dict, Optional, Tuple

import numpy as np
from scipy.optimize import curve_fit

logger = logging.getLogger(__name__)


def second_order_response(t, A, tau1, tau2, delay, y0):
    """Inverted 2nd order aperiodic transfer function starting from high to low."""
    t_adj = np.maximum(t - delay, 0)
    # A * (1 - exp(-t/tau1) - exp(-t/tau2)) + baseline
    response = (
        y0
        - ((A * tau1) / (tau2 - tau1)) * np.exp(-t_adj / tau1)
        - ((A * tau2) / (tau1 - tau2)) * np.exp(-t_adj / tau2)
    )
    return response


def second_order_response_div(t, A, tau1, tau2, delay, y0):
    """Derriative of inverted 2nd order aperiodic transfer function starting from high to low."""
    t_adj = np.maximum(t - delay, 0)
    # A * (1 - exp(-t/tau1) - exp(-t/tau2)) + baseline
    response = (-(t_adj * A) / (tau2 - tau1)) * np.exp(-t_adj / tau1) + (
        (A * t_adj) / (tau1 - tau2)
    ) * np.exp(-t_adj / tau2)
    return response


def solve_crossover_equation(t_rel, A, tau1, tau2):
    """Solve for time to crossover point using second_order_response."""
    # Crossover when response reaches 50% of its range
    # Let tau_min = min(tau1, tau2), tau_max = max(tau1, tau2)

    # For better numerical stability, use the dominant time constant approach
    if tau1 < tau2:
        # First exponent dominates: exp(-t/τ1) + exp(-t/τ2) ≈ exp(-t/τ1)
        # So we solve: exp(-t/τ1) + exp(-t/τ2) + exp(-t/τ1)*exp(-t/τ2) ≈ exp(-t/τ1)
        # This is complex, so use simpler approximation
        exp1 = np.exp(-t_rel / tau1)
        exp2 = np.exp(-t_rel / tau2)

        # Solve for: exp(-t/τ1) + exp(-t/τ2) = 0.5
        return exp1 + exp2 - 0.5
    else:
        # Similar logic but switch_tau1 and tau2 if needed
        exp1 = np.exp(-t_rel / tau2)
        exp2 = np.exp(-t_rel / tau1)
        return exp1 + exp2 - 0.5


def analyze_curve_batch(curves: np.ndarray) -> Dict[str, np.ndarray]:
    """Analyze batch of contraction curves and compute biological parameters.

    Curves follow inverted 2nd order aperiodic transfer function:
    flat initial (~1.0) -> monotonic decrease -> flat final (~0.0).

    Args:
        curves: 2D array of shape (L, N) where L is frames, N is curves

    Returns:
        Dictionary containing parameter arrays of shape (N,):
        - crossover_position: Frame index at 50% transition point (halfway to final)
        - last_index_95p: Last index > 95% of initial value
        - first_index_5p: First index < 5% of initial value

    Raises:
        ValueError: If input validation fails
    """
    if curves.ndim != 2:
        raise ValueError("Input must be a 2D array with shape (frames, curves)")
    if curves.size == 0:
        raise ValueError("Input array cannot be empty")
    if not np.issubdtype(curves.dtype, np.number):
        raise ValueError("Input array must contain numeric data")

    logger.info(
        f"Analyzing {curves.shape[1]} curves with {curves.shape[0]} frames each"
    )

    # Use scipy curve fitting if available, otherwise numpy-based
    result, fitted_curves = _analyze_with_curve_fit(curves)

    logger.info(f"Analysis completed for {curves.shape[1]} curves")
    return result, fitted_curves


def _analyze_with_curve_fit(curves: np.ndarray) -> Dict[str, np.ndarray]:
    """Analyze curves using scipy.optimize.curve_fit with 2nd order aperiodic response."""
    params = {}
    for param_name in ["crossover_position", "last_index_95p", "first_index_5p"]:
        params[param_name] = np.full(curves.shape[1], np.nan, dtype=float)

    fitted_curves = np.zeros_like(curves)
    for i in range(curves.shape[1]):
        curve = curves[:, i]
        t = np.arange(len(curve))

        # Check if curve is valid for analysis before trying to fit
        if not _is_curve_valid_for_analysis(curve):
            params["crossover_position"][i] = np.nan
            params["last_index_95p"][i] = np.nan
            params["first_index_5p"][i] = np.nan
            continue

        try:
            # Initial parameters guess
            A_guess = np.max(curve)  # Amplitude
            tau1_guess = len(curve) / 8  # Time constant 1
            tau2_guess = len(curve) / 4  # Time constant 2
            delay_guess = len(curve) / 10  # Delay before start
            y0_guess = np.min(curve)  # Baseline value

            p0 = [A_guess, tau1_guess, tau2_guess, delay_guess, y0_guess]

            # Bounds for parameters
            bounds = (
                [-2.0, -len(curve), -len(curve), -len(curve), -2],  # Lower bounds
                [2.0, len(curve), len(curve), len(curve), 2],  # Upper bounds
            )

            # Fit the curve
            popt, pcov = curve_fit(
                second_order_response,
                t,
                curve,
                p0=p0,
                bounds=bounds,
                maxfev=5000,
                # method='trf'
            )

            A_fit, tau1_fit, tau2_fit, delay_fit, y0_fit = popt

            # Generate fitted curve for parameter computation
            fitted_curve = second_order_response(
                t, A_fit, tau1_fit, tau2_fit, delay_fit, y0_fit
            )
            fitted_curve_div = second_order_response_div(
                t, A_fit, tau1_fit, tau2_fit, delay_fit, y0_fit
            )

            # Compute parameters analytically from fitted parameters
            params["crossover_position"][i] = np.argmax(np.abs(fitted_curve_div))
            params["last_index_95p"][i] = _find_last_above_percentile(
                fitted_curve, 0.95
            )
            params["first_index_5p"][i] = _find_first_below_percentile(
                fitted_curve, 0.05
            )
            fitted_curves[:, i] = fitted_curve

        except Exception as e:
            logger.debug(f"Curve fitting failed for curve {i}: {e}")
    return params, fitted_curves


def _find_last_above_percentile(curve: np.ndarray, percentile: float) -> float:
    """Find last index where curve is above percentile of initial value."""
    max_val = curve.max()
    min_val = curve.min()

    threshold = (max_val - min_val) * percentile + min_val

    above = curve > threshold
    if np.any(above):
        return float(np.where(above)[0][-1])
    return np.nan


def _find_first_below_percentile(curve: np.ndarray, percentile: float) -> float:
    """Find first index where curve is below percentile of initial value."""
    max_val = curve.max()
    min_val = curve.min()

    threshold = (max_val - min_val) * percentile + min_val

    below = curve < threshold
    if np.any(below):
        return float(np.where(below)[0][0])
    return np.nan


def _is_curve_valid_for_analysis(curve: np.ndarray) -> bool:
    """Check if curve is suitable for parameter extraction."""
    if len(curve) < 5:
        return False

    # Basic sanity checks
    if np.all(np.isnan(curve)) or np.all(curve == 0):
        return False

    # Check for sufficient dynamic range - must have meaningful signal variation
    curve_range = np.max(curve) - np.min(curve)
    if curve_range < 0.05:  # Require at least 5% change for biological relevance
        return False

    # Check that curve actually shows significant biological behavior
    # For clot contraction, we expect curves to start in one state and end in another
    initial_region = curve[: len(curve) // 4]  # First 25%
    final_region = curve[len(curve) * 3 // 4 :]  # Last 25%

    initial_mean = np.mean(initial_region)
    final_mean = np.mean(final_region)

    # Require at least 15% difference between initial and final regions
    if abs(initial_mean - final_mean) / initial_mean < 0.15:
        return False  # Too flat, not biologically meaningful

    # Check for monotonic decrease trend (should be mostly decreasing)
    gradients = np.gradient(curve)
    mean_gradient = np.mean(gradients)
    if mean_gradient > 0.01:  # Allow small positive gradients due to noise
        return False

    return True
