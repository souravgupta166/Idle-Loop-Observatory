SELECT
  column_name,
  data_type
FROM
  `firebase-public-project.analytics_153293282.INFORMATION_SCHEMA.COLUMNS`
WHERE
  table_name = 'events_20180930'
ORDER BY
  ordinal_position;
