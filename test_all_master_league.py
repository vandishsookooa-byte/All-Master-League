"""Tests for all_master_league.py – the self-contained single-file version."""

import io
import sys

import pandas as pd
import pytest

from all_master_league import (
    FALLBACK_DATA,
    LEAGUES,
    build_master_table,
    get_top2_per_league,
    view_master_table,
    view_per_league,
    view_top2,
    view_overall_top10,
    view_summary,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_records():
    return [
        {"League": "League A", "Team": "Alpha",   "MP": 10, "W": 8, "D": 1, "L": 1, "GF": 25, "GA": 8,  "Pts": 25},
        {"League": "League A", "Team": "Beta",    "MP": 10, "W": 6, "D": 2, "L": 2, "GF": 18, "GA": 10, "Pts": 20},
        {"League": "League A", "Team": "Gamma",   "MP": 10, "W": 3, "D": 1, "L": 6, "GF": 12, "GA": 20, "Pts": 10},
        {"League": "League B", "Team": "Delta",   "MP": 8,  "W": 7, "D": 0, "L": 1, "GF": 20, "GA": 5,  "Pts": 21},
        {"League": "League B", "Team": "Epsilon", "MP": 8,  "W": 4, "D": 2, "L": 2, "GF": 14, "GA": 9,  "Pts": 14},
        {"League": "League B", "Team": "Zeta",    "MP": 8,  "W": 1, "D": 1, "L": 6, "GF": 6,  "GA": 18, "Pts": 4},
    ]


@pytest.fixture()
def sample_master(sample_records):
    return build_master_table(sample_records)


@pytest.fixture()
def sample_top2(sample_master):
    return get_top2_per_league(sample_master)


def _capture_stdout(fn, *args, **kwargs) -> str:
    buf = io.StringIO()
    old, sys.stdout = sys.stdout, buf
    try:
        fn(*args, **kwargs)
    finally:
        sys.stdout = old
    return buf.getvalue()


# ---------------------------------------------------------------------------
# build_master_table
# ---------------------------------------------------------------------------

class TestBuildMasterTable:
    def test_returns_dataframe(self, sample_records):
        assert isinstance(build_master_table(sample_records), pd.DataFrame)

    def test_win_percentage_calculation(self, sample_records):
        df = build_master_table(sample_records)
        alpha = df.loc[df["Team"] == "Alpha"].iloc[0]
        assert alpha["Win%"] == pytest.approx(80.0)

    def test_win_percentage_zero_when_no_wins(self):
        records = [{"League": "X", "Team": "T", "MP": 5, "W": 0, "D": 3, "L": 2, "GF": 2, "GA": 5, "Pts": 3}]
        df = build_master_table(records)
        assert df.iloc[0]["Win%"] == 0.0

    def test_all_required_columns_present(self, sample_records):
        df = build_master_table(sample_records)
        for col in ("League", "Team", "MP", "W", "D", "L", "GF", "GA", "Pts", "Win%", "League Rank"):
            assert col in df.columns

    def test_sorted_by_league_then_win_pct_desc(self, sample_records):
        df = build_master_table(sample_records).reset_index(drop=True)
        for league in df["League"].unique():
            subset = df[df["League"] == league]["Win%"].tolist()
            assert subset == sorted(subset, reverse=True)

    def test_league_rank_1_is_highest_win_pct(self, sample_records):
        df = build_master_table(sample_records)
        for league in df["League"].unique():
            top = df[df["League"] == league].sort_values("Win%", ascending=False).iloc[0]
            assert top["League Rank"] == 1


# ---------------------------------------------------------------------------
# get_top2_per_league
# ---------------------------------------------------------------------------

class TestGetTop2PerLeague:
    def test_returns_exactly_2_per_league(self, sample_master):
        top2 = get_top2_per_league(sample_master)
        for league in top2["League"].unique():
            assert len(top2[top2["League"] == league]) == 2

    def test_top2_are_highest_win_pct(self, sample_master):
        top2 = get_top2_per_league(sample_master)
        for league in top2["League"].unique():
            top_teams = set(top2[top2["League"] == league]["Team"])
            expected  = set(sample_master[sample_master["League"] == league].nlargest(2, "Win%")["Team"])
            assert top_teams == expected

    def test_covers_all_leagues(self, sample_master):
        top2 = get_top2_per_league(sample_master)
        assert set(top2["League"].unique()) == set(sample_master["League"].unique())


# ---------------------------------------------------------------------------
# View helpers
# ---------------------------------------------------------------------------

class TestViewMasterTable:
    def test_all_teams_present(self, sample_master):
        out = _capture_stdout(view_master_table, sample_master)
        for team in ["Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta"]:
            assert team in out

    def test_section_header(self, sample_master):
        out = _capture_stdout(view_master_table, sample_master)
        assert "FULL MASTER TABLE" in out

    def test_win_pct_column(self, sample_master):
        out = _capture_stdout(view_master_table, sample_master)
        assert "Win%" in out


class TestViewPerLeague:
    def test_each_league_has_section(self, sample_master):
        out = _capture_stdout(view_per_league, sample_master)
        assert "League A" in out
        assert "League B" in out

    def test_teams_in_correct_section(self, sample_master):
        out = _capture_stdout(view_per_league, sample_master)
        assert "League A" in out and "Alpha" in out and "League B" in out
        idx_a     = out.index("League A")
        idx_alpha = out.index("Alpha")
        idx_b     = out.index("League B")
        assert idx_a < idx_alpha < idx_b

    def test_header_present(self, sample_master):
        out = _capture_stdout(view_per_league, sample_master)
        assert "PER-LEAGUE STANDINGS" in out


class TestViewTop2:
    def test_top_team_per_league_shown(self, sample_master, sample_top2):
        out = _capture_stdout(view_top2, sample_top2)
        assert "Alpha" in out
        assert "Delta" in out

    def test_third_place_teams_excluded(self, sample_master, sample_top2):
        out = _capture_stdout(view_top2, sample_top2)
        assert "Gamma" not in out
        assert "Zeta"  not in out

    def test_header_present(self, sample_top2):
        out = _capture_stdout(view_top2, sample_top2)
        assert "TOP-2 TEAMS PER LEAGUE" in out


class TestViewOverallTop10:
    def test_header_present(self, sample_master):
        out = _capture_stdout(view_overall_top10, sample_master)
        assert "OVERALL TOP-10" in out

    def test_best_team_shown(self, sample_master):
        out = _capture_stdout(view_overall_top10, sample_master)
        assert "Alpha" in out

    def test_rank_column(self, sample_master):
        out = _capture_stdout(view_overall_top10, sample_master)
        assert "Rank" in out


class TestViewSummary:
    def test_counts(self, sample_master, sample_top2):
        out = _capture_stdout(view_summary, sample_master, sample_top2)
        assert "2" in out  # 2 leagues
        assert "6" in out  # 6 teams

    def test_stat_labels(self, sample_master, sample_top2):
        out = _capture_stdout(view_summary, sample_master, sample_top2)
        assert "Average Win%" in out
        assert "Highest Win%" in out
        assert "Lowest Win%"  in out

    def test_quick_reference(self, sample_master, sample_top2):
        out = _capture_stdout(view_summary, sample_master, sample_top2)
        assert "Top-2 quick-reference" in out


# ---------------------------------------------------------------------------
# Fallback data & LEAGUES constant
# ---------------------------------------------------------------------------

class TestFallbackData:
    def test_has_all_ten_leagues(self):
        fallback_leagues = {r["League"] for r in FALLBACK_DATA}
        assert fallback_leagues == set(LEAGUES.keys())

    def test_win_draw_loss_sums_to_mp(self):
        for row in FALLBACK_DATA:
            assert row["W"] + row["D"] + row["L"] == row["MP"], (
                f"{row['Team']}: W+D+L != MP"
            )

    def test_build_master_from_fallback(self):
        df = build_master_table(FALLBACK_DATA)
        assert len(df) == len(FALLBACK_DATA)
        assert (df["Win%"] >= 0).all()
        assert (df["Win%"] <= 100).all()

    def test_ten_leagues_configured(self):
        assert len(LEAGUES) == 10
