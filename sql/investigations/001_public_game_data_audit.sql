-- Idle Loop Observatory
-- Investigation 001: Public game event data audit
-- Source: Google's public Flood-It! GA4 export
-- Purpose: Validate data coverage before defining retention metrics.

SELECT
    COUNT(*) AS event_rows,
    COUNT(DISTINCT user_pseudo_id) AS distinct_players,
    COUNT(DISTINCT event_date) AS observed_days,
    MIN(event_date) AS first_event_date,
    MAX(event_date) AS last_event_date,
    COUNTIF(user_pseudo_id IS NULL) AS events_without_player_id,
    COUNTIF(event_name IS NULL OR event_name = '') AS events_without_name,
    COUNT(DISTINCT event_name) AS distinct_event_names
FROM
    `firebase-public-project.analytics_153293282.events_*`;
