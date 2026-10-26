
import pytest

from src.analytics.experiment_design import calculate_sample_size


def test_sample_size_is_positive_and_balanced():
    result = calculate_sample_size(
        baseline_retention=0.30,
        target_retention=0.35,
        alpha=0.05,
        power=0.80,
    )

    assert result["control_sample_size"] > 0
    assert result["treatment_sample_size"] > 0
    assert result["control_sample_size"] == result["treatment_sample_size"]
    assert result["total_sample_size"] == (
        result["control_sample_size"]
        + result["treatment_sample_size"]
    )


def test_five_percentage_point_lift_is_calculated():
    result = calculate_sample_size(
        baseline_retention=0.30,
        target_retention=0.35,
    )

    assert result["absolute_lift_pp"] == pytest.approx(5.0)
    assert result["relative_lift_pct"] == pytest.approx(16.6667, rel=1e-3)


def test_smaller_effect_requires_more_players():
    small_effect = calculate_sample_size(
        baseline_retention=0.30,
        target_retention=0.32,
    )
    larger_effect = calculate_sample_size(
        baseline_retention=0.30,
        target_retention=0.35,
    )

    assert (
        small_effect["total_sample_size"]
        > larger_effect["total_sample_size"]
    )


def test_higher_power_requires_more_players():
    standard_power = calculate_sample_size(
        baseline_retention=0.30,
        target_retention=0.35,
        power=0.80,
    )
    higher_power = calculate_sample_size(
        baseline_retention=0.30,
        target_retention=0.35,
        power=0.90,
    )

    assert (
        higher_power["total_sample_size"]
        > standard_power["total_sample_size"]
    )


@pytest.mark.parametrize(
    "baseline,target",
    [
        (0.0, 0.35),
        (1.0, 0.35),
        (0.30, 0.0),
        (0.30, 1.0),
        (0.30, 0.30),
    ],
)
def test_invalid_retention_inputs_are_rejected(baseline, target):
    with pytest.raises(ValueError):
        calculate_sample_size(
            baseline_retention=baseline,
            target_retention=target,
        )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"alpha": 0.0},
        {"alpha": 1.0},
        {"power": 0.0},
        {"power": 1.0},
        {"allocation_ratio": 0.0},
        {"allocation_ratio": -1.0},
    ],
)
def test_invalid_design_parameters_are_rejected(kwargs):
    with pytest.raises(ValueError):
        calculate_sample_size(
            baseline_retention=0.30,
            target_retention=0.35,
            **kwargs,
        )
