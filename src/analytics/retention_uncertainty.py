
"""Quantify uncertainty in synthetic player-retention comparisons.

All outputs concern simulated development data, not real players.

Methods:
- Wilson 95% confidence intervals for individual retention rates.
- Newcombe 95% confidence interval for the difference between two
  independent proportions, constructed from Wilson intervals.
- Two-proportion z-test for comparing retention rates.

Important:
- These are observational comparisons, not randomized experiments.
- Statistical significance does not establish causation.
- Synthetic results cannot support real-world game-product claims.
"""

from pathlib import Path

import duckdb
import pandas as pd
from statsmodels.stats.proportion import (
    confint_proportions_2indep,
    proportion_confint,
    proportions_ztest,
)


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "synthetic" / "idle_game_events.csv"
ALPHA = 0.05


def load_player_outcomes() -> pd.DataFrame:
    """Create one row per installed player with tutorial and retention flags."""

    query = """
    WITH events AS (
        SELECT *
        FROM read_csv_auto(?)
    ),

    tutorial AS (
        SELECT
            player_id,
            MAX(
                CASE
                    WHEN event_name = 'tutorial_complete'
                     AND TRY_CAST(days_since_install AS INTEGER) = 0
                    THEN 1
                    ELSE 0
                END
            ) AS completed_tutorial
        FROM events
        GROUP BY player_id
    ),

    installs AS (
        SELECT
            player_id,
            MAX(acquisition_channel) AS acquisition_channel,
            MAX(platform) AS platform
        FROM events
        WHERE event_name = 'install'
        GROUP BY player_id
    ),

    activity AS (
        SELECT
            player_id,

            MAX(
                CASE
                    WHEN event_name = 'session_start'
                     AND TRY_CAST(days_since_install AS INTEGER) = 1
                    THEN 1
                    ELSE 0
                END
            ) AS d1,

            MAX(
                CASE
                    WHEN event_name = 'session_start'
                     AND TRY_CAST(days_since_install AS INTEGER) = 7
                    THEN 1
                    ELSE 0
                END
            ) AS d7

        FROM events
        GROUP BY player_id
    )

    SELECT
        i.player_id,
        i.acquisition_channel,
        i.platform,
        COALESCE(t.completed_tutorial, 0) AS completed_tutorial,
        COALESCE(a.d1, 0) AS d1,
        COALESCE(a.d7, 0) AS d7
    FROM installs AS i
    LEFT JOIN tutorial AS t USING (player_id)
    LEFT JOIN activity AS a USING (player_id)
    ORDER BY i.player_id
    """

    with duckdb.connect() as conn:
        df = conn.execute(query, [str(DATA)]).df()

    if df.empty:
        raise ValueError("No installed players found in the dataset.")

    if df["player_id"].duplicated().any():
        raise ValueError(
            "Expected one row per installed player, but duplicates were found."
        )

    return df


def summarize_rate(
    label: str,
    successes: int,
    total: int,
) -> dict:
    """Summarize a retention rate and its Wilson confidence interval."""

    if total <= 0:
        raise ValueError(f"Cannot calculate a rate for an empty group: {label}")

    if not 0 <= successes <= total:
        raise ValueError(
            f"Invalid counts for {label}: {successes} successes out of {total}"
        )

    rate = successes / total

    low, high = proportion_confint(
        count=successes,
        nobs=total,
        alpha=ALPHA,
        method="wilson",
    )

    return {
        "segment": label,
        "players": total,
        "retained": successes,
        "retention_pct": round(rate * 100, 2),
        "ci_95_low_pct": round(low * 100, 2),
        "ci_95_high_pct": round(high * 100, 2),
    }


