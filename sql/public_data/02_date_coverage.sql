SELECT
  MIN(table_name) AS first_daily_table,
  MAX(table_name) AS last_daily_table,
  COUNT(*) AS daily_table_count
FROM
  `firebase-public-project.analytics_153293282.INFORMATION_SCHEMA.TABLES`
WHERE
  REGEXP_CONTAINS(table_name, r'^events_[0-9]{8}$');