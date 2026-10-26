# 🎮 Idle Loop Observatory
### A Game Analytics Command Center for Retention, Player Behaviour & Experiment Readiness

<p align="center">
  <a href="https://idle-loop-observatory-sggcmvrlqepybsy9xwrg2q.streamlit.app/">
    <img src="https://img.shields.io/badge/🚀_Launch-Live_Dashboard-00F5FF?style=for-the-badge" alt="Launch Live Dashboard">
  </a>
  <a href="https://github.com/souravgupta166/Idle-Loop-Observatory">
    <img src="https://img.shields.io/badge/GitHub-Source_Code-181717?style=for-the-badge&logo=github" alt="GitHub Repository">
  </a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-Analytics-3776AB?style=flat-square&logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/Streamlit-Interactive_UI-FF4B4B?style=flat-square&logo=streamlit&logoColor=white">
  <img src="https://img.shields.io/badge/SQL-Data_Analysis-4479A1?style=flat-square&logo=postgresql&logoColor=white">
  <img src="https://img.shields.io/badge/Plotly-Visualisation-3F4F75?style=flat-square&logo=plotly&logoColor=white">
  <img src="https://img.shields.io/badge/Testing-Pytest-0A9EDC?style=flat-square&logo=pytest&logoColor=white">
</p>

---

## 🚀 Explore the project

**Live dashboard:** https://idle-loop-observatory-sggcmvrlqepybsy9xwrg2q.streamlit.app/

**Source code:** https://github.com/souravgupta166/Idle-Loop-Observatory

Idle Loop Observatory is an interactive game analytics portfolio project built to explore how analysts can measure player retention, investigate behavioural patterns, assess experiment quality, and plan statistically informed game experiments.

The project combines SQL-based event analysis, Python analytics, uncertainty estimation, experiment-readiness checks, automated tests, and a dark, gaming-inspired Streamlit interface.

The objective is not simply to display metrics. It is to connect **raw events → trustworthy player-level metrics → statistical interpretation → better product decisions.**

> **Data transparency:** The public-data analysis uses the historical Firebase/Google Analytics Flood-It! sample from 2018. Flood-It! is not an idle game, and the dataset is not from Kolibri Games. Synthetic idle-game events are used separately for development and experiment-workflow demonstrations. Neither source establishes actual Kolibri Games player behaviour.

---

## 🕹️ What can you explore?

| Mission | What it does | Why it matters |
|---|---|---|
| 🎮 Command Center | Summarises player cohorts and retention metrics | Quickly understand the overall retention picture |
| 📊 Player Observatory | Explores daily retention, platforms, and cohorts | Investigate when players return after their first observed activity |
| ⚔️ Experiment Arena | Examines experiment balance, group metrics, uncertainty, and sample-size planning | Assess whether an experiment is ready for reliable interpretation |
| 🛡️ Data Integrity | Presents data-quality and validation information | Identify issues before trusting the results |

