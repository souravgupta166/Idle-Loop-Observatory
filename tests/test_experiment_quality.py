
import pandas as pd
import pytest

from src.analytics.experiment_quality import (
    check_sample_ratio,
    filter_mature_players,
    summarize_binary_metrics,
)


# =========================================================
# Observation-window eligibility
# =========================================================

def test_filter_mature_players_uses_install_time_and_cutoff():
    df = pd.DataFrame(
        {
            "player_id": ["p1", "p2", "p3"],
            "install_timestamp_utc": [
                "2026-10-18T12:00:00Z",
                "2026-10-19T12:00:00Z",
                "2026-10-20T12:00:00Z",
            ],
            "last_session_timestamp_utc": [
                "2026-10-19T12:00:00Z",
                "2026-10-19T12:00:00Z",
                "2026-10-20T12:00:00Z",
            ],
        }
    )

    result = filter_mature_players(
        df,
        observation_day=7,
        cutoff_timestamp="2026-10-26T12:00:00Z",
    )

    # p1 and p2 have completed seven full days.
    # p3 has completed only six days.
    assert result["player_id"].tolist() == ["p1", "p2"]


def test_filter_mature_players_accounts_for_processing_delay():
    df = pd.DataFrame(
        {
            "player_id": ["p1", "p2"],
            "install_timestamp_utc": [
                "2026-10-19T11:01:00Z",
                "2026-10-19T11:00:00Z",
            ],
        }
    )

    result = filter_mature_players(
        df,
        observation_day=7,
        cutoff_timestamp="2026-10-26T12:00:00Z",
        processing_delay_hours=1,
    )

    # p1 becomes eligible at 12:01, after the cutoff.
    # p2 becomes eligible exactly at 12:00.
    assert result["player_id"].tolist() == ["p2"]


def test_filter_mature_players_rejects_naive_cutoff():
    df = pd.DataFrame(
        {
            "install_timestamp_utc": [
                "2026-10-18T12:00:00Z",
            ],
        }
    )

    with pytest.raises(ValueError, match="timezone"):
        filter_mature_players(
            df,
            observation_day=7,
            cutoff_timestamp="2026-10-26 12:00:00",
        )


def test_filter_mature_players_excludes_invalid_install_timestamp():
    df = pd.DataFrame(
        {
            "player_id": ["p1", "p2"],
            "install_timestamp_utc": [
                "not-a-timestamp",
                "2026-10-18T12:00:00Z",
            ],
        }
    )

    result = filter_mature_players(
        df,
        observation_day=7,
        cutoff_timestamp="2026-10-26T12:00:00Z",
    )

    assert result["player_id"].tolist() == ["p2"]


def test_filter_mature_players_does_not_modify_original_dataframe():
    df = pd.DataFrame(
        {
            "player_id": ["p1", "p2"],
            "install_timestamp_utc": [
                "2026-10-18T12:00:00Z",
                "2026-10-25T12:00:00Z",
            ],
        }
    )
    original = df.copy(deep=True)

    filter_mature_players(
        df,
        observation_day=7,
        cutoff_timestamp="2026-10-26T12:00:00Z",
    )

    pd.testing.assert_frame_equal(df, original)


@pytest.mark.parametrize("day", [-1, -7])
def test_filter_mature_players_rejects_negative_observation_day(day):
    df = pd.DataFrame(
        {
            "install_timestamp_utc": [
                "2026-10-18T12:00:00Z",
            ],
        }
    )

    with pytest.raises(ValueError):
        filter_mature_players(
            df,
            observation_day=day,
        )


def test_filter_mature_players_rejects_negative_processing_delay():
    df = pd.DataFrame(
        {
            "install_timestamp_utc": [
                "2026-10-18T12:00:00Z",
            ],
        }
    )

    with pytest.raises(ValueError):
        filter_mature_players(
            df,
            observation_day=7,
            processing_delay_hours=-1,
        )


def test_filter_mature_players_includes_exact_eligibility_boundary():
    df = pd.DataFrame(
        {
            "player_id": ["boundary", "not_yet"],
            "install_timestamp_utc": [
                "2026-10-19T12:00:00Z",
                "2026-10-19T12:00:01Z",
            ],
        }
    )

    result = filter_mature_players(
        df,
        observation_day=7,
        cutoff_timestamp="2026-10-26T12:00:00Z",
    )

    assert result["player_id"].tolist() == ["boundary"]


# =========================================================
# Sample-ratio mismatch checks
# =========================================================

def test_sample_ratio_check_accepts_balanced_assignment():
    result = check_sample_ratio(
        control_count=5000,
        treatment_count=5000,
    )

    assert result["observed_control_share"] == pytest.approx(0.5)
    assert result["p_value"] > 0.001
    assert result["srm_flag"] is False


