
import pandas as pd
import pytest

from src.analytics.retention_uncertainty import (
    compare_groups,
    summarize_rate,
)


def test_wilson_interval_contains_observed_rate():
    result = summarize_rate(
        label="Test segment",
        successes=45,
        total=100,
    )

    assert result["retention_pct"] == 45.0
    assert result["ci_95_low_pct"] < 45.0
    assert result["ci_95_high_pct"] > 45.0


def test_wilson_interval_is_valid():
    result = summarize_rate(
        label="Test segment",
        successes=0,
        total=100,
    )

    assert result["retention_pct"] == 0.0
    assert result["ci_95_low_pct"] >= 0.0
    assert result["ci_95_high_pct"] <= 100.0


def test_empty_group_is_rejected():
    with pytest.raises(ValueError):
        summarize_rate(
            label="Empty segment",
            successes=0,
            total=0,
        )


def test_difference_is_reported_in_correct_direction(capsys):
    df = pd.DataFrame(
        {
            "completed_tutorial": [1] * 80 + [0] * 80,
            "d1": [1] * 48 + [0] * 32 + [1] * 32 + [0] * 48,
        }
    )

    result = compare_groups(
        df=df,
        metric="d1",
        group_column="completed_tutorial",
        group_a=1,
        group_b=0,
    )

    assert result["rate_a"] == pytest.approx(0.60)
    assert result["rate_b"] == pytest.approx(0.40)
    assert result["difference"] == pytest.approx(0.20)
    assert result["ci_low"] < result["ci_high"]
    assert 0.0 <= result["p_value"] <= 1.0

    output = capsys.readouterr().out
    assert "Newcombe CI" in output
    assert "percentage points" in output


def test_invalid_success_count_is_rejected():
    with pytest.raises(ValueError):
        summarize_rate(
            label="Invalid segment",
            successes=101,
            total=100,
        )
