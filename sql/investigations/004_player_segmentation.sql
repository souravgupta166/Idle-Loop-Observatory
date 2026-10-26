-- Idle Loop Observatory
-- Investigation 004: Player segmentation and retention
-- DATA STATUS: SYNTHETIC DEVELOPMENT DATA ONLY
--
-- D1 and D7 mean activity exactly one or seven days
-- after installation, respectively.
--
-- Segment comparisons are observational, not causal.

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
        MIN(TRY_CAST(event_timestamp_utc AS TIMESTAMPTZ)) AS install_ts,
        MAX(acquisition_channel) AS acquisition_channel,
        MAX(platform) AS platform
    FROM events
    WHERE event_name = 'install'
    GROUP BY player_id
),

tutorial_status AS (
    SELECT
        player_id,
        MAX(
            CASE
                WHEN event_name = 'tutorial_complete'
                 AND TRY_CAST(days_since_install AS INTEGER) = 0
                THEN 1 ELSE 0
            END
        ) AS completed_tutorial_day0
    FROM events
    GROUP BY player_id
),

active_days AS (
    SELECT DISTINCT
        player_id,
        TRY_CAST(days_since_install AS INTEGER) AS activity_day
    FROM events
    WHERE event_name = 'session_start'
),

player_outcomes AS (
    SELECT
        i.player_id,
        i.acquisition_channel,
        i.platform,
        COALESCE(t.completed_tutorial_day0, 0) AS completed_tutorial_day0,
        MAX(CASE WHEN a.activity_day = 1 THEN 1 ELSE 0 END) AS retained_d1,
        MAX(CASE WHEN a.activity_day = 7 THEN 1 ELSE 0 END) AS retained_d7
    FROM install_cohort AS i
    LEFT JOIN tutorial_status AS t
        ON i.player_id = t.player_id
    LEFT JOIN active_days AS a
        ON i.player_id = a.player_id
    GROUP BY
        i.player_id,
        i.acquisition_channel,
        i.platform,
        t.completed_tutorial_day0
),

segment_memberships AS (
    SELECT
        player_id,
        'acquisition_channel' AS segment_type,
        acquisition_channel AS segment_value,
        retained_d1,
        retained_d7
    FROM player_outcomes

    UNION ALL

    SELECT
        player_id,
        'platform' AS segment_type,
        platform AS segment_value,
        retained_d1,
        retained_d7
    FROM player_outcomes

    UNION ALL

    SELECT
        player_id,
        'tutorial_completion_day0' AS segment_type,
        CASE
            WHEN completed_tutorial_day0 = 1 THEN 'completed'
            ELSE 'not_completed'
        END AS segment_value,
        retained_d1,
        retained_d7
    FROM player_outcomes
)

SELECT
    segment_type,
    segment_value,
    COUNT(*) AS players,
    SUM(retained_d1) AS d1_retained_players,
    ROUND(100.0 * AVG(retained_d1), 2) AS d1_retention_pct,
    SUM(retained_d7) AS d7_retained_players,
    ROUND(100.0 * AVG(retained_d7), 2) AS d7_retention_pct
FROM segment_memberships
GROUP BY segment_type, segment_value
ORDER BY segment_type, segment_value;
