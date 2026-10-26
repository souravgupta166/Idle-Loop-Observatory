SELECT
  event_date,
  platform,
  event_name,
  COUNT(*) AS event_count,
  COUNT(DISTINCT user_pseudo_id) AS unique_users,
  COUNTIF(user_pseudo_id IS NULL) AS events_missing_user_id
FROM
  `firebase-public-project.analytics_153293282.events_*`
WHERE
  _TABLE_SUFFIX BETWEEN '20180612' AND '20181003'
  AND event_name IN (
    'first_open',
    'session_start',
    'user_engagement'
  )
GROUP BY
  event_date,
  platform,
  event_name
ORDER BY
  event_date,
  platform,
  event_name;