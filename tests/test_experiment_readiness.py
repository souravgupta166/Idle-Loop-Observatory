
import pandas as pd
import pytest

from src.analytics import run_experiment_readiness as pipeline


@pytest.fixture
def cohort():
    """Small synthetic cohort with different D1 and D7 maturity."""
    return pd.DataFrame(
        {
            "player_id": [f"p{i}" for i in range(8)],
            "d1_eligible": [True] * 6 + [False] * 2,
            "d7_eligible": [True] * 4 + [False] * 4,
            "d1_retained": [1, 0, 1, 1, 0, 1, None, None],
            "d7_retained": [1, 0, 1, 0, None, None, None, None],
            "is_synthetic": [True] * 8,
        }
    )


@pytest.fixture
def assigned(cohort):
    """Assign reproducible synthetic experiment arms."""
    return pipeline.assign_synthetic_arms(cohort)


@pytest.fixture
def statistical_results(assigned):
    """Calculate base metrics and statistical uncertainty."""
    from src.analytics.experiment_quality import summarize_binary_metrics

    base_metrics = summarize_binary_metrics(
        assigned,
        assignment_column="experiment_arm",
        control_label="control",
        treatment_label="treatment",
        metrics=["d1_retained", "d7_retained"],
    )

    return pipeline.calculate_statistical_results(assigned, base_metrics)


def test_assignment_is_reproducible(cohort):
    first = pipeline.assign_synthetic_arms(cohort)
    second = pipeline.assign_synthetic_arms(cohort)

    assert first["experiment_arm"].tolist() == second["experiment_arm"].tolist()


def test_assignment_covers_every_player(assigned, cohort):
    assert len(assigned) == len(cohort)
    assert assigned["player_id"].is_unique
    assert set(assigned["experiment_arm"]) == {"control", "treatment"}


def test_assignment_does_not_modify_input(cohort):
    original = cohort.copy(deep=True)

    pipeline.assign_synthetic_arms(cohort)

    pd.testing.assert_frame_equal(cohort, original)


def test_load_cohort_rejects_non_synthetic_data(tmp_path, monkeypatch, cohort):
    path = tmp_path / "cohort.csv"
    non_synthetic = cohort.copy()
    non_synthetic["is_synthetic"] = False
    non_synthetic.to_csv(path, index=False)

    monkeypatch.setattr(pipeline, "INPUT_PATH", path)

    with pytest.raises(ValueError, match="synthetic data only"):
        pipeline.load_cohort()


def test_load_cohort_rejects_duplicate_players(tmp_path, monkeypatch, cohort):
    duplicated = cohort.copy()
    duplicated.loc[1, "player_id"] = duplicated.loc[0, "player_id"]

    path = tmp_path / "cohort.csv"
    duplicated.to_csv(path, index=False)

    monkeypatch.setattr(pipeline, "INPUT_PATH", path)

    with pytest.raises(ValueError, match="unique"):
        pipeline.load_cohort()


def test_metrics_use_only_mature_observations(assigned):
    from src.analytics.experiment_quality import summarize_binary_metrics

    metrics = summarize_binary_metrics(
        assigned,
        assignment_column="experiment_arm",
        control_label="control",
        treatment_label="treatment",
        metrics=["d1_retained", "d7_retained"],
    )

    by_metric = metrics.set_index("metric")

    assert (
        by_metric.loc["d1_retained", "control_n"]
        + by_metric.loc["d1_retained", "treatment_n"]
        == 6
    )
    assert (
        by_metric.loc["d7_retained", "control_n"]
        + by_metric.loc["d7_retained", "treatment_n"]
        == 4
    )


def test_report_disclaims_causal_claims(assigned, statistical_results):
    from src.analytics.experiment_quality import check_sample_ratio

    counts = assigned["experiment_arm"].value_counts()

    srm = check_sample_ratio(
        control_count=int(counts.get("control", 0)),
        treatment_count=int(counts.get("treatment", 0)),
    )

    report = pipeline.build_report(assigned, statistical_results, srm)

    assert "Synthetic demonstration only" in report
    assert "not causal effects" in report
    assert "Kolibri Games" in report


def test_statistical_results_include_confidence_intervals(statistical_results):
    required = [
        "control_ci_low_pct",
        "control_ci_high_pct",
        "treatment_ci_low_pct",
        "treatment_ci_high_pct",
        "difference_ci_low_pp",
        "difference_ci_high_pp",
        "z_statistic",
        "p_value",
        "statistically_significant",
    ]

    assert all(column in statistical_results.columns for column in required)
    assert statistical_results["p_value"].between(0, 1).all()


def test_difference_intervals_are_ordered(statistical_results):
    assert (
        statistical_results["difference_ci_low_pp"]
        <= statistical_results["difference_ci_high_pp"]
    ).all()


def test_statistical_results_use_mature_players_only(
    cohort, statistical_results
):
    by_metric = statistical_results.set_index("metric")

    assert (
        by_metric.loc["d1_retained", "control_n"]
        + by_metric.loc["d1_retained", "treatment_n"]
        == int(cohort["d1_eligible"].sum())
    )

    assert (
        by_metric.loc["d7_retained", "control_n"]
        + by_metric.loc["d7_retained", "treatment_n"]
        == int(cohort["d7_eligible"].sum())
    )


def test_statistical_report_documents_uncertainty(
    assigned, statistical_results
):
    from src.analytics.experiment_quality import check_sample_ratio

    counts = assigned["experiment_arm"].value_counts()

    srm = check_sample_ratio(
        control_count=int(counts.get("control", 0)),
        treatment_count=int(counts.get("treatment", 0)),
    )

    report = pipeline.build_report(assigned, statistical_results, srm)

    assert "Wilson 95% confidence intervals" in report
    assert "Newcombe 95% confidence intervals" in report
    assert (
        "A p-value is not the probability that the null hypothesis is true."
        in report
    )