def test_sample_ratio_check_flags_large_imbalance():
    result = check_sample_ratio(
        control_count=6000,
        treatment_count=4000,
    )

    assert result["srm_flag"] is True
    assert result["p_value"] < 0.001


def test_sample_ratio_check_supports_non_50_50_allocation():
    result = check_sample_ratio(
        control_count=2500,
        treatment_count=7500,
        expected_control_share=0.25,
    )

    assert result["observed_control_share"] == pytest.approx(0.25)
    assert result["srm_flag"] is False


@pytest.mark.parametrize(
    "control,treatment,share,alpha",
    [
        (-1, 10, 0.5, 0.001),
        (0, 0, 0.5, 0.001),
        (10, 10, 0.0, 0.001),
        (10, 10, 1.0, 0.001),
        (10, 10, 0.5, 0.0),
        (10, 10, 0.5, 1.0),
    ],
)
def test_sample_ratio_check_rejects_invalid_inputs(
    control,
    treatment,
    share,
    alpha,
):
    with pytest.raises(ValueError):
        check_sample_ratio(
            control_count=control,
            treatment_count=treatment,
            expected_control_share=share,
            alpha=alpha,
        )


# =========================================================
# Binary metric summaries
# =========================================================

def test_binary_metric_summary_calculates_lift():
    df = pd.DataFrame(
        {
            "variant": ["control"] * 4 + ["treatment"] * 4,
            "d1_retained": [1, 0, 1, 0, 1, 1, 1, 0],
            "tutorial_completed": [1, 1, 0, 0, 1, 1, 1, 1],
        }
    )

    result = summarize_binary_metrics(
        df=df,
        assignment_column="variant",
        control_label="control",
        treatment_label="treatment",
        metrics=["d1_retained", "tutorial_completed"],
    )

    d1 = result.loc[result["metric"] == "d1_retained"].iloc[0]

    assert d1["control_n"] == 4
    assert d1["treatment_n"] == 4
    assert d1["control_rate_pct"] == pytest.approx(50.0)
    assert d1["treatment_rate_pct"] == pytest.approx(75.0)
    assert d1["absolute_lift_pp"] == pytest.approx(25.0)


def test_binary_metric_summary_rejects_non_binary_values():
    df = pd.DataFrame(
        {
            "variant": ["control", "control", "treatment", "treatment"],
            "d1_retained": [0, 2, 1, 0],
        }
    )

    with pytest.raises(ValueError):
        summarize_binary_metrics(
            df=df,
            assignment_column="variant",
            control_label="control",
            treatment_label="treatment",
            metrics=["d1_retained"],
        )


def test_binary_metric_summary_rejects_unexpected_variant():
    df = pd.DataFrame(
        {
            "variant": ["control", "other"],
            "d1_retained": [0, 1],
        }
    )

    with pytest.raises(ValueError):
        summarize_binary_metrics(
            df=df,
            assignment_column="variant",
            control_label="control",
            treatment_label="treatment",
            metrics=["d1_retained"],
        )


def test_binary_metric_summary_rejects_missing_assignment():
    df = pd.DataFrame(
        {
            "variant": ["control", None],
            "d1_retained": [0, 1],
        }
    )

    with pytest.raises(ValueError):
        summarize_binary_metrics(
            df=df,
            assignment_column="variant",
            control_label="control",
            treatment_label="treatment",
            metrics=["d1_retained"],
        )


def test_binary_metric_summary_handles_zero_control_rate():
    df = pd.DataFrame(
        {
            "variant": ["control"] * 2 + ["treatment"] * 2,
            "d1_retained": [0, 0, 1, 1],
        }
    )

    result = summarize_binary_metrics(
        df=df,
        assignment_column="variant",
        control_label="control",
        treatment_label="treatment",
        metrics=["d1_retained"],
    )

    assert result.iloc[0]["control_rate_pct"] == 0.0
    assert result.iloc[0]["relative_lift_pct"] is None


def test_binary_metric_summary_rejects_missing_columns():
    df = pd.DataFrame(
        {
            "variant": ["control", "treatment"],
        }
    )

    with pytest.raises(ValueError):
        summarize_binary_metrics(
            df=df,
            assignment_column="variant",
            control_label="control",
            treatment_label="treatment",
            metrics=["d1_retained"],
        )


def test_binary_metric_summary_rejects_empty_metric_list():
    df = pd.DataFrame(
        {
            "variant": ["control", "treatment"],
        }
    )

    with pytest.raises(ValueError):
        summarize_binary_metrics(
            df=df,
            assignment_column="variant",
            control_label="control",
            treatment_label="treatment",
            metrics=[],
        )
