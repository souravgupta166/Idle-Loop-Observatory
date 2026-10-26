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
),

summary AS (
  SELECT
    platform,
    COUNT(*) AS n,
    SUM(d1) AS d1_users,
    SUM(d7) AS d7_users
  FROM player_retention
  GROUP BY GROUPING SETS ((platform), ())
),

rates AS (
  SELECT
    *,
    SAFE_DIVIDE(d1_users, n) AS p1,
    SAFE_DIVIDE(d7_users, n) AS p7,
    1.96 AS z
  FROM summary
),

intervals AS (
  SELECT
    *,
    SAFE_DIVIDE(
      p1 + POW(z, 2) / (2 * n),
      1 + POW(z, 2) / n
    ) AS d1_center,
    SAFE_DIVIDE(
      z * SQRT(
        SAFE_DIVIDE(p1 * (1 - p1), n)
        + SAFE_DIVIDE(POW(z, 2), 4 * POW(n, 2))
      ),
      1 + POW(z, 2) / n
    ) AS d1_half,
    SAFE_DIVIDE(
      p7 + POW(z, 2) / (2 * n),
      1 + POW(z, 2) / n
    ) AS d7_center,
    SAFE_DIVIDE(
      z * SQRT(
        SAFE_DIVIDE(p7 * (1 - p7), n)
        + SAFE_DIVIDE(POW(z, 2), 4 * POW(n, 2))
      ),
      1 + POW(z, 2) / n
    ) AS d7_half
  FROM rates
)

SELECT
  COALESCE(platform, 'ALL_PLATFORMS') AS platform,
  n AS cohort_users,
  d1_users,
  ROUND(100 * p1, 2) AS d1_retention_pct,
  ROUND(100 * (d1_center - d1_half), 2) AS d1_ci_lower_pct,
  ROUND(100 * (d1_center + d1_half), 2) AS d1_ci_upper_pct,
  d7_users,
  ROUND(100 * p7, 2) AS d7_retention_pct,
  ROUND(100 * (d7_center - d7_half), 2) AS d7_ci_lower_pct,
  ROUND(100 * (d7_center + d7_half), 2) AS d7_ci_upper_pct
FROM intervals
ORDER BY
  CASE WHEN platform IS NULL THEN 0 ELSE 1 END,
  platform;