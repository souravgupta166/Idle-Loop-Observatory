
"""Validate exported BigQuery results for the public Flood-It! analysis.

This script checks export presence, expected schemas, duplicate rows,
data-quality indicators, and retention arithmetic. It does not re-query
BigQuery or claim that this dataset represents idle-game behavior.
"""

from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "external" / "flood_it"
REPORT_DIR = ROOT / "reports" / "public_data"

FILES = {
    "schema": "01_schema_inspection.csv",
    "coverage": "02_date_coverage.csv",
    "quality": "03_event_quality_by_day.csv",
    "daily_retention": "04_daily_retention.csv",
    "summary": "05_retention_summary.csv",
}

EXPECTED_COLUMNS = {
    "schema": {"column_name", "data_type"},
    "coverage": {
        "first_daily_table",
        "last_daily_table",
        "daily_table_count",
    },
    "quality": {
        "event_date",
        "platform",
        "event_name",
        "event_count",
        "unique_users",
        "events_missing_user_id",
    },
    "daily_retention": {
        "cohort_date",
        "platform",
        "cohort_users",
        "d1_retained_users",
        "d1_retention_pct",
        "d7_retained_users",
        "d7_retention_pct",
    },
    "summary": {
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
    },
}

errors = []
warnings = []
frames = {}


def check(condition, message):
    """Record a failed validation check."""
    if not condition:
        errors.append(message)


def load_csv(key):
    """Load one expected CSV export and check its columns."""
    path = DATA_DIR / FILES[key]

    if not path.exists():
        errors.append(f"Missing export: {path}")
        return None

    try:
        df = pd.read_csv(path, encoding="utf-8-sig")
    except Exception as exc:
        errors.append(f"Could not read {path.name}: {exc}")
        return None

    df.columns = df.columns.str.strip()

    missing = EXPECTED_COLUMNS[key] - set(df.columns)
    if missing:
        errors.append(
            f"{path.name}: missing expected columns "
            f"{sorted(missing)}"
        )
        return None

    print(f"[OK] {path.name}: {len(df):,} rows")
    return df


def numeric_columns(df, columns, filename):
    """Convert required numeric columns or record an error."""
    for column in columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")
        check(
            df[column].notna().all(),
            f"{filename}: invalid numeric values in {column}",
        )


def validate_schema(df):
    names = set(df["column_name"].astype(str))
    required = {
        "event_date",
        "event_timestamp",
        "event_name",
        "user_pseudo_id",
        "platform",
    }
    check(
        required.issubset(names),
        "Schema export does not contain all required fields: "
        f"{sorted(required - names)}",
    )


def validate_coverage(df):
    row = df.iloc[0]
    numeric_columns(
        df,
        ["daily_table_count"],
        FILES["coverage"],
    )
    if pd.notna(row["daily_table_count"]):
        check(
            int(row["daily_table_count"]) > 0,
            "Date coverage reports no daily tables",
        )
        print(
            "  Table coverage: "
            f"{row['first_daily_table']} to "
            f"{row['last_daily_table']} "
            f"({int(row['daily_table_count'])} tables)"
        )


def validate_quality(df):
    numeric_columns(
        df,
        [
            "event_count",
            "unique_users",
            "events_missing_user_id",
        ],
        FILES["quality"],
    )

    check((df["event_count"] >= 0).all(), "Negative event count")
    check(
        (df["unique_users"] >= 0).all(),
        "Negative unique-user count",
    )
    check(
        (df["events_missing_user_id"] >= 0).all(),
        "Negative missing-ID count",
    )
    check(
        (df["events_missing_user_id"] <= df["event_count"]).all(),
        "Missing-ID count exceeds event count",
    )

    keys = ["event_date", "platform", "event_name"]
    check(
        not df.duplicated(keys).any(),
        "Event-quality export has duplicate date/platform/event rows",
    )

    if (df["events_missing_user_id"] > 0).any():
        warnings.append(
            "Some selected events have missing user identifiers."
        )
    else:
        print("  No missing user IDs in selected event rows.")


def validate_retention(df):
    numeric = [
        "cohort_users",
        "d1_retained_users",
        "d1_retention_pct",
        "d7_retained_users",
        "d7_retention_pct",
    ]
    numeric_columns(df, numeric, FILES["daily_retention"])

    check(
        not df.duplicated(["cohort_date", "platform"]).any(),
        "Daily retention has duplicate cohort-date/platform rows",
    )
    check(
        (df["cohort_users"] > 0).all(),
        "Daily retention contains an empty or invalid cohort",
    )

    for day in ["d1", "d7"]:
        users = df[f"{day}_retained_users"]
        pct = df[f"{day}_retention_pct"]
        n = df["cohort_users"]

        check(
            ((users >= 0) & (users <= n)).all(),
            f"{day.upper()}: retained counts outside cohort bounds",
        )

        expected = (100 * users / n).round(2)
        check(
            (expected.sub(pct).abs() <= 0.02).all(),
            f"{day.upper()}: percentages do not match counts",
        )

    print(f"  Daily cohorts: {len(df):,}")


