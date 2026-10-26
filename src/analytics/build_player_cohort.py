
"""Build a player-level retention cohort from synthetic game events.

All generated outputs are synthetic development data. They are not evidence
about real players or Kolibri Games.
"""

from pathlib import Path

import duckdb
import pandas as pd

from src.analytics.experiment_quality import filter_mature_players


ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = ROOT / "data" / "synthetic" / "idle_game_events.csv"
OUTPUT_DIR = ROOT / "data" / "processed"
OUTPUT_PATH = OUTPUT_DIR / "synthetic_player_cohort.csv"

ANALYSIS_CUTOFF_UTC = pd.Timestamp("2026-10-26T12:00:00Z")
PROCESSING_DELAY_HOURS = 0


def load_player_cohort() -> pd.DataFrame:
    """Aggregate event-level data to one row per installed player."""
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Synthetic event data not found: {INPUT_PATH}"
        )

    query = """
    WITH events AS (
        SELECT
            *,
            TRY_CAST(event_timestamp_utc AS TIMESTAMPTZ) AS event_ts,
            TRY_CAST(days_since_install AS INTEGER) AS activity_day
        FROM read_csv_auto(?)
    ),

    installs AS (
        SELECT
            player_id,
            MIN(event_ts) AS install_timestamp_utc,
            MAX(acquisition_channel) AS acquisition_channel,
            MAX(platform) AS platform
        FROM events
        WHERE event_name = 'install'
        GROUP BY player_id
    ),

    tutorial AS (
        SELECT
            player_id,
            MAX(
                CASE
                    WHEN event_name = 'tutorial_complete'
                     AND activity_day = 0
                    THEN 1
                    ELSE 0
                END
            ) AS tutorial_completed_d0
        FROM events
        GROUP BY player_id
    ),

    retention AS (
        SELECT
            player_id,
            MAX(
                CASE
                    WHEN event_name = 'session_start'
                     AND activity_day = 1
                    THEN 1
                    ELSE 0
                END
            ) AS d1_retained,
            MAX(
                CASE
                    WHEN event_name = 'session_start'
                     AND activity_day = 7
                    THEN 1
                    ELSE 0
                END
            ) AS d7_retained
        FROM events
        GROUP BY player_id
    )

    SELECT
        i.player_id,
        CAST(i.install_timestamp_utc AS VARCHAR) AS install_timestamp_utc,
        i.acquisition_channel,
        i.platform,
        COALESCE(t.tutorial_completed_d0, 0) AS tutorial_completed_d0,
        COALESCE(r.d1_retained, 0) AS d1_retained,
        COALESCE(r.d7_retained, 0) AS d7_retained
    FROM installs AS i
    LEFT JOIN tutorial AS t USING (player_id)
    LEFT JOIN retention AS r USING (player_id)
    ORDER BY i.player_id
    """

    with duckdb.connect() as conn:
        result = conn.execute(query, [str(INPUT_PATH)])
        columns = [column[0] for column in result.description]
        rows = result.fetchall()

    df = pd.DataFrame(rows, columns=columns)

    if df.empty:
        raise ValueError("No installed players were found in the event log.")

    if df["player_id"].duplicated().any():
        raise ValueError("Cohort output must contain one row per player.")

    df["install_timestamp_utc"] = pd.to_datetime(
        df["install_timestamp_utc"],
        utc=True,
        errors="coerce",
    )

    if df["install_timestamp_utc"].isna().any():
        raise ValueError("Some players have invalid installation timestamps.")

    return df


def build_cohort() -> pd.DataFrame:
    """Add observation-window eligibility and provenance fields."""
    players = load_player_cohort()

    d1_eligible = filter_mature_players(
        players,
        observation_day=1,
        cutoff_timestamp=ANALYSIS_CUTOFF_UTC,
        processing_delay_hours=PROCESSING_DELAY_HOURS,
    )

    d7_eligible = filter_mature_players(
        players,
        observation_day=7,
        cutoff_timestamp=ANALYSIS_CUTOFF_UTC,
        processing_delay_hours=PROCESSING_DELAY_HOURS,
    )

    players["d1_eligible"] = players["player_id"].isin(
        d1_eligible["player_id"]
    )
    players["d7_eligible"] = players["player_id"].isin(
        d7_eligible["player_id"]
    )

    # An immature outcome is unknown, not a retention failure.
    players.loc[~players["d1_eligible"], "d1_retained"] = pd.NA
    players.loc[~players["d7_eligible"], "d7_retained"] = pd.NA

    players["analysis_cutoff_utc"] = ANALYSIS_CUTOFF_UTC.isoformat()
    players["data_provenance"] = "synthetic_development_fixture"
    players["is_synthetic"] = True

    return players


def main() -> None:
    """Build and save the player cohort with a quality summary."""
    cohort = build_cohort()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    cohort.to_csv(OUTPUT_PATH, index=False)

    print("=" * 72)
    print("IDLE LOOP OBSERVATORY — PLAYER COHORT BUILD")
    print("SYNTHETIC DATA ONLY — NOT REAL PLAYER EVIDENCE")
    print("=" * 72)
    print(f"Analysis cutoff (UTC): {ANALYSIS_CUTOFF_UTC}")
    print(f"Installed players: {len(cohort):,}")
    print(f"D1 eligible: {int(cohort['d1_eligible'].sum()):,}")
    print(f"D7 eligible: {int(cohort['d7_eligible'].sum()):,}")
    print(f"Unique player IDs: {cohort['player_id'].nunique():,}")
    print(f"Output: {OUTPUT_PATH.relative_to(ROOT)}")

    print("\nRetention rates among eligible players:")

    for metric, eligibility in [
        ("d1_retained", "d1_eligible"),
        ("d7_retained", "d7_eligible"),
    ]:
        values = cohort.loc[cohort[eligibility], metric].dropna()

        if values.empty:
            print(f"{metric}: no eligible players")
        else:
            successes = int(values.sum())
            total = len(values)
            rate = values.mean() * 100

            print(f"{metric}: {rate:.2f}% ({successes}/{total})")


if __name__ == "__main__":
    main()
