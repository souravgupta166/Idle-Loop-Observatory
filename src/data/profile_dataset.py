"""Profile a CSV or Parquet dataset without modifying the source."""

import argparse
from pathlib import Path

import pandas as pd


def profile_dataset(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    suffix = path.suffix.lower()

    if suffix == ".csv":
        df = pd.read_csv(path, low_memory=False)
    elif suffix in {".parquet", ".pq"}:
        df = pd.read_parquet(path)
    else:
        raise ValueError("Supported formats: CSV and Parquet")

    print("\n=== DATASET OVERVIEW ===")
    print(f"File: {path.resolve()}")
    print(f"Rows: {len(df):,}")
    print(f"Columns: {len(df.columns):,}")
    print(f"Exact duplicate rows: {df.duplicated().sum():,}")

    print("\n=== COLUMN PROFILE ===")
    report = pd.DataFrame({
        "column": df.columns,
        "dtype": [str(df[c].dtype) for c in df.columns],
        "missing_count": [int(df[c].isna().sum()) for c in df.columns],
        "missing_pct": [
            round(float(df[c].isna().mean() * 100), 2)
            for c in df.columns
        ],
        "distinct_values": [int(df[c].nunique(dropna=True)) for c in df.columns],
    })

    print(report.to_string(index=False))

    print("\n=== SAMPLE ROWS ===")
    print(df.head(5).to_string(index=False))

    print("\nNote: duplicates and missing values require investigation;")
    print("they should not automatically be deleted or imputed.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Profile a CSV or Parquet dataset."
    )
    parser.add_argument("path", type=Path, help="Path to the dataset")
    args = parser.parse_args()
    profile_dataset(args.path)


if __name__ == "__main__":
    main()