def compare_groups(
    df: pd.DataFrame,
    metric: str,
    group_column: str,
    group_a,
    group_b,
) -> dict:
    """Compare two independent groups using a z-test and Newcombe interval.

    The reported difference is Group A minus Group B, in percentage points.
    """

    a = df.loc[df[group_column] == group_a, metric].astype(int)
    b = df.loc[df[group_column] == group_b, metric].astype(int)

    count_a, count_b = int(a.sum()), int(b.sum())
    n_a, n_b = len(a), len(b)

    if n_a == 0 or n_b == 0:
        raise ValueError(
            f"Cannot compare empty groups: {group_a!r} vs {group_b!r}"
        )

    rate_a = count_a / n_a
    rate_b = count_b / n_b
    difference = rate_a - rate_b

    # Two-sided test of equal proportions.
    z_stat, p_value = proportions_ztest(
        count=[count_a, count_b],
        nobs=[n_a, n_b],
        alternative="two-sided",
    )

    # Newcombe confidence interval for the difference between proportions.
    # Group A is the first proportion; Group B is the second.
    ci_low, ci_high = confint_proportions_2indep(
        count1=count_a,
        nobs1=n_a,
        count2=count_b,
        nobs2=n_b,
        method="newcomb",
        compare="diff",
        alpha=ALPHA,
    )

    print(f"\nComparison: {group_a} vs {group_b} ({metric.upper()})")
    print("-" * 64)
    print(f"Group A: {count_a}/{n_a} = {rate_a:.2%}")
    print(f"Group B: {count_b}/{n_b} = {rate_b:.2%}")
    print(f"Difference (A - B): {difference * 100:+.2f} percentage points")
    print(
        "95% Newcombe CI for difference: "
        f"[{ci_low * 100:+.2f}, {ci_high * 100:+.2f}] "
        "percentage points"
    )
    print(f"Two-proportion z statistic: {z_stat:.3f}")
    print(f"Two-sided p-value: {p_value:.4f}")

    # The interval and test are related but are not mathematically identical
    # procedures. Report both rather than treating them as interchangeable.
    if p_value < ALPHA:
        print(
            "Test interpretation: evidence against equal retention rates "
            "at the 5% significance level under the test assumptions."
        )
    else:
        print(
            "Test interpretation: insufficient evidence to reject equal "
            "retention rates at the 5% significance level."
        )

    if ci_low <= 0 <= ci_high:
        print(
            "Interval interpretation: the 95% confidence interval includes "
            "zero difference."
        )
    else:
        print(
            "Interval interpretation: the 95% confidence interval excludes "
            "zero difference."
        )

    print(
        "Caution: this is an observational comparison of synthetic data. "
        "It does not establish causation."
    )

    return {
        "metric": metric,
        "group_a": str(group_a),
        "group_b": str(group_b),
        "n_a": n_a,
        "n_b": n_b,
        "rate_a": rate_a,
        "rate_b": rate_b,
        "difference": difference,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "z_stat": z_stat,
        "p_value": p_value,
    }


def main() -> None:
    """Run the retention uncertainty analysis."""

    if not DATA.exists():
        raise FileNotFoundError(
            f"Expected synthetic dataset was not found: {DATA}"
        )

    df = load_player_outcomes()

    print("=" * 72)
    print("IDLE LOOP OBSERVATORY")
    print("SYNTHETIC DATA ONLY — NOT REAL PLAYER EVIDENCE")
    print("=" * 72)
    print(f"Unique installed players: {df['player_id'].nunique():,}")
    print(f"Dataset: {DATA.relative_to(ROOT)}")
    print(f"Significance level: {ALPHA:.0%}")
    print("Rate intervals: Wilson")
    print("Difference interval: Newcombe")
    print("Comparison test: two-sided two-proportion z-test")

    tutorial_groups = [
        (1, "Completed tutorial"),
        (0, "Did not complete"),
    ]

    results = []

    for metric in ["d1", "d7"]:
        print(f"\n{'=' * 72}")
        print(f"{metric.upper()} RETENTION — 95% WILSON INTERVALS")
        print("=" * 72)

        rows = []

        for value, label in tutorial_groups:
            subset = df[df["completed_tutorial"] == value]
            successes = int(subset[metric].sum())
            total = len(subset)

            rows.append(
                summarize_rate(
                    label=label,
                    successes=successes,
                    total=total,
                )
            )

        print(
            pd.DataFrame(rows).to_string(
                index=False,
                formatters={
                    "retention_pct": "{:.2f}".format,
                    "ci_95_low_pct": "{:.2f}".format,
                    "ci_95_high_pct": "{:.2f}".format,
                },
            )
        )

        result = compare_groups(
            df=df,
            metric=metric,
            group_column="completed_tutorial",
            group_a=1,
            group_b=0,
        )
        results.append(result)

    print(f"\n{'=' * 72}")
    print("SUMMARY OF GROUP COMPARISONS")
    print("=" * 72)

    summary = pd.DataFrame(
        [
            {
                "metric": r["metric"].upper(),
                "difference_pp": round(r["difference"] * 100, 2),
                "ci_95_low_pp": round(r["ci_low"] * 100, 2),
                "ci_95_high_pp": round(r["ci_high"] * 100, 2),
                "p_value": round(r["p_value"], 4),
            }
            for r in results
        ]
    )

    print(summary.to_string(index=False))
    print(
        "\nDecision note: observational segment differences are useful for "
        "forming hypotheses, not proving that tutorial completion causes "
        "retention changes. Validate any product hypothesis with an "
        "appropriately designed experiment and pre-specified metrics."
    )


if __name__ == "__main__":
    main()