def validate_summary(df):
    numeric = [
        "cohort_users",
        "d1_users",
        "d1_retention_pct",
        "d1_ci_lower_pct",
        "d1_ci_upper_pct",
        "d7_users",
        "d7_retention_pct",
        "d7_ci_lower_pct",
        "d7_ci_upper_pct",
    ]
    numeric_columns(df, numeric, FILES["summary"])

    check(
        not df["platform"].duplicated().any(),
        "Summary has duplicate platform rows",
    )

    for day in ["d1", "d7"]:
        users = df[f"{day}_users"]
        rate = df[f"{day}_retention_pct"]
        lower = df[f"{day}_ci_lower_pct"]
        upper = df[f"{day}_ci_upper_pct"]
        n = df["cohort_users"]

        check(
            ((users >= 0) & (users <= n)).all(),
            f"Summary {day.upper()}: counts outside cohort bounds",
        )
        expected = (100 * users / n).round(2)
        check(
            (expected.sub(rate).abs() <= 0.02).all(),
            f"Summary {day.upper()}: rate does not match counts",
        )
        check(
            ((lower >= 0) & (upper <= 100) & (lower <= upper)).all(),
            f"Summary {day.upper()}: invalid confidence interval",
        )
        check(
            ((rate >= lower - 0.02) & (rate <= upper + 0.02)).all(),
            f"Summary {day.upper()}: rate outside confidence interval",
        )

    expected_platforms = {"ALL_PLATFORMS", "ANDROID", "IOS"}
    actual_platforms = set(df["platform"].astype(str).str.upper())
    check(
        expected_platforms.issubset(actual_platforms),
        "Summary is missing one or more expected platform rows",
    )

    print("\nPooled retention summary:")
    print(
        df[
            [
                "platform",
                "cohort_users",
                "d1_retention_pct",
                "d1_ci_lower_pct",
                "d1_ci_upper_pct",
                "d7_retention_pct",
                "d7_ci_lower_pct",
                "d7_ci_upper_pct",
            ]
        ].to_string(index=False)
    )

    # Check whether the platform counts reconcile with the overall row.
    lookup = {
        str(row["platform"]).upper(): row
        for _, row in df.iterrows()
    }
    if {"ALL_PLATFORMS", "ANDROID", "IOS"}.issubset(lookup):
        all_row = lookup["ALL_PLATFORMS"]
        android = lookup["ANDROID"]
        ios = lookup["IOS"]

        for column in ["cohort_users", "d1_users", "d7_users"]:
            check(
                int(all_row[column]) == int(android[column] + ios[column]),
                f"Overall {column} does not equal Android + iOS",
            )


def main():
    print("Flood-It! public export validation")
    print(f"Project root: {ROOT}")
    print(f"CSV directory: {DATA_DIR}\n")

    for key in FILES:
        frames[key] = load_csv(key)

    if any(frame is None for frame in frames.values()):
        print("\nValidation stopped: missing or invalid CSV exports.")
        sys.exit(1)

    check(len(frames["schema"]) > 0, "Schema export is empty")
    check(len(frames["coverage"]) == 1, "Coverage export must have one row")

    if len(frames["coverage"]) == 1:
        validate_coverage(frames["coverage"])

    validate_schema(frames["schema"])
    validate_quality(frames["quality"])
    validate_retention(frames["daily_retention"])
    validate_summary(frames["summary"])

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / "flood_it_validation_report.txt"

    report_lines = [
        "Flood-It! Public Export Validation",
        "==================================",
        "Dataset: firebase-public-project.analytics_153293282",
        "Purpose: validate exported event and retention data",
        "Limitations: historical Flood-It! data; not idle-game data",
        "",
        f"Files checked: {len(FILES)}",
        f"Errors: {len(errors)}",
        f"Warnings: {len(warnings)}",
        "",
        "Errors:",
        *(f"- {item}" for item in errors),
        "",
        "Warnings:",
        *(f"- {item}" for item in warnings),
    ]

    report_path.write_text(
        "\n".join(report_lines) + "\n",
        encoding="utf-8",
    )

    print(f"\nValidation report saved: {report_path}")

    if warnings:
        print("\nWarnings:")
        for item in warnings:
            print(f"  [WARN] {item}")

    if errors:
        print("\nValidation FAILED:")
        for item in errors:
            print(f"  [ERROR] {item}")
        sys.exit(1)

    print("\nValidation PASSED.")
    print("All five exports passed the configured checks.")


if __name__ == "__main__":
    main()
