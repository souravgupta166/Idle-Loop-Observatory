WITH events AS (
  SELECT
    PARSE_DATE('%Y%m%d', event_date) AS event_day,
    event_timestamp,
    event_name,
    user_pseudo_id,
    platform
  FROM
    `firebase-public-project.analytics_153293282.events_*`
  WHERE
    _TABLE_SUFFIX BETWEEN '20180612' AND '20181003'
    AND user_pseudo_id IS NOT NULL
    AND event_name IN ('first_open', 'session_start')
),

first_opens AS (
  SELECT
    user_pseudo_id,
    ARRAY_AGG(
      platform ORDER BY event_timestamp LIMIT 1
    )[OFFSET(0)] AS platform,
    MIN(event_day) AS cohort_date
  FROM events
  WHERE event_name = 'first_open'
  GROUP BY user_pseudo_id
),

sessions AS (
  SELECT DISTINCT
    user_pseudo_id,
    event_day AS session_date
  FROM events
  WHERE event_name = 'session_start'
),

player_retention AS (
  SELECT
    f.user_pseudo_id,
    f.platform,
    f.cohort_date,
    MAX(IF(
      s.session_date = DATE_ADD(f.cohort_date, INTERVAL 1 DAY),
      1, 0
    )) AS d1,
    MAX(IF(
      s.session_date = DATE_ADD(f.cohort_date, INTERVAL 7 DAY),
      1, 0
    )) AS d7
  FROM first_opens f
  LEFT JOIN sessions s
    ON s.user_pseudo_id = f.user_pseudo_id
    AND s.session_date IN (
      DATE_ADD(f.cohort_date, INTERVAL 1 DAY),
      DATE_ADD(f.cohort_date, INTERVAL 7 DAY)
    )
  WHERE f.cohort_date <= DATE '2018-09-26'
  GROUP BY f.user_pseudo_id, f.platform, f.cohort_date
)

SELECT
  cohort_date,
  platform,
  COUNT(*) AS cohort_users,
  SUM(d1) AS d1_retained_users,
  ROUND(100 * SAFE_DIVIDE(SUM(d1), COUNT(*)), 2)
    AS d1_retention_pct,
  SUM(d7) AS d7_retained_users,
  ROUND(100 * SAFE_DIVIDE(SUM(d7), COUNT(*)), 2)
    AS d7_retention_pct
FROM player_retention
GROUP BY cohort_date, platform
ORDER BY cohort_date, platform;