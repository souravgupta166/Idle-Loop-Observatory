# Flood-It! Public Sample — Retention Analysis

## Scope and provenance

- Source: public Firebase/Google Analytics BigQuery export.
- Dataset: `firebase-public-project.analytics_153293282`.
- Game: Flood-It!; this is not an idle game or Kolibri Games data.
- Source table coverage: `events_20180612` to `events_20181003`.
- Cohort dates represented in the daily export: 2018-06-12 to 2018-09-26.
- Cohort definition: earliest observed `first_open` date per pseudonymous user ID.
- Retention event: `session_start` on the exact target day.
- D1 is activity on cohort date + 1 day; D7 is activity on cohort date + 7 days.
- Dates use the exported `event_date` field consistently.

## Pooled results

| Platform | Cohort users | D1 retained | D1 retention (95% CI) | D7 retained | D7 retention (95% CI) |
|---|---:|---:|---:|---:|---:|
| All platforms | 3,998 | 718 | 17.96% (16.80–19.18%) | 191 | 4.78% (4.16–5.48%) |
| ANDROID | 2,670 | 472 | 17.68% (16.28–19.17%) | 129 | 4.83% (4.08–5.71%) |
| IOS | 1,328 | 246 | 18.52% (16.53–20.70%) | 62 | 4.67% (3.66–5.94%) |

## Interpretation

- Overall D1 retention is 17.96% (718/3,998).
- Overall D7 retention is 4.78% (191/3,998).
- D1 and D7 are exact-day metrics, not cumulative activity through those days.
- Android minus iOS retention is -0.84 percentage points for D1 and +0.16 percentage points for D7.
- The confidence intervals overlap for both metrics. That observation alone is not a formal test of the platform difference.
- Small daily cohorts can produce volatile percentages; interpret daily trends cautiously.

## Limitations

- The dataset is historical and covers 2018.
- Flood-It! is not an idle game, so these results cannot be used as an idle-game benchmark.
- Public sample results do not describe Kolibri Games or its players.
- A missing session event does not necessarily prove that a person stopped playing; conclusions depend on instrumentation and identifier availability.
- Confidence intervals quantify sampling uncertainty under the chosen binomial model; they do not account for all data-quality or measurement bias.

## Generated artifacts

- D1 chart: `reports/public_data/flood_it_d1_retention.png`
- D7 chart: `reports/public_data/flood_it_d7_retention.png`
- Validation report: `reports/public_data/flood_it_validation_report.txt`

## Reproducibility

Run `src/analytics/analyze_flood_it_retention.py` from the project root using the project's Python environment. The script reads the exported CSVs and does not query BigQuery.
