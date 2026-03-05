"""Tests for flashscore_scraper core logic."""

import pandas as pd
import pytest
from flashscore_scraper import build_master_table, get_top2_per_league, FALLBACK_DATA


@pytest.fixture()
def sample_records():
    """Minimal multi-league dataset for unit tests."""
    return [
        {"League": "League A", "Team": "Alpha",   "MP": 10, "W": 8, "D": 1, "L": 1, "GF": 25, "GA": 8,  "Pts": 25},
        {"League": "League A", "Team": "Beta",    "MP": 10, "W": 6, "D": 2, "L": 2, "GF": 18, "GA": 10, "Pts": 20},
        {"League": "League A", "Team": "Gamma",   "MP": 10, "W": 3, "D": 1, "L": 6, "GF": 12, "GA": 20, "Pts": 10},
        {"League": "League B", "Team": "Delta",   "MP": 8,  "W": 7, "D": 0, "L": 1, "GF": 20, "GA": 5,  "Pts": 21},
        {"League": "League B", "Team": "Epsilon", "MP": 8,  "W": 4, "D": 2, "L": 2, "GF": 14, "GA": 9,  "Pts": 14},
        {"League": "League B", "Team": "Zeta",    "MP": 8,  "W": 1, "D": 1, "L": 6, "GF": 6,  "GA": 18, "Pts": 4},
    ]


class TestBuildMasterTable:
    def test_returns_dataframe(self, sample_records):
        df = build_master_table(sample_records)
        assert isinstance(df, pd.DataFrame)

    def test_win_percentage_calculation(self, sample_records):
        df = build_master_table(sample_records)
        alpha = df.loc[df["Team"] == "Alpha"].iloc[0]
        # 8 wins / 10 games = 80.00 %
        assert alpha["Win%"] == pytest.approx(80.0)

    def test_win_percentage_zero_when_no_wins(self, sample_records):
        records = [{"League": "X", "Team": "T", "MP": 5, "W": 0, "D": 3, "L": 2, "GF": 2, "GA": 5, "Pts": 3}]
        df = build_master_table(records)
        assert df.iloc[0]["Win%"] == 0.0

    def test_league_rank_is_1_for_highest_win_pct(self, sample_records):
        df = build_master_table(sample_records)
        for league in df["League"].unique():
            top = df[df["League"] == league].sort_values("Win%", ascending=False).iloc[0]
            assert top["League Rank"] == 1

    def test_all_required_columns_present(self, sample_records):
        df = build_master_table(sample_records)
        for col in ("League", "Team", "MP", "W", "D", "L", "GF", "GA", "Pts", "Win%", "League Rank"):
            assert col in df.columns

    def test_sorted_by_league_then_win_pct_desc(self, sample_records):
        df = build_master_table(sample_records).reset_index(drop=True)
        for league in df["League"].unique():
            subset = df[df["League"] == league]["Win%"].tolist()
            assert subset == sorted(subset, reverse=True)


class TestGetTop2PerLeague:
    def test_returns_exactly_2_per_league(self, sample_records):
        df = build_master_table(sample_records)
        top2 = get_top2_per_league(df)
        for league in top2["League"].unique():
            assert len(top2[top2["League"] == league]) == 2

    def test_top2_are_highest_win_pct(self, sample_records):
        df = build_master_table(sample_records)
        top2 = get_top2_per_league(df)
        for league in top2["League"].unique():
            top_teams = set(top2[top2["League"] == league]["Team"])
            all_teams = df[df["League"] == league].nlargest(2, "Win%")["Team"]
            assert top_teams == set(all_teams)

    def test_result_has_required_columns(self, sample_records):
        df = build_master_table(sample_records)
        top2 = get_top2_per_league(df)
        for col in ("League", "Team", "MP", "W", "D", "L", "GF", "GA", "Pts", "Win%"):
            assert col in top2.columns

    def test_top2_covers_all_leagues(self, sample_records):
        df = build_master_table(sample_records)
        top2 = get_top2_per_league(df)
        assert set(top2["League"].unique()) == set(df["League"].unique())


class TestFallbackData:
    def test_fallback_has_multiple_leagues(self):
        leagues = {r["League"] for r in FALLBACK_DATA}
        assert len(leagues) >= 5

    def test_fallback_has_valid_win_draw_loss(self):
        for row in FALLBACK_DATA:
            assert row["W"] + row["D"] + row["L"] == row["MP"], (
                f"{row['Team']}: W+D+L ({row['W']+row['D']+row['L']}) != MP ({row['MP']})"
            )

    def test_build_master_from_fallback(self):
        df = build_master_table(FALLBACK_DATA)
        assert len(df) == len(FALLBACK_DATA)
        assert (df["Win%"] >= 0).all()
        assert (df["Win%"] <= 100).all()
