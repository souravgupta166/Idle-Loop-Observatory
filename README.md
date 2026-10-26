# Idle Loop Observatory
### Retention Analytics, Experiment Readiness & Statistical Quality Checks

**A reproducible game-data analytics project built with Python, SQL, DuckDB, pandas, and statistical methods.**

Idle Loop Observatory explores how a game data analyst can turn event-level telemetry into player cohorts, retention metrics, uncertainty estimates, and experiment-readiness checks.

The project combines two deliberately separate datasets:

1. **Public Firebase/Google Analytics sample:** historical event data from Flood-It!, used to validate event-processing and retention-analysis methods.
2. **Synthetic idle-game event data:** generated development data used to test local analytics pipelines, cohort construction, experiment assignment, and quality checks.

> **Important:** This repository does not contain Kolibri Games data. Flood-It! is not an idle game, and the synthetic data does not represent real players. The project demonstrates analytical methods and engineering practices, not conclusions about Kolibri Games or its products.

---

## Table of Contents

- [Project Objectives](#project-objectives)
- [Architecture](#architecture)
- [Data Sources and Provenance](#data-sources-and-provenance)
- [Public Dataset Analysis](#public-dataset-analysis)
- [Retention Metric Definitions](#retention-metric-definitions)
- [Statistical Methods](#statistical-methods)
- [Public Dataset Results](#public-dataset-results)
- [Synthetic Experiment Readiness](#synthetic-experiment-readiness)
- [Data Quality and Validation](#data-quality-and-validation)
- [Repository Structure](#repository-structure)
- [Setup and Reproduction](#setup-and-reproduction)
- [Limitations and Next Steps](#limitations-and-next-steps)

---

## Project Objectives

The project is designed to demonstrate practical skills relevant to game data analytics:

- Transform raw event telemetry into player-level and cohort-level datasets.
- Define retention metrics with explicit event and observation windows.
- Compare retention across platforms without confusing descriptive differences with statistical evidence.
- Quantify uncertainty around estimated retention rates.
- Check experiment assignment for sample-ratio mismatch (SRM).
- Apply eligibility and observation-maturity checks before evaluating player outcomes.
- Calculate experiment sample-size requirements for a hypothetical improvement.
- Validate exported datasets and document their provenance.
- Produce reproducible charts, SQL queries, reports, and automated tests.

## Architecture

The workflow separates data ingestion, validation, analytics, and reporting.

```text
Public Firebase / Google Analytics sample
                  |
                  v
       BigQuery SQL investigations
                  |
                  v
        CSV exports to local files
                  |
                  v
       Export validation and checks
                  |
                  v
        Retention calculations
                  |
                  v
     Charts + findings report


Synthetic idle-game event generator
                  |
                  v
       Synthetic event-level data
                  |
                  v
       Player cohort construction
                  |
                  v
    Experiment assignment and checks
                  |
                  v
    Retention uncertainty + readiness
```

The two data sources are kept separate so that synthetic results cannot accidentally be presented as real-world player findings.

---

## Data Sources and Provenance

### 1. Public Firebase/Google Analytics sample

**Source:** `firebase-public-project.analytics_153293282`

**Access:** Google BigQuery public dataset.

The project inspected the source schema, identified daily table coverage, examined event quality, and calculated D1/D7 retention using exported event dates.

| Property | Verified result |
|---|---|
| Game | Flood-It! |
| First daily table | `events_20180612` |
| Last daily table | `events_20181003` |
| Daily tables identified | 114 |
| Eligible cohort dates | 12 June 2018 – 26 September 2018 |
| Selected event-quality rows with missing pseudonymous user IDs | 0 |

The source data is historical and is not an idle-game dataset. It is used to exercise real event-data processing methods, not to establish idle-game benchmarks.

### 2. Synthetic idle-game dataset

The local generator creates a reproducible development fixture.

| Property | Value |
|---|---:|
| Synthetic players | 500 |
| Observation period | 14 days |
| Random seed | 42 |
| Generated event rows | 8,416 |

The generated events include installation, sessions, tutorial completion, upgrades, and offline reward claims.

Because this dataset is synthetic, its event frequencies, retention rates, and player behavior must not be interpreted as estimates of real users.

### Provenance rules

- Keep public and synthetic datasets separately labeled.
- Preserve the source and limitations of every analysis.
- Define metric numerators, denominators, and observation windows.
- Validate data quality before interpreting results.
- Do not make causal claims from outcomes that were not generated by a genuine randomized treatment effect.

---

## Public Dataset Analysis

Five BigQuery queries were developed and exported.

| Query | Purpose |
|---|---|
| `01_schema_inspection.sql` | Inspect the columns and data types of a daily event table. |
| `02_date_coverage.sql` | Identify the first and last daily tables and count available tables. |
| `03_event_quality_by_day.sql` | Aggregate selected events and check for missing user identifiers. |
| `04_daily_retention.sql` | Calculate D1/D7 retention by cohort date and platform. |
| `05_retention_summary.sql` | Calculate pooled platform results and confidence intervals. |

The five exports were checked locally by `src/data/validate_flood_it_exports.py`.

The export validation confirmed:

- All five expected CSV files were present and passed the configured checks.
- The source coverage query returned 114 daily tables.
- The selected event-quality export had no missing user IDs.
- The daily retention export contained 203 cohort-date/platform rows.
- The pooled platform counts and retention calculations reconciled under the configured validation rules.

The local analysis script reads these exports. It does not query BigQuery automatically.

---

## Retention Metric Definitions

### Cohort construction

A player enters a cohort on their earliest observed `first_open` date.

For the public dataset:

- Player identifier: `user_pseudo_id`.
- Cohort date: earliest observed `first_open` date.
- Platform: platform associated with the earliest observed event timestamp.
- Activity event: `session_start`.
- Date basis: exported `event_date`, used consistently throughout the calculation.

Cohorts after 26 September 2018 are excluded because seven days of follow-up are required for D7 retention and the available source data ends on 3 October 2018.

### Day 1 retention

A player is D1-retained if they have a `session_start` on the calendar day immediately following their cohort date.

\[
D1 = \frac{\text{Players with a session on cohort day + 1}}
{\text{Eligible cohort players}}
\]

### Day 7 retention

A player is D7-retained if they have a `session_start` exactly seven calendar days after their cohort date.

\[
D7 = \frac{\text{Players with a session on cohort day + 7}}
{\text{Eligible cohort players}}
\]

These are **exact-day retention metrics**, not rolling or cumulative retention. A player active on day 6 but not day 7 does not count as D7-retained.

### Platform aggregation

For pooled platform retention, player counts are aggregated before calculating the rate:

\[
\text{Retention rate} =
\frac{\sum \text{retained players}}
{\sum \text{cohort players}}
\]

This avoids taking an unweighted average of daily percentages, which could give a small cohort the same influence as a large cohort.

---

## Statistical Methods

### 1. Wilson confidence interval for a retention rate

Retention is modeled as a binary outcome: a player either satisfies the specified retention definition or does not.

A normal-approximation interval can behave poorly when proportions are low or sample sizes are limited. The project therefore uses the **Wilson score interval** for the pooled public retention estimates.

Let:

- \(n\) = eligible cohort size.
- \(x\) = number of retained players.
- \(\hat p = x/n\) = observed retention rate.
- \(z = 1.96\) for a nominal 95% interval.

The Wilson interval is:

\[
\frac{
\hat p + \frac{z^2}{2n}
\ \pm
z\sqrt{\frac{\hat p(1-\hat p)}{n}+\frac{z^2}{4n^2}}
}{
1+\frac{z^2}{n}
}
\]

The result is bounded between 0 and 1 and is generally more reliable than a simple symmetric normal interval for binomial proportions.

These intervals quantify sampling uncertainty under the binomial model. They do not automatically account for instrumentation errors, selection bias, or other measurement problems.

### 2. Comparing two retention rates

The experiment analytics module compares two groups using a two-proportion z-test and a Newcombe confidence interval for the difference in proportions.

The reported difference is:

\[
\Delta = \hat p_A - \hat p_B
\]

The sign depends on group order. The experiment-readiness report uses treatment minus control.

The null hypothesis for the two-sided test is:

\[
H_0: p_A = p_B
\]

The alternative is:

\[
H_1: p_A \ne p_B
\]

A p-value below the selected significance level provides evidence against the null hypothesis under the test assumptions. A non-significant result does not establish that the groups are equivalent.

The Newcombe interval provides an uncertainty range for the difference in proportions rather than relying only on overlapping individual confidence intervals.

### 3. Sample-size planning

The sample-size calculator uses a two-independent-proportion design through `statsmodels`.

The hypothetical design inputs are:

- Baseline conversion/retention: 30%.
- Target rate: 35%.
- Absolute minimum detectable effect: 5 percentage points.
- Two-sided significance level: 5%.
- Statistical power: 80%.

The resulting planning estimate is **1,376 players per arm, or 2,752 total**, under the specified calculator assumptions.

This is a hypothetical planning scenario, not a claim that the public Flood-It! retention rate is 30% or that an actual experiment achieved a 5-percentage-point lift. The design should be recalculated for the real metric, baseline, effect size, allocation ratio, and analysis plan.

### 4. Sample-ratio mismatch (SRM)

The experiment-quality module uses a chi-square goodness-of-fit test to compare observed assignment counts with expected counts.

For a two-arm experiment with an expected 50:50 split:

\[
E_C = N \times 0.5,\qquad E_T = N \times 0.5
\]

The Pearson chi-square statistic is:

\[
\chi^2 = \sum_i \frac{(O_i-E_i)^2}{E_i}
\]

where \(O_i\) and \(E_i\) represent observed and expected group counts.

The readiness workflow uses an SRM significance threshold of 0.001. This stricter threshold is used as a diagnostic for unexpected allocation imbalance; it is not a universal threshold for every experiment.

A passing SRM check does not prove that randomization, exposure logging, or outcome measurement is otherwise correct.

### 5. Observation maturity

Retention outcomes are only interpretable after players have had enough time to complete the specified observation window.

The experiment-quality module includes a maturity filter with configurable observation day and processing delay. This helps prevent players with incomplete follow-up from being incorrectly treated as non-retained.

The cutoff and delay should reflect the actual data pipeline and metric definition in a production experiment.

---

## Public Dataset Results

The validated pooled results are:

| Platform | Cohort users | D1 retained | D1 retention (95% CI) | D7 retained | D7 retention (95% CI) |
|---|---:|---:|---:|---:|---:|
| All platforms | 3,998 | 718 | 17.96% (16.80–19.18%) | 191 | 4.78% (4.16–5.48%) |
| Android | 2,670 | 472 | 17.68% (16.28–19.17%) | 129 | 4.83% (4.08–5.71%) |
| iOS | 1,328 | 246 | 18.52% (16.53–20.70%) | 62 | 4.67% (3.66–5.94%) |

### Interpretation

- Overall D1 retention is 17.96%, based on 718 of 3,998 cohort users.
- Overall D7 retention is 4.78%, based on 191 of 3,998 cohort users.
- The descriptive Android-minus-iOS difference is −0.84 percentage points for D1 and +0.16 percentage points for D7.
- The daily export contains 203 cohort-date/platform rows. The plotting script also calculates a pooled daily series across 102 cohort dates.
- Daily percentages may be volatile when cohorts are small.

The platform differences are descriptive. Overlap between individual confidence intervals is not a formal significance test, and this report does not claim that platform causes a retention difference.

### Generated reports

- `reports/public_data/flood_it_d1_retention.png`
- `reports/public_data/flood_it_d7_retention.png`
- `reports/public_data/flood_it_retention_findings.md`
- `reports/public_data/flood_it_validation_report.txt`

The charts visualize daily cohort retention by platform. The Markdown report records the pooled metrics, definitions, interpretation, and limitations.

---

## Synthetic Experiment Readiness

The local experiment workflow builds a player-level cohort dataset from the synthetic event log, generates reproducible experiment assignments, checks sample allocation, and compares binary retention outcomes.

The current run used a reproducible assignment seed of `20261026`.

### Assignment and SRM

| Group | Assigned players |
|---|---:|
| Control | 257 |
| Treatment | 243 |
| Total | 500 |

The SRM check returned a p-value of approximately 0.531, so the configured SRM test did not flag an allocation imbalance at the 0.001 threshold.

This is a check of assignment counts only. It does not establish that all experiment-quality requirements have been satisfied.

### Synthetic outcome comparison

| Metric | Control | Treatment | Treatment − control | p-value |
|---|---:|---:|---:|---:|
| D1 retention | 46.30% (119/257) | 46.91% (114/243) | +0.61 pp | 0.8913 |
| D7 retention | 28.79% (74/257) | 27.57% (67/243) | −1.22 pp | 0.7615 |

The corresponding 95% Newcombe intervals for treatment minus control were:

- D1: approximately −8.08 to +9.29 percentage points.
- D7: approximately −9.05 to +6.66 percentage points.

Neither comparison is statistically significant at a conventional 5% threshold. The intervals are wide and include zero.

**Crucial limitation:** the synthetic assignment was applied to pre-existing synthetic outcomes; a genuine treatment effect was not simulated. These numbers demonstrate the mechanics of an experiment-readiness workflow, not the causal impact of a product change.

### Synthetic output files

- `data/processed/synthetic_player_cohort.csv`
- `data/processed/synthetic_experiment_assignments.csv`
- `data/processed/synthetic_experiment_metrics.csv`
- `data/processed/synthetic_experiment_srm.json`
- `data/processed/synthetic_experiment_readiness.md`

These generated files are excluded from version control by `.gitignore`.

---

## Data Quality and Validation

The project uses checks at different stages rather than assuming that successful code execution means the data is correct.

### Public export validation

`src/data/validate_flood_it_exports.py` checks the expected exports, required columns, row counts and duplicates, retention arithmetic, confidence interval bounds, and reconciliation between platform and overall counts.

### Synthetic cohort construction

`src/analytics/build_player_cohort.py` builds one player-level row per installed synthetic player, calculates retention flags, and uses an analysis cutoff to mark whether observation windows are eligible.

Ineligible outcomes are represented as missing rather than being silently treated as non-retained.

### Experiment quality

`src/analytics/experiment_quality.py` provides functions for observation maturity, SRM, and binary metric summaries.

### Automated tests

Run the test suite with:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

The current development run passed **69 tests**. Re-run the suite after making changes to confirm that the current checkout remains valid.

---

## Repository Structure

```text
idle-loop-observatory/
├── data/
│   ├── external/flood_it/       # Downloaded CSV exports; Git-ignored
│   ├── processed/               # Generated outputs; Git-ignored
│   ├── raw/                     # Raw data; Git-ignored
│   └── synthetic/               # Synthetic development fixture
├── docs/
│   └── data_sources.yml          # Source metadata and provenance rules
├── reports/
│   └── public_data/              # Charts and Markdown findings
├── sql/
│   ├── investigations/           # Synthetic-data SQL investigations
│   └── public_data/               # BigQuery source queries
├── src/
│   ├── analytics/
│   │   ├── analyze_flood_it_retention.py
│   │   ├── build_player_cohort.py
│   │   ├── experiment_design.py
│   │   ├── experiment_quality.py
│   │   ├── retention_uncertainty.py
│   │   └── run_experiment_readiness.py
│   └── data/
│       ├── generate_synthetic_idle_events.py
│       ├── profile_dataset.py
│       └── validate_flood_it_exports.py
├── tests/
├── .gitignore
└── README.md
```

Some output directories may be empty until the relevant scripts have been run. Downloaded exports, generated data, and local databases are excluded from Git to avoid committing bulky or machine-specific artifacts.

---

## Setup and Reproduction

### Requirements

- Python with a compatible version for the installed project dependencies.
- Git.
- Google BigQuery access to run the public-data SQL queries.
- A local Python virtual environment.

### 1. Create and activate a virtual environment

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the project's dependencies from its dependency manifest if one is provided. If a dependency manifest has not yet been created, add one containing the packages required by the scripts before expecting a fresh environment to run them.

### 2. Generate the synthetic fixture

```powershell
.\.venv\Scripts\python.exe src\data\generate_synthetic_idle_events.py
```

This generates synthetic events for local pipeline testing.

### 3. Build the synthetic player cohort

```powershell
.\.venv\Scripts\python.exe src\analytics\build_player_cohort.py
```

### 4. Run experiment-readiness checks

```powershell
.\.venv\Scripts\python.exe src\analytics\run_experiment_readiness.py
```

### 5. Run the tests

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

### 6. Run the public-data queries

Execute the SQL files in `sql/public_data/` in BigQuery. Export the results to the following exact local filenames:

```text
data/external/flood_it/01_schema_inspection.csv
data/external/flood_it/02_date_coverage.csv
data/external/flood_it/03_event_quality_by_day.csv
data/external/flood_it/04_daily_retention.csv
data/external/flood_it/05_retention_summary.csv
```

The BigQuery queries require access to the public dataset. Running the local plotting script does not require a live BigQuery connection once the expected exports are available.

### 7. Validate the public exports

```powershell
.\.venv\Scripts\python.exe src\data\validate_flood_it_exports.py
```

### 8. Generate the retention charts and findings report

```powershell
.\.venv\Scripts\python.exe src\analytics\analyze_flood_it_retention.py
```

Inspect the generated artifacts:

```powershell
Get-ChildItem .\reports\public_data
Get-Content .\reports\public_data\flood_it_retention_findings.md -Encoding utf8
```

---

## Limitations and Next Steps

### Current limitations

- The public dataset is historical, covering 2018.
- Flood-It! is not an idle game.
- The public dataset does not represent Kolibri Games or its players.
- A missing session event does not necessarily prove that a player stopped playing.
- Retention results depend on instrumentation, identifiers, cohort construction, and observation windows.
- Confidence intervals do not account for every source of measurement or selection bias.
- Synthetic experiment outcomes are not evidence of a causal treatment effect.
- The local export workflow requires a separate BigQuery export step.

### Potential extensions

1. Add a dependency manifest and pin tested package versions for easier reproduction.
2. Add automated tests for the public-export validation and chart-generation modules.
3. Add explicit configuration for cohort dates, metric windows, and analysis cutoffs.
4. Add a formal platform-difference test to the public-data report if that comparison is needed.
5. Add an experiment-analysis workflow using simulated treatment effects and verify type-I error and power over repeated simulations.
6. Add sensitivity checks for event definitions, incomplete follow-up, and alternative retention windows.
7. Extend the pipeline with a clearly sourced idle-game dataset if one with suitable provenance and access becomes available.

---

## Summary

Idle Loop Observatory demonstrates a reproducible workflow for event-data quality checks, cohort construction, exact-day retention, confidence intervals, sample-size planning, sample-ratio mismatch detection, and experiment-readiness reporting.

Its central principle is that **good game analytics requires more than calculating a metric**: it requires clear definitions, correct denominators, uncertainty estimates, data-quality checks, reproducible code, and honest communication about what the data can—and cannot—support.
