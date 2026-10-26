
"""Plan sample size for a hypothetical player-retention experiment.

This script calculates required sample size for a two-arm randomized
experiment comparing two independent retention proportions.

No real Kolibri Games data is used.
"""

from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize


def calculate_sample_size(
    baseline_retention: float,
    target_retention: float,
    alpha: float = 0.05,
    power: float = 0.80,
    allocation_ratio: float = 1.0,
) -> dict:
    """Calculate approximate sample size for a two-proportion experiment.

    Args:
        baseline_retention: Expected control retention, from 0 to 1.
        target_retention: Expected treatment retention, from 0 to 1.
        alpha: Two-sided significance level.
        power: Desired statistical power.
        allocation_ratio: Treatment sample size / control sample size.

    Returns:
        Sample-size estimates for control and treatment arms.
    """

    for name, value in [
        ("baseline_retention", baseline_retention),
        ("target_retention", target_retention),
    ]:
        if not 0 < value < 1:
            raise ValueError(f"{name} must be strictly between 0 and 1.")

    if baseline_retention == target_retention:
        raise ValueError("Target retention must differ from baseline retention.")

    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1.")

    if not 0 < power < 1:
        raise ValueError("power must be between 0 and 1.")

    if allocation_ratio <= 0:
        raise ValueError("allocation_ratio must be greater than zero.")

    effect_size = abs(
        proportion_effectsize(baseline_retention, target_retention)
    )

    analysis = NormalIndPower()

    control_n = analysis.solve_power(
        effect_size=effect_size,
        power=power,
        alpha=alpha,
        ratio=allocation_ratio,
        alternative="two-sided",
    )

    treatment_n = control_n * allocation_ratio

    return {
        "baseline_retention": baseline_retention,
        "target_retention": target_retention,
        "absolute_lift_pp": (
            target_retention - baseline_retention
        ) * 100,
        "relative_lift_pct": (
            target_retention / baseline_retention - 1
        ) * 100,
        "alpha": alpha,
        "power": power,
        "allocation_ratio": allocation_ratio,
        "control_sample_size": int(__import__("math").ceil(control_n)),
        "treatment_sample_size": int(__import__("math").ceil(treatment_n)),
        "total_sample_size": (
            int(__import__("math").ceil(control_n))
            + int(__import__("math").ceil(treatment_n))
        ),
    }


def main():
    # Planning assumptions only; replace with a defensible real baseline
    # before using this calculation to launch an actual experiment.
    baseline = 0.30
    target = 0.35

    result = calculate_sample_size(
        baseline_retention=baseline,
        target_retention=target,
        alpha=0.05,
        power=0.80,
        allocation_ratio=1.0,
    )

    print("=" * 68)
    print("IDLE LOOP OBSERVATORY — EXPERIMENT SAMPLE-SIZE PLAN")
    print("HYPOTHETICAL ASSUMPTIONS — NOT REAL GAME PERFORMANCE")
    print("=" * 68)
    print(f"Control retention assumption: {baseline:.1%}")
    print(f"Treatment retention target:   {target:.1%}")
    print(f"Absolute lift to detect:      {result['absolute_lift_pp']:.1f} pp")
    print(f"Relative lift to detect:      {result['relative_lift_pct']:.1f}%")
    print(f"Significance level:           {result['alpha']:.0%}")
    print(f"Statistical power:            {result['power']:.0%}")
    print(f"Allocation ratio (T/C):       {result['allocation_ratio']:.1f}")
    print("-" * 68)
    print(f"Required control players:     {result['control_sample_size']:,}")
    print(f"Required treatment players:   {result['treatment_sample_size']:,}")
    print(f"Total required players:       {result['total_sample_size']:,}")
    print("-" * 68)
    print(
        "Planning note: this is an approximate normal-theory calculation "
        "for two independent proportions. Confirm assumptions and use "
        "a suitable final analysis plan before running a real experiment."
    )


if __name__ == "__main__":
    main()
