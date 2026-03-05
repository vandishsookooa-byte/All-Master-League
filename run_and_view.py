"""
run_and_view.py
===============
Single entry-point script that runs the full All-Master-League pipeline and
displays **all** results in a structured, easy-to-read format.

What it shows
-------------
  1. Data-source notice  (live scrape vs. built-in snapshot)
  2. Full master table   (every team in every league, sorted by Win%)
  3. Per-league breakdown (each league gets its own standings section)
  4. Top-2 per league    (ranked by Winning Percentage)
  5. Overall top-10      (best Win% across all leagues)
  6. Summary statistics  (league count, team count, avg Win%)
  7. CSV save notice

Usage
-----
    python run_and_view.py
"""

from __future__ import annotations

import sys

import pandas as pd
from tabulate import tabulate

# Re-use all logic from the scraper module
from flashscore_scraper import (
    LEAGUES,
    build_master_table,
    fetch_all_standings,
    get_top2_per_league,
)

# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

_BOLD  = "\033[1m"
_CYAN  = "\033[96m"
_GREEN = "\033[92m"
_GOLD  = "\033[93m"
_RESET = "\033[0m"

# Fall back to plain text when colours are not supported (e.g. piped output)
if not sys.stdout.isatty():
    _BOLD = _CYAN = _GREEN = _GOLD = _RESET = ""


def _header(text: str, char: str = "=") -> None:
    """Print a prominently bordered section header."""
    border = char * (len(text) + 4)
    print(f"\n{_BOLD}{_CYAN}{border}{_RESET}")
    print(f"{_BOLD}{_CYAN}  {text}  {_RESET}")
    print(f"{_BOLD}{_CYAN}{border}{_RESET}")


def _subheader(text: str) -> None:
    """Print a lighter sub-section header."""
    print(f"\n{_BOLD}{_GOLD}── {text} ──{_RESET}")


def _table(df: pd.DataFrame) -> None:
    """Print a DataFrame as a rounded ASCII table."""
    print(tabulate(df, headers="keys", tablefmt="rounded_outline", showindex=False))


# ---------------------------------------------------------------------------
# View sections
# ---------------------------------------------------------------------------

def view_master_table(master: pd.DataFrame) -> None:
    """Section 1 – print the complete master table."""
    cols = ["League", "Team", "MP", "W", "D", "L", "GF", "GA", "Pts", "Win%", "League Rank"]
    _header("FULL MASTER TABLE  –  all leagues, sorted by League → Win%")
    _table(master[cols])


def view_per_league(master: pd.DataFrame) -> None:
    """Section 2 – print each league's standings as a separate block."""
    _header("PER-LEAGUE STANDINGS")
    cols = ["Team", "MP", "W", "D", "L", "GF", "GA", "Pts", "Win%", "League Rank"]
    for league in sorted(master["League"].unique()):
        _subheader(league)
        subset = master[master["League"] == league][cols].reset_index(drop=True)
        _table(subset)


def view_top2(top2: pd.DataFrame) -> None:
    """Section 3 – print top-2 per league."""
    _header("TOP-2 TEAMS PER LEAGUE  –  ranked by Winning Percentage")
    _table(top2)


def view_overall_top10(master: pd.DataFrame) -> None:
    """Section 4 – print the global top-10 teams by Win%."""
    _header("OVERALL TOP-10 TEAMS  –  best Win% across all leagues")
    cols = ["League", "Team", "MP", "W", "D", "L", "Pts", "Win%"]
    top10 = master.nlargest(10, "Win%")[cols].reset_index(drop=True)
    top10.index = top10.index + 1          # 1-based rank
    top10.index.name = "Rank"
    print(tabulate(top10, headers="keys", tablefmt="rounded_outline"))


def view_summary(master: pd.DataFrame, top2: pd.DataFrame) -> None:
    """Section 5 – print aggregate statistics."""
    _header("SUMMARY STATISTICS")

    n_leagues = master["League"].nunique()
    n_teams   = len(master)
    avg_win   = master["Win%"].mean()
    max_win   = master["Win%"].max()
    min_win   = master["Win%"].min()

    best_team  = master.loc[master["Win%"].idxmax(), "Team"]
    best_league = master.loc[master["Win%"].idxmax(), "League"]
    worst_team = master.loc[master["Win%"].idxmin(), "Team"]

    lines = [
        ("Leagues covered",          str(n_leagues)),
        ("Total teams",               str(n_teams)),
        ("Average Win% (all teams)",  f"{avg_win:.2f}%"),
        ("Highest Win%",              f"{max_win:.2f}%  →  {best_team} ({best_league})"),
        ("Lowest Win%",               f"{min_win:.2f}%  →  {worst_team}"),
    ]

    width = max(len(label) for label, _ in lines)
    for label, value in lines:
        print(f"  {_BOLD}{label:<{width}}{_RESET}  :  {value}")

    _subheader("Top-2 quick-reference")
    compact = top2[["League", "Team", "Win%"]].copy()
    compact["Win%"] = compact["Win%"].map(lambda x: f"{x:.2f}%")
    _table(compact)


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def run() -> None:
    """Execute the full pipeline and display every result section."""

    print(f"{_BOLD}{'=' * 60}{_RESET}")
    print(f"{_BOLD}  ALL-MASTER-LEAGUE  –  Run & View All Results{_RESET}")
    print(f"{_BOLD}{'=' * 60}{_RESET}")
    print(f"\nLeagues in scope: {', '.join(LEAGUES.keys())}\n")

    # ── 1. Fetch data ──────────────────────────────────────────────────────
    records = fetch_all_standings()
    master  = build_master_table(records)
    top2    = get_top2_per_league(master)

    # ── 2. Display all sections ────────────────────────────────────────────
    view_master_table(master)
    view_per_league(master)
    view_top2(top2)
    view_overall_top10(master)
    view_summary(master, top2)

    # ── 3. Save CSVs ──────────────────────────────────────────────────────
    display_cols = ["League", "Team", "MP", "W", "D", "L", "GF", "GA", "Pts", "Win%", "League Rank"]
    master_path = "master_table.csv"
    top2_path   = "top2_per_league.csv"
    master[display_cols].to_csv(master_path, index=False)
    top2.to_csv(top2_path, index=False)

    print(f"\n{_GREEN}✓ Results saved:{_RESET}")
    print(f"    {master_path}   (all {len(master)} teams)")
    print(f"    {top2_path}  ({len(top2)} top-2 entries)")


if __name__ == "__main__":
    run()
