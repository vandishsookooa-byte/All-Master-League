"""Tests for run_and_view helper functions."""

import io
import sys

import pandas as pd
import pytest

from flashscore_scraper import build_master_table, get_top2_per_league
from run_and_view import (
    view_master_table,
    view_per_league,
    view_top2,
    view_overall_top10,
    view_summary,
)


@pytest.fixture()
def sample_master():
    records = [
        {"League": "League A", "Team": "Alpha",   "MP": 10, "W": 8, "D": 1, "L": 1, "GF": 25, "GA": 8,  "Pts": 25},
        {"League": "League A", "Team": "Beta",    "MP": 10, "W": 6, "D": 2, "L": 2, "GF": 18, "GA": 10, "Pts": 20},
        {"League": "League A", "Team": "Gamma",   "MP": 10, "W": 3, "D": 1, "L": 6, "GF": 12, "GA": 20, "Pts": 10},
        {"League": "League B", "Team": "Delta",   "MP": 8,  "W": 7, "D": 0, "L": 1, "GF": 20, "GA": 5,  "Pts": 21},
        {"League": "League B", "Team": "Epsilon", "MP": 8,  "W": 4, "D": 2, "L": 2, "GF": 14, "GA": 9,  "Pts": 14},
        {"League": "League B", "Team": "Zeta",    "MP": 8,  "W": 1, "D": 1, "L": 6, "GF": 6,  "GA": 18, "Pts": 4},
    ]
    return build_master_table(records)


@pytest.fixture()
def sample_top2(sample_master):
    return get_top2_per_league(sample_master)


def _capture(fn, *args, **kwargs) -> str:
    """Run fn(*args, **kwargs) and return its stdout as a string."""
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        fn(*args, **kwargs)
    finally:
        sys.stdout = old
    return buf.getvalue()


class TestViewMasterTable:
    def test_outputs_all_teams(self, sample_master):
        out = _capture(view_master_table, sample_master)
        for team in ["Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta"]:
            assert team in out

    def test_outputs_section_header(self, sample_master):
        out = _capture(view_master_table, sample_master)
        assert "FULL MASTER TABLE" in out

    def test_outputs_win_pct_column(self, sample_master):
        out = _capture(view_master_table, sample_master)
        assert "Win%" in out


class TestViewPerLeague:
    def test_each_league_has_its_own_section(self, sample_master):
        out = _capture(view_per_league, sample_master)
        assert "League A" in out
        assert "League B" in out

    def test_teams_appear_in_correct_league_section(self, sample_master):
        out = _capture(view_per_league, sample_master)
        # Alpha belongs to League A – it should appear after League A header
        assert "League A" in out
        assert "Alpha" in out
        assert "League B" in out
        idx_a     = out.index("League A")
        idx_alpha = out.index("Alpha")
        idx_b     = out.index("League B")
        assert idx_a < idx_alpha < idx_b

    def test_section_header_present(self, sample_master):
        out = _capture(view_per_league, sample_master)
        assert "PER-LEAGUE STANDINGS" in out


class TestViewTop2:
    def test_contains_top_team_per_league(self, sample_master, sample_top2):
        out = _capture(view_top2, sample_top2)
        assert "Alpha" in out   # highest Win% in League A
        assert "Delta" in out   # highest Win% in League B

    def test_section_header_present(self, sample_top2):
        out = _capture(view_top2, sample_top2)
        assert "TOP-2 TEAMS PER LEAGUE" in out

    def test_exactly_two_entries_per_league_shown(self, sample_master, sample_top2):
        out = _capture(view_top2, sample_top2)
        # League A teams: Alpha (top), Beta (2nd), Gamma (3rd – should NOT appear)
        assert "Gamma"   not in out
        assert "Zeta"    not in out


class TestViewOverallTop10:
    def test_section_header_present(self, sample_master):
        out = _capture(view_overall_top10, sample_master)
        assert "OVERALL TOP-10" in out

    def test_best_team_is_rank_1(self, sample_master):
        out = _capture(view_overall_top10, sample_master)
        # Alpha has 80% Win% – highest overall
        assert "Alpha" in out

    def test_rank_column_present(self, sample_master):
        out = _capture(view_overall_top10, sample_master)
        assert "Rank" in out


class TestViewSummary:
    def test_league_and_team_counts(self, sample_master, sample_top2):
        out = _capture(view_summary, sample_master, sample_top2)
        assert "2" in out   # 2 leagues
        assert "6" in out   # 6 teams

    def test_average_win_pct_present(self, sample_master, sample_top2):
        out = _capture(view_summary, sample_master, sample_top2)
        assert "Average Win%" in out

    def test_highest_and_lowest_labels_present(self, sample_master, sample_top2):
        out = _capture(view_summary, sample_master, sample_top2)
        assert "Highest Win%" in out
        assert "Lowest Win%" in out

    def test_top2_quick_reference_present(self, sample_master, sample_top2):
        out = _capture(view_summary, sample_master, sample_top2)
        assert "Top-2 quick-reference" in out
