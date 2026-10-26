
"""Experiment-readiness and quality checks for Idle Loop Observatory."""

from math import isclose

import pandas as pd
from scipy.stats import chisquare


def filter_mature_players(
    df: pd.DataFrame,
    observation_day: int,
    install_column: str = "install_timestamp_utc",
    cutoff_timestamp: str | pd.Timestamp | None = None,
    processing_delay_hours: int = 0,
) -> pd.DataFrame:
    """Keep players whose retention observation window has elapsed.

    Eligibility uses installation time and a fixed analysis cutoff,
    not the player's last session time.
    """
    if observation_day < 0:
        raise ValueError("observation_day cannot be negative.")

    if processing_delay_hours < 0:
        raise ValueError("processing_delay_hours cannot be negative.")

    if install_column not in df.columns:
        raise ValueError(f"Missing required column: {install_column}")

    if cutoff_timestamp is None:
        cutoff = pd.Timestamp.now(tz="UTC")
    else:
        cutoff = pd.Timestamp(cutoff_timestamp)

        if cutoff.tzinfo is None:
            raise ValueError("cutoff_timestamp must include a timezone.")

        cutoff = cutoff.tz_convert("UTC")

    # Parse ISO-8601 timestamps consistently; invalid timestamps become NaT.
    install_times = pd.to_datetime(
        df[install_column],
        format="mixed",
        errors="coerce",
        utc=True,
    )

    required_age = pd.Timedelta(days=observation_day)
    ingestion_delay = pd.Timedelta(hours=processing_delay_hours)

    eligible = (
        install_times.notna()
        & (install_times + required_age + ingestion_delay <= cutoff)
    )

    return df.loc[eligible].copy()


def check_sample_ratio(
    control_count: int,
    treatment_count: int,
    expected_control_share: float = 0.5,
    alpha: float = 0.001,
) -> dict:
    """Flag potential sample-ratio mismatch using a chi-square test."""
    if control_count < 0 or treatment_count < 0:
        raise ValueError("Assignment counts cannot be negative.")

    total = control_count + treatment_count

    if total == 0:
        raise ValueError("At least one assignment is required.")

    if not 0 < expected_control_share < 1:
        raise ValueError("expected_control_share must be between 0 and 1.")

    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1.")

    observed = [control_count, treatment_count]
    expected = [
        total * expected_control_share,
        total * (1 - expected_control_share),
    ]

    statistic, p_value = chisquare(
        f_obs=observed,
        f_exp=expected,
    )

    return {
        "control_count": control_count,
        "treatment_count": treatment_count,
        "observed_control_share": control_count / total,
        "expected_control_share": expected_control_share,
        "chi_square_statistic": float(statistic),
        "p_value": float(p_value),
        "alpha": alpha,
        "srm_flag": bool(p_value < alpha),
    }


def summarize_binary_metrics(
    df: pd.DataFrame,
    assignment_column: str,
    control_label: str,
    treatment_label: str,
    metrics: list[str],
) -> pd.DataFrame:
    """Summarize binary outcomes and treatment-versus-control differences."""
    if not metrics:
        raise ValueError("At least one metric must be supplied.")

    required = [assignment_column, *metrics]
    missing = [column for column in required if column not in df.columns]

    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    if control_label == treatment_label:
        raise ValueError("Control and treatment labels must be different.")

    arms = df[assignment_column]

    if arms.isna().any():
        raise ValueError("Experiment assignment contains missing values.")

    if not arms.isin([control_label, treatment_label]).all():
        raise ValueError("Unexpected experiment assignment labels.")

    rows = []

    for metric in metrics:
        values = pd.to_numeric(df[metric], errors="coerce")
        non_missing = values.dropna()

        if not non_missing.isin([0, 1]).all():
            raise ValueError(
                f"Metric '{metric}' must contain only 0/1 values "
                "or missing values."
            )

        control = values[arms == control_label].dropna()
        treatment = values[arms == treatment_label].dropna()

        if control.empty or treatment.empty:
            raise ValueError(
                f"Metric '{metric}' needs observed values in both arms."
            )

        control_rate = float(control.mean())
        treatment_rate = float(treatment.mean())

        relative_lift = (
            (treatment_rate / control_rate - 1) * 100
            if not isclose(control_rate, 0.0)
            else None
        )

        rows.append(
            {
                "metric": metric,
                "control_n": len(control),
                "treatment_n": len(treatment),
                "control_rate_pct": control_rate * 100,
                "treatment_rate_pct": treatment_rate * 100,
                "absolute_lift_pp": (
                    treatment_rate - control_rate
                ) * 100,
                "relative_lift_pct": relative_lift,
            }
        )

    return pd.DataFrame(rows)
