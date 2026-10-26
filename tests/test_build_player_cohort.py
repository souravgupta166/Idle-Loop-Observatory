
import pandas as pd
import pytest

from src.analytics import build_player_cohort as pipeline


@pytest.fixture
def sample_players():
    return pd.DataFrame(
        {
            "player_id": ["p1", "p2", "p3", "p4"],
            "install_timestamp_utc": pd.to_datetime(
                [
                    "2026-10-18T12:00:00Z",
                    "2026-10-19T12:00:00Z",
                    "2026-10-25T12:00:00Z",
                    "2026-10-26T12:00:00Z",
                ],
                utc=True,
            ),
            "acquisition_channel": [
                "organic", "paid_social", "search", "organic"
            ],
            "platform": ["android", "ios", "android", "ios"],
            "tutorial_completed_d0": [1, 0, 1, 0],
            "d1_retained": [1, 0, 1, 0],
            "d7_retained": [1, 1, 0, 0],
        }
    )


@pytest.fixture
def configure_pipeline(monkeypatch, sample_players):
    monkeypatch.setattr(
        pipeline,
        "load_player_cohort",
        lambda: sample_players.copy(),
    )
    monkeypatch.setattr(
        pipeline,
        "ANALYSIS_CUTOFF_UTC",
        pd.Timestamp("2026-10-26T12:00:00Z"),
    )
    monkeypatch.setattr(pipeline, "PROCESSING_DELAY_HOURS", 0)


def test_build_cohort_has_one_row_per_player(configure_pipeline):
    cohort = pipeline.build_cohort()

    assert len(cohort) == 4
    assert cohort["player_id"].is_unique


def test_d1_eligibility_uses_install_timestamp(configure_pipeline):
    cohort = pipeline.build_cohort().set_index("player_id")

    assert cohort.loc["p1", "d1_eligible"]
    assert cohort.loc["p2", "d1_eligible"]
    assert cohort.loc["p3", "d1_eligible"]
    assert not cohort.loc["p4", "d1_eligible"]


def test_d7_eligibility_uses_install_timestamp(configure_pipeline):
    cohort = pipeline.build_cohort().set_index("player_id")

    assert cohort.loc["p1", "d7_eligible"]
    assert cohort.loc["p2", "d7_eligible"]
    assert not cohort.loc["p3", "d7_eligible"]
    assert not cohort.loc["p4", "d7_eligible"]


def test_immature_retention_outcomes_are_unknown(configure_pipeline):
    cohort = pipeline.build_cohort().set_index("player_id")

    assert pd.isna(cohort.loc["p4", "d1_retained"])
    assert pd.isna(cohort.loc["p3", "d7_retained"])
    assert pd.isna(cohort.loc["p4", "d7_retained"])


def test_mature_retention_outcomes_are_preserved(configure_pipeline):
    cohort = pipeline.build_cohort().set_index("player_id")

    assert cohort.loc["p1", "d1_retained"] == 1
    assert cohort.loc["p2", "d1_retained"] == 0
    assert cohort.loc["p1", "d7_retained"] == 1


def test_cohort_has_synthetic_provenance(configure_pipeline):
    cohort = pipeline.build_cohort()

    assert cohort["is_synthetic"].all()
    assert (
        cohort["data_provenance"]
        == "synthetic_development_fixture"
    ).all()


def test_analysis_cutoff_is_recorded(configure_pipeline):
    cohort = pipeline.build_cohort()

    assert (
        cohort["analysis_cutoff_utc"]
        == "2026-10-26T12:00:00+00:00"
    ).all()


def test_build_cohort_does_not_modify_source_data(
    configure_pipeline, sample_players
):
    original = sample_players.copy(deep=True)

    pipeline.build_cohort()

    pd.testing.assert_frame_equal(sample_players, original)
