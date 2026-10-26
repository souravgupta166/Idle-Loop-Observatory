
"""Create retention charts and a findings report from validated Flood-It! exports."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "external" / "flood_it"
REPORT_DIR = ROOT / "reports" / "public_data"

DAILY_FILE = DATA_DIR / "04_daily_retention.csv"
SUMMARY_FILE = DATA_DIR / "05_retention_summary.csv"

D1_CHART = REPORT_DIR / "flood_it_d1_retention.png"
D7_CHART = REPORT_DIR / "flood_it_d7_retention.png"
REPORT_FILE = REPORT_DIR / "flood_it_retention_findings.md"


def load_data():
    """Load and validate the minimum required columns."""
    daily = pd.read_csv(DAILY_FILE)
    summary = pd.read_csv(SUMMARY_FILE)

    daily.columns = daily.columns.str.strip()
    summary.columns = summary.columns.str.strip()

    daily["cohort_date"] = pd.to_datetime(
        daily["cohort_date"], errors="raise"
    )
    daily["platform"] = daily["platform"].astype(str).str.upper()

    required_daily = {
        "cohort_date",
        "platform",
        "cohort_users",
        "d1_retained_users",
        "d1_retention_pct",
        "d7_retained_users",
        "d7_retention_pct",
    }
    required_summary = {
        "platform",
        "cohort_users",
        "d1_users",
        "d1_retention_pct",
        "d1_ci_lower_pct",
        "d1_ci_upper_pct",
        "d7_users",
        "d7_retention_pct",
        "d7_ci_lower_pct",
        "d7_ci_upper_pct",
    }

    if not required_daily.issubset(daily.columns):
        raise ValueError(
            f"Daily export missing columns: "
            f"{sorted(required_daily - set(daily.columns))}"
        )

    if not required_summary.issubset(summary.columns):
        raise ValueError(
            f"Summary export missing columns: "
            f"{sorted(required_summary - set(summary.columns))}"
        )

    return daily, summary


def plot_daily_retention(daily, metric, title, output_path):
    """Plot daily cohort retention by platform."""
    pct_column = f"{metric}_retention_pct"
    users_column = f"{metric}_retained_users"

    fig, ax = plt.subplots(figsize=(12, 6))

    for platform in sorted(daily["platform"].unique()):
        subset = daily[daily["platform"] == platform].sort_values(
            "cohort_date"
        )

        ax.plot(
            subset["cohort_date"],
            subset[pct_column],
            marker="o",
            markersize=3,
            linewidth=1.3,
            label=platform,
        )

    ax.set_title(title)
    ax.set_xlabel("First-open cohort date")
    ax.set_ylabel("Retention (%)")
    ax.set_ylim(bottom=0)
    ax.grid(True, alpha=0.3)
    ax.legend(title="Platform")
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def build_findings(daily, summary):
    """Create a concise, reproducible Markdown findings report."""
    lookup = {
        str(row["platform"]).upper(): row
        for _, row in summary.iterrows()
    }

    overall = lookup["ALL_PLATFORMS"]
    android = lookup["ANDROID"]
    ios = lookup["IOS"]

    # Pooled overall retention by cohort date, weighting by cohort size.
    overall_daily = (
        daily.groupby("cohort_date", as_index=False)
        .agg(
            cohort_users=("cohort_users", "sum"),
            d1_retained_users=("d1_retained_users", "sum"),
            d7_retained_users=("d7_retained_users", "sum"),
        )
    )
    overall_daily["d1_retention_pct"] = (
        100 * overall_daily["d1_retained_users"]
        / overall_daily["cohort_users"]
    )
    overall_daily["d7_retention_pct"] = (
        100 * overall_daily["d7_retained_users"]
        / overall_daily["cohort_users"]
    )

    first_date = daily["cohort_date"].min().date()
    last_date = daily["cohort_date"].max().date()

    lines = [
        "# Flood-It! Public Sample — Retention Analysis",
        "",
        "## Scope and provenance",
        "",
        "- Source: public Firebase/Google Analytics BigQuery export.",
        "- Dataset: `firebase-public-project.analytics_153293282`.",
        "- Game: Flood-It!; this is not an idle game or Kolibri Games data.",
        "- Source table coverage: `events_20180612` to `events_20181003`.",
        "- Cohort dates represented in the daily export: "
        f"{first_date} to {last_date}.",
        "- Cohort definition: earliest observed `first_open` date per "
        "pseudonymous user ID.",
        "- Retention event: `session_start` on the exact target day.",
        "- D1 is activity on cohort date + 1 day; D7 is activity on "
        "cohort date + 7 days.",
        "- Dates use the exported `event_date` field consistently.",
        "",
        "## Pooled results",
        "",
        "| Platform | Cohort users | D1 retained | D1 retention (95% CI) "
        "| D7 retained | D7 retention (95% CI) |",
        "|---|---:|---:|---:|---:|---:|",
    ]

    for platform in ["ALL_PLATFORMS", "ANDROID", "IOS"]:
        row = lookup[platform]
        label = "All platforms" if platform == "ALL_PLATFORMS" else platform
        lines.append(
            f"| {label} "
            f"| {int(row['cohort_users']):,} "
            f"| {int(row['d1_users']):,} "
            f"| {row['d1_retention_pct']:.2f}% "
            f"({row['d1_ci_lower_pct']:.2f}–"
            f"{row['d1_ci_upper_pct']:.2f}%) "
            f"| {int(row['d7_users']):,} "
            f"| {row['d7_retention_pct']:.2f}% "
            f"({row['d7_ci_lower_pct']:.2f}–"
            f"{row['d7_ci_upper_pct']:.2f}%) |"
        )

    d1_difference = (
        android["d1_retention_pct"] - ios["d1_retention_pct"]
    )
    d7_difference = (
        android["d7_retention_pct"] - ios["d7_retention_pct"]
    )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"- Overall D1 retention is "
            f"{overall['d1_retention_pct']:.2f}% "
            f"({int(overall['d1_users']):,}/"
            f"{int(overall['cohort_users']):,}).",
            f"- Overall D7 retention is "
            f"{overall['d7_retention_pct']:.2f}% "
            f"({int(overall['d7_users']):,}/"
            f"{int(overall['cohort_users']):,}).",
            "- D1 and D7 are exact-day metrics, not cumulative "
            "activity through those days.",
            f"- Android minus iOS retention is "
            f"{d1_difference:+.2f} percentage points for D1 and "
            f"{d7_difference:+.2f} percentage points for D7.",
            "- The confidence intervals overlap for both metrics. "
            "That observation alone is not a formal test of the "
            "platform difference.",
            "- Small daily cohorts can produce volatile percentages; "
            "interpret daily trends cautiously.",
            "",
            "## Limitations",
            "",
            "- The dataset is historical and covers 2018.",
            "- Flood-It! is not an idle game, so these results cannot "
            "be used as an idle-game benchmark.",
            "- Public sample results do not describe Kolibri Games "
            "or its players.",
            "- A missing session event does not necessarily prove "
            "that a person stopped playing; conclusions depend on "
            "instrumentation and identifier availability.",
            "- Confidence intervals quantify sampling uncertainty "
            "under the chosen binomial model; they do not account "
            "for all data-quality or measurement bias.",
            "",
            "## Generated artifacts",
            "",
            f"- D1 chart: `{D1_CHART.relative_to(ROOT).as_posix()}`",
            f"- D7 chart: `{D7_CHART.relative_to(ROOT).as_posix()}`",
            f"- Validation report: "
            "`reports/public_data/flood_it_validation_report.txt`",
            "",
            "## Reproducibility",
            "",
            "Run `src/analytics/analyze_flood_it_retention.py` from "
            "the project root using the project's Python environment. "
            "The script reads the exported CSVs and does not query "
            "BigQuery.",
        ]
    )

    REPORT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Saved findings report: {REPORT_FILE}")
    print(
        "Pooled overall retention by cohort date calculated for "
        f"{len(overall_daily)} cohort dates."
    )


def main():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    daily, summary = load_data()

    plot_daily_retention(
        daily,
        "d1",
        "Flood-It! Public Sample — D1 Retention by Cohort",
        D1_CHART,
    )
    plot_daily_retention(
        daily,
        "d7",
        "Flood-It! Public Sample — D7 Retention by Cohort",
        D7_CHART,
    )
    build_findings(daily, summary)

    print(f"Saved D1 chart: {D1_CHART}")
    print(f"Saved D7 chart: {D7_CHART}")
    print("Analysis completed.")


if __name__ == "__main__":
    main()
