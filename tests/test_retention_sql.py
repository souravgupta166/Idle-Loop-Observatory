from pathlib import Path

import duckdb
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "synthetic" / "idle_game_events.csv"
SQL_PATH = ROOT / "sql" / "investigations" / "003_retention_by_day.sql"


def get_retention_results():
    sql = SQL_PATH.read_text(encoding="utf-8-sig")
    sql = sql.replace(
        "data/synthetic/idle_game_events.csv",
        DATA_PATH.as_posix(),
    )
    with duckdb.connect() as conn:
        return conn.execute(sql).df()


def test_retention_has_expected_day_range():
    result = get_retention_results()

    assert result["day_number"].tolist() == list(range(14))


def test_cohort_size_is_consistent():
    result = get_retention_results()

    with duckdb.connect() as conn:
        players = conn.execute(
            """
            SELECT COUNT(DISTINCT player_id)
            FROM read_csv_auto(?)
            WHERE event_name = 'install'
            """,
            [str(DATA_PATH)],
        ).fetchone()[0]

    assert (result["cohort_size"] == players).all()


def test_day_zero_retention_is_100_percent():
    result = get_retention_results()
    day_zero = result.loc[result["day_number"] == 0].iloc[0]

    assert day_zero["retained_players"] == day_zero["cohort_size"]
    assert day_zero["retention_pct"] == 100.0


def test_retention_matches_raw_session_events():
    result = get_retention_results()

    with duckdb.connect() as conn:
        raw = conn.execute(
            """
            SELECT
                CAST(days_since_install AS INTEGER) AS day_number,
                COUNT(DISTINCT player_id) AS actual_players
            FROM read_csv_auto(?)
            WHERE event_name = 'session_start'
            GROUP BY 1
            """,
            [str(DATA_PATH)],
        ).df()

    checked = result.merge(raw, on="day_number", how="left")
    checked["actual_players"] = checked["actual_players"].fillna(0)

    assert (
        checked["retained_players"] == checked["actual_players"]
    ).all()


def test_retention_values_are_valid():
    result = get_retention_results()

    assert result["retained_players"].between(
        0, result["cohort_size"]
    ).all()

    expected_pct = (
        100 * result["retained_players"] / result["cohort_size"]
    ).round(2)

    pd.testing.assert_series_equal(
        result["retention_pct"].reset_index(drop=True),
        expected_pct.reset_index(drop=True),
        check_names=False,
    )
