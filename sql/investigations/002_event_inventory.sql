-- Investigation 002: Event inventory
-- Identify actual event names before defining product metrics.

SELECT
    event_name,
    COUNT(*) AS event_count,
    COUNT(DISTINCT user_pseudo_id) AS distinct_players,
    COUNTIF(user_pseudo_id IS NULL) AS events_without_player_id
FROM
    `firebase-public-project.analytics_153293282.events_*`
GROUP BY
    event_name
ORDER BY
    event_count DESC;