Open the [live dashboard](https://idle-loop-observatory-sggcmvrlqepybsy9xwrg2q.streamlit.app/) to explore the interface.

---

## 🎯 Product questions this project investigates

A game analytics workflow should help answer questions that matter to product, design, and live-operations teams.

- How many newly observed players return the next day?
- What proportion of a cohort returns exactly seven days after its cohort date?
- How do observed retention rates differ across platforms?
- How much statistical uncertainty surrounds a retention estimate?
- Are control and treatment groups allocated in the expected proportions?
- Is an experiment sufficiently powered to detect a meaningful improvement?
- Are the event definitions, observation windows, and data-quality checks consistent?
- Which conclusions are supported by the available evidence, and which remain hypotheses?

These are analytical questions the project is designed to investigate. They are not claims about any particular commercial game's performance.

---

## 📈 Public-data findings

The project analyses the public Firebase/Google Analytics Flood-It! sample.

| Metric | Observed result |
|---|---:|
| Eligible observed player cohorts | 3,998 |
| D1 retained players | 718 |
| D1 retention | 17.96% |
| D1 95% Wilson confidence interval | 16.80%–19.18% |
| D7 retained players | 191 |
| D7 retention | 4.78% |
| D7 95% Wilson confidence interval | 4.16%–5.48% |
| Source table coverage | 12 June–3 October 2018 |

The eligible cohort dates run from 12 June through 26 September 2018, allowing seven days of follow-up within the available table coverage.

### What do these numbers mean?

- **D1 retention of 17.96%:** 718 of 3,998 eligible observed cohorts had a qualifying session on the exact following day.
- **D7 retention of 4.78%:** 191 of 3,998 eligible observed cohorts had a qualifying session exactly seven days after their cohort date.
- **Confidence intervals:** These quantify sampling uncertainty around the estimated proportions under the chosen statistical model. They do not account for every possible source of measurement or selection bias.

These are historical sample results, not current industry benchmarks. Missing observed activity does not prove that a person permanently churned, and the results should not be generalised to idle games or Kolibri Games.

Detailed findings and validation outputs are available in [`reports/public_data/`](reports/public_data/).

---

## 🧠 Analytical methodology

### 1. Event data and cohort construction

Player analytics begins with a consistent definition of who belongs in a cohort and which events qualify as returning activity.

For the public dataset:

1. Identify each player's earliest observed `first_open` event.
2. Use that date as the player's cohort date.
3. Identify qualifying `session_start` events on the exact target day.
4. Exclude cohorts without sufficient follow-up for the requested retention metric.
5. Aggregate player outcomes into cohort- and platform-level metrics.

The exported `event_date` field is used consistently for the cohort-day calculations.

**D1 retention**

\[
R_{D1}=\frac{\text{Players active on cohort day}+1}
{\text{Eligible cohort players}}\times100
\]

**D7 retention**

\[
R_{D7}=\frac{\text{Players active on cohort day}+7}
{\text{Eligible cohort players}}\times100
\]

These are exact-day metrics, not cumulative measures of whether a player returned at any time during the first seven days.

### 2. Retention uncertainty with Wilson confidence intervals

A retention percentage alone can hide how uncertain an estimate is, particularly for smaller cohorts.

For an observed proportion \(\hat p=x/n\), the Wilson interval is:

\[
\frac{
\hat p+\frac{z^2}{2n}
\pm z\sqrt{\frac{\hat p(1-\hat p)}{n}+\frac{z^2}{4n^2}}
}{
1+\frac{z^2}{n}
}
\]

Where:

- \(x\) is the number of retained players.
- \(n\) is the eligible cohort size.
- \(\hat p\) is the observed retention proportion.
- \(z\) is the standard-normal critical value; approximately 1.96 for a two-sided 95% interval.

Wilson intervals are used instead of relying on the simple normal approximation for a proportion, especially when the number of successes is small or the observed rate is near zero or one.

### 3. Comparing two retention rates

For two independent groups, the implementation compares observed proportions using a two-proportion z-test.

The pooled proportion under the null hypothesis is:

\[
\hat p=\frac{x_A+x_B}{n_A+n_B}
\]

The standard error under the null is:

\[
SE_0=
\sqrt{\hat p(1-\hat p)
\left(\frac{1}{n_A}+\frac{1}{n_B}\right)}
\]

The test statistic is:

\[
z=\frac{\hat p_A-\hat p_B}{SE_0}
\]

The implementation also calculates a Newcombe confidence interval for the difference in proportions, using Wilson intervals for the two individual rates.

Interpretation matters: a small p-value is evidence against the null hypothesis under the test assumptions, not proof that a product change caused the difference. A non-significant result does not prove that the groups are equivalent.

### 4. Experiment sample-size planning

The experiment-design module estimates the sample size needed to detect a specified difference between two proportions.

The current illustrative planning scenario uses:

| Input | Value |
|---|---:|
| Baseline rate | 30% |
| Target rate | 35% |
| Absolute minimum detectable effect | 5 percentage points |
| Significance level, α | 0.05 |
| Statistical power | 80% |
| Required sample size | 1,376 per arm |
| Total required sample | 2,752 |

This is a hypothetical planning example, not an observed retention result.

The sample-size calculation uses a normal-approximation method for two independent proportions. Actual planning should also consider the metric definition, allocation ratio, repeated measurements, clustering, multiple comparisons, expected data loss, and the chosen statistical test.

### 5. Sample Ratio Mismatch (SRM)

A well-designed experiment should allocate users approximately according to the intended assignment ratio.

For a two-arm experiment, the SRM module compares observed group counts against expected counts using a chi-square goodness-of-fit statistic:

\[
\chi^2=\sum_{i=1}^{k}\frac{(O_i-E_i)^2}{E_i}
\]

Where:

- \(O_i\) is the observed count in group \(i\).
- \(E_i\) is the expected count under the assignment plan.
- \(k\) is the number of groups.

The implementation uses a configurable significance threshold, with 0.001 as the illustrative default.

An SRM flag indicates that the assignment counts warrant investigation. It does not, by itself, identify the cause of the mismatch.

### 6. Experiment data quality and observation windows

Retention outcomes are only meaningful when players have had sufficient time to reach the measurement window.

The quality module supports:

- Filtering players whose observation window has matured.
- Applying an analysis cutoff and optional processing delay.
- Checking control/treatment allocation balance.
- Summarising binary outcomes by assignment group.

For example, a D7 outcome should not be treated as a negative result for a player who has not yet had seven days of follow-up.

The analysis also distinguishes data-quality failures from product-performance changes. Missing events, immature observation windows, and unexpected assignment counts should be investigated before interpreting an experiment result.

---

## 🧪 Synthetic experiment demonstration

The project includes a separate synthetic idle-game event generator and an experiment-readiness workflow.

The current development fixture contains 500 simulated players over 14 days. These generated events are useful for testing player-level aggregation, retention calculations, group assignment, and experiment-quality checks.

In the illustrative experiment run, the generated cohort was assigned to:

- Control: 257 players
- Treatment: 243 players

The SRM check did not flag an allocation mismatch at the configured threshold. The retention comparisons were not statistically significant:

| Metric | Control | Treatment | Treatment − control |
|---|---:|---:|---:|
| D1 retention | 46.30% | 46.91% | +0.61 percentage points |
| D7 retention | 28.79% | 27.57% | −1.22 percentage points |

These results are outputs from a synthetic development fixture. The underlying retention outcomes were generated before group assignment; no treatment effect was simulated. The observed differences therefore must not be interpreted as evidence that a game change improved or reduced retention.

The synthetic workflow demonstrates how an analyst can validate a pipeline and interpret uncertainty before applying the same process to a properly instrumented, randomised product experiment.

---

## 🛡️ Data quality, validation, and testing

The project includes a dedicated public-export validation script and automated tests.

Validation checks include:

- Required files and expected columns.
- Daily event-quality records and duplicate rows.
- Retention calculations and count consistency.
- Confidence-interval bounds and arithmetic.
- Reconciliation of platform-level counts with pooled totals.

The recorded public-export validation run completed with **zero errors and zero warnings**.

The test suite covers cohort construction, retention SQL, confidence intervals, experiment design, experiment quality, and experiment-readiness outputs.

Run the tests locally:

```bash
python -m pytest tests -q
```

A previously recorded development run passed 69 tests. Re-run the suite after making changes to verify the current code.

---

## 🏗️ Architecture and project structure

```text
Idle-Loop-Observatory/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── docs/
│   └── data_sources.yml
│
├── data/
│   └── external/
│       └── flood_it/
│           ├── 01_schema_inspection.csv
│           ├── 02_date_coverage.csv
│           ├── 03_event_quality_by_day.csv
│           ├── 04_daily_retention.csv
│           └── 05_retention_summary.csv
│
├── reports/
│   └── public_data/
│       ├── flood_it_d1_retention.png
│       ├── flood_it_d7_retention.png
│       ├── flood_it_retention_findings.md
│       └── flood_it_validation_report.txt
│
├── sql/
│   ├── investigations/
│   │   ├── 000_environment_check.sql
│   │   ├── 001_public_game_data_audit.sql
│   │   ├── 002_event_inventory.sql
│   │   ├── 003_retention_by_day.sql
│   │   └── 004_player_segmentation.sql
│   │
│   └── public_data/
│       ├── 01_schema_inspection.sql
│       ├── 02_date_coverage.sql
│       ├── 03_event_quality_by_day.sql
│       ├── 04_daily_retention.sql
│       └── 05_retention_summary.sql
│
├── src/
│   ├── analytics/
│   │   ├── analyze_flood_it_retention.py
│   │   ├── build_player_cohort.py
│   │   ├── experiment_design.py
│   │   ├── experiment_quality.py
│   │   ├── retention_uncertainty.py
│   │   └── run_experiment_readiness.py
│   │
│   └── data/
│       ├── generate_synthetic_idle_events.py
│       ├── profile_dataset.py
│       └── validate_flood_it_exports.py
│
└── tests/
    ├── test_build_player_cohort.py
    ├── test_experiment_design.py
    ├── test_experiment_quality.py
    ├── test_experiment_readiness.py
    ├── test_retention_sql.py
    └── test_retention_uncertainty.py
```

Generated data and processed experiment outputs are excluded from version control to keep the repository lean. The five compact public-data exports are committed so the deployed dashboard can load the analysis inputs.

---

## 🛠️ Technology stack

| Technology | Purpose |
|---|---|
| Python | Analytics logic, data processing, statistical calculations |
| SQL | Event exploration, cohort construction, retention aggregation |
| DuckDB | Local analytical queries over event data |
| Pandas and NumPy | Data manipulation and numerical calculations |
| SciPy and statsmodels | Statistical tests and experiment planning |
| Streamlit | Interactive dashboard and navigation |
| Plotly | Interactive visualisations |
| Pytest | Automated validation and regression tests |
| Git and GitHub | Version control and source-code hosting |
| Streamlit Community Cloud | Public dashboard deployment |

---

## 💻 Run locally

### 1. Clone the repository

```bash
git clone https://github.com/souravgupta166/Idle-Loop-Observatory.git
cd Idle-Loop-Observatory
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Launch the dashboard

```bash
streamlit run app.py
```

Open the local URL shown in the terminal, usually `http://localhost:8501`.

### 5. Run automated tests

```bash
python -m pytest tests -q
```

The deployed app uses the five committed public-data exports. Rebuilding the synthetic experiment workflow requires running its relevant generation and analytics scripts in the intended sequence.

---

## 📚 Data sources and limitations

### Public data

The public-data workflow uses the Firebase/Google Analytics sample:

`firebase-public-project.analytics_153293282.events_*`

The source contains historical Flood-It! mobile-game event data. It is useful for demonstrating event-data analysis, cohort construction, retention measurement, and data-quality checks.

It is not a source of Kolibri Games telemetry or idle-game-specific evidence.

### Synthetic data

The synthetic dataset is generated locally for development and workflow testing. It is not observed player behaviour, and it should not be combined with the public sample as though both represented the same population.

### Important limitations

- The public sample dates from 2018.
- Flood-It! is not an idle game.
- The data is not from Kolibri Games.
- Observed event absence is not definitive proof of churn.
- Historical platform differences are descriptive, not causal.
- Synthetic experiment results do not estimate a real treatment effect.
- Confidence intervals and significance tests do not eliminate instrumentation bias, selection bias, or other study-design limitations.

These boundaries are intentional. A credible analytics workflow should make its evidence and assumptions explicit.

---

## 🔭 Potential next steps

The project provides a foundation for extending the workflow with:

- Survival analysis and time-to-churn modelling.
- Cohort retention heatmaps and deeper player segmentation.
- More rigorous experiment monitoring and sequential decision frameworks.
- Guardrail metrics, such as session frequency and monetisation, when suitable data is available.
- Reproducible analytical reports and configurable cohort definitions.
- An idle-game dataset with documented provenance and appropriate permissions.

These are potential extensions, not features claimed to be implemented in the current version.

---

## 👨‍💻 About the project

Idle Loop Observatory was built as a portfolio project to demonstrate practical game-data analytics skills: event-level data processing, retention definitions, SQL, statistical uncertainty, experiment design, validation, automated testing, and interactive reporting.

The central principle is simple:

**A metric is only useful when its definition is clear, its data is trustworthy, and its uncertainty is understood.**

### 🔗 Links

- **Live dashboard:** https://idle-loop-observatory-sggcmvrlqepybsy9xwrg2q.streamlit.app/
- **GitHub repository:** https://github.com/souravgupta166/Idle-Loop-Observatory

If you explore the project, feedback on the analytical methodology, experiment workflow, and dashboard experience is welcome.
