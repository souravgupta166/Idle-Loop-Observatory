-- Idle Loop Observatory
-- Investigation 003: Relative-day player retention
-- Dataset: Synthetic development fixture only.
--
-- Definition:
-- A player is retained on day N if they have a session_start
-- event on day N after installation.
--
-- Denominator:
-- All distinct players with an installation event.
--
-- This is a validation model, not a real-world game benchmark.

WITH events AS (
    SELECT *
    FROM read_csv_auto(
        'data/synthetic/idle_game_events.csv',
        header = true
    )
),

install_cohort AS (
    SELECT
        player_id,
        MIN(TRY_CAST(event_timestamp_utc AS TIMESTAMPTZ)) AS install_ts
    FROM events
    WHERE event_name = 'install'
    GROUP BY player_id
),

active_days AS (
    SELECT DISTINCT
        player_id,
        TRY_CAST(days_since_install AS INTEGER) AS activity_day
    FROM events
    WHERE event_name = 'session_start'
),

retention_by_day AS (
    SELECT
        d.day_number,
        COUNT(DISTINCT i.player_id) AS cohort_size,
        COUNT(DISTINCT a.player_id) AS retained_players
    FROM range(0, 14) AS d(day_number)
    CROSS JOIN install_cohort AS i
    LEFT JOIN active_days AS a
        ON a.player_id = i.player_id
       AND a.activity_day = d.day_number
    GROUP BY d.day_number
)

SELECT
    day_number,
    cohort_size,
    retained_players,
    ROUND(
        100.0 * retained_players / NULLIF(cohort_size, 0),
        2
    ) AS retention_pct
FROM retention_by_day
ORDER BY day_number;
