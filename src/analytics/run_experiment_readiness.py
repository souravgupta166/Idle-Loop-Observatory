
"""Statistical experiment-readiness report for synthetic player data.

The experiment assignment and player outcomes are synthetic. Statistical
results validate the workflow, not a real product intervention.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.analytics.experiment_quality import (
    check_sample_ratio,
    summarize_binary_metrics,
)
from src.analytics.retention_uncertainty import (
    compare_groups,
    summarize_rate,
)


ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = ROOT / "data" / "processed" / "synthetic_player_cohort.csv"
OUTPUT_DIR = ROOT / "data" / "processed"

ASSIGNMENT_OUTPUT = OUTPUT_DIR / "synthetic_experiment_assignments.csv"
METRICS_OUTPUT = OUTPUT_DIR / "synthetic_experiment_metrics.csv"
SRM_OUTPUT = OUTPUT_DIR / "synthetic_experiment_srm.json"
REPORT_OUTPUT = OUTPUT_DIR / "synthetic_experiment_readiness.md"

RANDOM_SEED = 20261026
EXPECTED_CONTROL_SHARE = 0.5
SRM_ALPHA = 0.001
OUTCOME_ALPHA = 0.05

EXPERIMENT_ID = "synthetic_retention_demo_v1"


def load_cohort() -> pd.DataFrame:
    """Load the cohort and validate provenance and outcome maturity."""
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Cohort file not found: {INPUT_PATH}. "
            "Run the cohort builder first."
        )

    df = pd.read_csv(INPUT_PATH)

    required = {
        "player_id",
        "d1_eligible",
        "d7_eligible",
        "d1_retained",
        "d7_retained",
        "is_synthetic",
    }
    missing = required - set(df.columns)

    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    if df.empty:
        raise ValueError("The cohort contains no players.")

    if df["player_id"].isna().any() or df["player_id"].duplicated().any():
        raise ValueError("Player IDs must be present and unique.")

    synthetic = df["is_synthetic"].astype(str).str.lower()
    if not synthetic.eq("true").all():
        raise ValueError("This demonstration pipeline accepts synthetic data only.")

    for column in ["d1_eligible", "d7_eligible"]:
        df[column] = (
            df[column]
            .astype(str)
            .str.lower()
            .map({"true": True, "false": False})
        )
        if df[column].isna().any():
            raise ValueError(f"{column} contains invalid eligibility values.")

    for metric, eligibility in [
        ("d1_retained", "d1_eligible"),
        ("d7_retained", "d7_eligible"),
    ]:
        values = pd.to_numeric(df[metric], errors="coerce")
        observed = values.dropna()

        if not observed.isin([0, 1]).all():
            raise ValueError(f"{metric} must contain only 0/1 or missing values.")

        if values[~df[eligibility]].notna().any():
            raise ValueError(
                f"Ineligible players must have unknown {metric} outcomes."
            )

        if values[df[eligibility]].isna().any():
            raise ValueError(
                f"Eligible players have missing {metric} outcomes."
            )

        df[metric] = values

    return df


def assign_synthetic_arms(df: pd.DataFrame) -> pd.DataFrame:
    """Create reproducible random assignments for workflow testing."""
    result = df.copy()
    rng = np.random.default_rng(RANDOM_SEED)

    result["experiment_arm"] = rng.choice(
        ["control", "treatment"],
        size=len(result),
        p=[EXPECTED_CONTROL_SHARE, 1 - EXPECTED_CONTROL_SHARE],
    )
    result["experiment_id"] = EXPERIMENT_ID
    result["assignment_seed"] = RANDOM_SEED
    result["assignment_provenance"] = "synthetic_random_assignment"

    return result


def calculate_statistical_results(
    assignments: pd.DataFrame,
    metrics: pd.DataFrame,
) -> pd.DataFrame:
    """Add rate intervals, difference intervals, and two-sided test results.

    Only eligible players are included for each retention metric.
    The difference is treatment minus control.
    """
    results = metrics.copy()

    for column in [
        "control_ci_low_pct",
        "control_ci_high_pct",
        "treatment_ci_low_pct",
        "treatment_ci_high_pct",
        "difference_ci_low_pp",
        "difference_ci_high_pp",
        "z_statistic",
        "p_value",
    ]:
        results[column] = np.nan

    for index, row in results.iterrows():
        metric = row["metric"]
        eligibility_column = (
            "d1_eligible" if metric == "d1_retained" else "d7_eligible"
        )

        eligible = assignments.loc[
            assignments[eligibility_column]
        ].copy()

        control = eligible.loc[eligible["experiment_arm"] == "control", metric]
        treatment = eligible.loc[
            eligible["experiment_arm"] == "treatment", metric
        ]

        if control.empty or treatment.empty:
            raise ValueError(
                f"Both experiment arms need eligible observations for {metric}."
            )

        control_summary = summarize_rate(
            label="control",
            successes=int(control.sum()),
            total=len(control),
        )
        treatment_summary = summarize_rate(
            label="treatment",
            successes=int(treatment.sum()),
            total=len(treatment),
        )

        comparison = compare_groups(
            df=eligible,
            metric=metric,
            group_column="experiment_arm",
            group_a="treatment",
            group_b="control",
        )

        results.loc[index, "control_ci_low_pct"] = (
            control_summary["ci_95_low_pct"]
        )
        results.loc[index, "control_ci_high_pct"] = (
            control_summary["ci_95_high_pct"]
        )
        results.loc[index, "treatment_ci_low_pct"] = (
            treatment_summary["ci_95_low_pct"]
        )
        results.loc[index, "treatment_ci_high_pct"] = (
            treatment_summary["ci_95_high_pct"]
        )
        results.loc[index, "difference_ci_low_pp"] = (
            comparison["ci_low"] * 100
        )
        results.loc[index, "difference_ci_high_pp"] = (
            comparison["ci_high"] * 100
        )
        results.loc[index, "z_statistic"] = comparison["z_stat"]
        results.loc[index, "p_value"] = comparison["p_value"]

    results["outcome_alpha"] = OUTCOME_ALPHA
    results["statistically_significant"] = (
        results["p_value"] < OUTCOME_ALPHA
    )

    return results


def build_report(
    assignments: pd.DataFrame,
    metrics: pd.DataFrame,
    srm: dict,
) -> str:
    """Build a Markdown report with uncertainty and limitations."""
    lines = [
        "# Idle Loop Observatory — Experiment Readiness Report",
        "",
        "> **Synthetic demonstration only.** These assignments and outcomes",
        "> do not represent a real experiment or evidence about Kolibri Games.",
        "",
        "## Experiment setup",
        "",
        f"- Experiment ID: `{EXPERIMENT_ID}`",
        f"- Assignment seed: `{RANDOM_SEED}`",
        f"- Players assigned: {len(assignments)}",
        f"- Control: {srm['control_count']}",
        f"- Treatment: {srm['treatment_count']}",
        f"- Expected control share: {EXPECTED_CONTROL_SHARE:.0%}",
        f"- SRM significance threshold: {SRM_ALPHA}",
        f"- Outcome-test significance threshold: {OUTCOME_ALPHA}",
        "",
        "## Sample-ratio mismatch check",
        "",
        f"- Chi-square statistic: {srm['chi_square_statistic']:.4f}",
        f"- p-value: {srm['p_value']:.6f}",
        f"- SRM flag: **{srm['srm_flag']}**",
        "",
        "The SRM check assesses whether assignment counts are consistent with",
        "the expected allocation. It does not prove that randomization,",
        "instrumentation, or the experiment design is valid.",
        "",
        "## Retention outcomes",
        "",
        "All differences are treatment minus control, in percentage points.",
        "Rate intervals are Wilson 95% confidence intervals; difference",
        "intervals are Newcombe 95% confidence intervals.",
        "",
        "| Metric | Control rate (95% CI) | Treatment rate (95% CI) | Lift (pp) | Difference 95% CI (pp) | z | p-value |",
        "|---|---|---|---:|---|---:|---:|",
    ]

    for row in metrics.to_dict(orient="records"):
        lines.append(
            f"| {row['metric']} "
            f"| {row['control_rate_pct']:.2f}% "
            f"({row['control_ci_low_pct']:.2f}–"
            f"{row['control_ci_high_pct']:.2f}%) "
            f"| {row['treatment_rate_pct']:.2f}% "
            f"({row['treatment_ci_low_pct']:.2f}–"
            f"{row['treatment_ci_high_pct']:.2f}%) "
            f"| {row['absolute_lift_pp']:+.2f} "
            f"| [{row['difference_ci_low_pp']:+.2f}, "
            f"{row['difference_ci_high_pp']:+.2f}] "
            f"| {row['z_statistic']:.3f} "
            f"| {row['p_value']:.4f} |"
        )

    lines.extend(
        [
            "",
            "## Statistical interpretation",
            "",
        ]
    )

    for row in metrics.to_dict(orient="records"):
        includes_zero = (
            row["difference_ci_low_pp"] <= 0
            <= row["difference_ci_high_pp"]
        )
        significant = bool(row["statistically_significant"])

        if significant and not includes_zero:
            interpretation = (
                "The two-sided test rejects equal rates at the configured "
                "5% significance level; inspect the interval and assumptions."
            )
        else:
            interpretation = (
                "The two-sided test does not reject equal rates at the "
                "configured 5% significance level."
            )

        lines.append(
            f"- **{row['metric']}:** {interpretation} "
            f"The 95% difference interval "
            f"{'includes' if includes_zero else 'excludes'} zero."
        )

    lines.extend(
        [
            "",
            "## Limitations",
            "",
            "- D1 retention is the illustrative primary metric; D7 is a guardrail.",
            "- Each metric includes only players eligible for that observation window.",
            "- Assignments are synthetic and outcomes come from a pre-existing fixture.",
            "- No treatment effect was simulated; observed differences are not causal effects.",
            "- A p-value is not the probability that the null hypothesis is true.",
            "- Statistical significance alone does not establish product importance.",
            "- No product decision should be made from this report.",
            "",
            "## Provenance",
            "",
            "- Source: `data/processed/synthetic_player_cohort.csv`",
            "- Assignment: `synthetic_random_assignment`",
            "- Analysis: `synthetic_development_fixture`",
        ]
    )

    return "\n".join(lines) + "\n"


def run_analysis() -> tuple[pd.DataFrame, pd.DataFrame, dict, str]:
    """Run assignment, quality checks, and statistical summaries."""
    cohort = load_cohort()
    assignments = assign_synthetic_arms(cohort)

    control_count = int((assignments["experiment_arm"] == "control").sum())
    treatment_count = int((assignments["experiment_arm"] == "treatment").sum())

    srm = check_sample_ratio(
        control_count=control_count,
        treatment_count=treatment_count,
        expected_control_share=EXPECTED_CONTROL_SHARE,
        alpha=SRM_ALPHA,
    )
    srm["experiment_id"] = EXPERIMENT_ID
    srm["data_provenance"] = "synthetic_development_fixture"

    base_metrics = summarize_binary_metrics(
        assignments,
        assignment_column="experiment_arm",
        control_label="control",
        treatment_label="treatment",
        metrics=["d1_retained", "d7_retained"],
    )

    metrics = calculate_statistical_results(assignments, base_metrics)
    report = build_report(assignments, metrics, srm)

    return assignments, metrics, srm, report


def main() -> None:
    """Write experiment assignments, statistics, and the report."""
    assignments, metrics, srm, report = run_analysis()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    assignments.to_csv(ASSIGNMENT_OUTPUT, index=False)
    metrics.to_csv(METRICS_OUTPUT, index=False)
    SRM_OUTPUT.write_text(json.dumps(srm, indent=2), encoding="utf-8")
    REPORT_OUTPUT.write_text(report, encoding="utf-8")

    print("=" * 72)
    print("IDLE LOOP OBSERVATORY — EXPERIMENT READINESS")
    print("SYNTHETIC DATA ONLY — NO CAUSAL PRODUCT CLAIMS")
    print("=" * 72)
    print(f"Players assigned: {len(assignments):,}")
    print(f"Control: {srm['control_count']:,}")
    print(f"Treatment: {srm['treatment_count']:,}")
    print(f"SRM p-value: {srm['p_value']:.6f}")
    print(f"SRM flag: {srm['srm_flag']}")
    print("\nStatistical results:")
    print(metrics.to_string(index=False))
    print("\nSaved outputs:")
    for path in [
        ASSIGNMENT_OUTPUT,
        METRICS_OUTPUT,
        SRM_OUTPUT,
        REPORT_OUTPUT,
    ]:
        print(f"- {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
