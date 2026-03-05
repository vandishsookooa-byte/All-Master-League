"""
all_master_league.py
====================
Complete, self-contained Python script for the All-Master-League project.
Copy this single file anywhere and run it – no other project files required.

What it does
------------
  1. Attempts to scrape live standings from flashscore.com for 10 top European
     football leagues.
  2. Falls back to a built-in 2024-25 season snapshot when the site is
     unreachable (e.g. in CI / sandboxed environments).
  3. Builds a master table of all teams with Winning Percentage calculated as:

         Win% = Wins / Matches Played × 100

  4. Displays results in five clearly-labelled sections:
       • Full master table     – all leagues and teams, sorted by Win%
       • Per-league standings  – each league in its own block
       • Top-2 per league      – highest Win% teams per league
       • Overall top-10        – cross-league leaderboard with rank numbers
       • Summary statistics    – aggregate numbers and quick-reference table

  5. Saves master_table.csv and top2_per_league.csv in the working directory.

Usage
-----
    pip install pandas tabulate requests beautifulsoup4 lxml
    python all_master_league.py

Dependencies
------------
    pandas, tabulate, requests, beautifulsoup4, lxml
"""

from __future__ import annotations

import sys

import pandas as pd
import requests
from bs4 import BeautifulSoup
from tabulate import tabulate

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

FLASHSCORE_BASE = "https://www.flashscore.com"

LEAGUES: dict[str, str] = {
    "English Premier League":  "/football/england/premier-league/standings/",
    "Spanish La Liga":          "/football/spain/laliga/standings/",
    "German Bundesliga":        "/football/germany/bundesliga/standings/",
    "Italian Serie A":          "/football/italy/serie-a/standings/",
    "French Ligue 1":           "/football/france/ligue-1/standings/",
    "Portuguese Primeira Liga": "/football/portugal/liga-portugal/standings/",
    "Dutch Eredivisie":         "/football/netherlands/eredivisie/standings/",
    "Belgian First Division A": "/football/belgium/jupiler-pro-league/standings/",
    "Turkish Super Lig":        "/football/turkey/super-lig/standings/",
    "Scottish Premiership":     "/football/scotland/premiership/standings/",
}

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# ---------------------------------------------------------------------------
# Terminal colours (disabled automatically when output is not a TTY)
# ---------------------------------------------------------------------------

if sys.stdout.isatty():
    _BOLD  = "\033[1m"
    _CYAN  = "\033[96m"
    _GREEN = "\033[92m"
    _GOLD  = "\033[93m"
    _RESET = "\033[0m"
else:
    _BOLD = _CYAN = _GREEN = _GOLD = _RESET = ""

# ---------------------------------------------------------------------------
# Fallback data – 2024-25 season standings (sampled ~mid-season)
# ---------------------------------------------------------------------------

FALLBACK_DATA: list[dict] = [
    # ── English Premier League ──────────────────────────────────────────────
    {"League": "English Premier League", "Team": "Liverpool",           "MP": 28, "W": 21, "D": 5, "L": 2,  "GF": 66, "GA": 28, "Pts": 68},
    {"League": "English Premier League", "Team": "Arsenal",             "MP": 28, "W": 18, "D": 5, "L": 5,  "GF": 58, "GA": 28, "Pts": 59},
    {"League": "English Premier League", "Team": "Nottm Forest",        "MP": 28, "W": 16, "D": 5, "L": 7,  "GF": 44, "GA": 31, "Pts": 53},
    {"League": "English Premier League", "Team": "Chelsea",             "MP": 28, "W": 15, "D": 6, "L": 7,  "GF": 58, "GA": 43, "Pts": 51},
    {"League": "English Premier League", "Team": "Manchester City",     "MP": 28, "W": 14, "D": 5, "L": 9,  "GF": 52, "GA": 43, "Pts": 47},
    {"League": "English Premier League", "Team": "Newcastle",           "MP": 27, "W": 13, "D": 6, "L": 8,  "GF": 45, "GA": 35, "Pts": 45},
    {"League": "English Premier League", "Team": "Aston Villa",         "MP": 28, "W": 13, "D": 4, "L": 11, "GF": 52, "GA": 45, "Pts": 43},
    {"League": "English Premier League", "Team": "Brighton",            "MP": 28, "W": 11, "D": 8, "L": 9,  "GF": 49, "GA": 46, "Pts": 41},
    {"League": "English Premier League", "Team": "Brentford",           "MP": 28, "W": 11, "D": 7, "L": 10, "GF": 47, "GA": 47, "Pts": 40},
    {"League": "English Premier League", "Team": "Fulham",              "MP": 28, "W": 11, "D": 7, "L": 10, "GF": 42, "GA": 41, "Pts": 40},
    {"League": "English Premier League", "Team": "Tottenham",           "MP": 28, "W": 11, "D": 5, "L": 12, "GF": 49, "GA": 54, "Pts": 38},
    {"League": "English Premier League", "Team": "Manchester Utd",      "MP": 28, "W": 10, "D": 5, "L": 13, "GF": 32, "GA": 42, "Pts": 35},
    {"League": "English Premier League", "Team": "West Ham",            "MP": 28, "W": 9,  "D": 5, "L": 14, "GF": 33, "GA": 52, "Pts": 32},
    {"League": "English Premier League", "Team": "Everton",             "MP": 28, "W": 8,  "D": 8, "L": 12, "GF": 27, "GA": 43, "Pts": 32},
    {"League": "English Premier League", "Team": "Crystal Palace",      "MP": 28, "W": 7,  "D": 9, "L": 12, "GF": 32, "GA": 46, "Pts": 30},
    {"League": "English Premier League", "Team": "Wolves",              "MP": 28, "W": 6,  "D": 8, "L": 14, "GF": 34, "GA": 55, "Pts": 26},
    {"League": "English Premier League", "Team": "Bournemouth",         "MP": 28, "W": 7,  "D": 4, "L": 17, "GF": 36, "GA": 52, "Pts": 25},
    {"League": "English Premier League", "Team": "Ipswich",             "MP": 28, "W": 4,  "D": 9, "L": 15, "GF": 25, "GA": 54, "Pts": 21},
    {"League": "English Premier League", "Team": "Leicester",           "MP": 28, "W": 4,  "D": 8, "L": 16, "GF": 27, "GA": 56, "Pts": 20},
    {"League": "English Premier League", "Team": "Southampton",         "MP": 28, "W": 2,  "D": 5, "L": 21, "GF": 19, "GA": 64, "Pts": 11},
    # ── Spanish La Liga ──────────────────────────────────────────────────────
    {"League": "Spanish La Liga", "Team": "Barcelona",        "MP": 27, "W": 19, "D": 5, "L": 3,  "GF": 67, "GA": 37, "Pts": 62},
    {"League": "Spanish La Liga", "Team": "Real Madrid",      "MP": 27, "W": 18, "D": 4, "L": 5,  "GF": 63, "GA": 36, "Pts": 58},
    {"League": "Spanish La Liga", "Team": "Atletico Madrid",  "MP": 27, "W": 17, "D": 5, "L": 5,  "GF": 54, "GA": 30, "Pts": 56},
    {"League": "Spanish La Liga", "Team": "Athletic Club",    "MP": 27, "W": 14, "D": 5, "L": 8,  "GF": 42, "GA": 29, "Pts": 47},
    {"League": "Spanish La Liga", "Team": "Villarreal",       "MP": 27, "W": 13, "D": 5, "L": 9,  "GF": 47, "GA": 38, "Pts": 44},
    {"League": "Spanish La Liga", "Team": "Real Sociedad",    "MP": 27, "W": 11, "D": 8, "L": 8,  "GF": 43, "GA": 36, "Pts": 41},
    {"League": "Spanish La Liga", "Team": "Girona",           "MP": 27, "W": 12, "D": 4, "L": 11, "GF": 48, "GA": 50, "Pts": 40},
    {"League": "Spanish La Liga", "Team": "Osasuna",          "MP": 27, "W": 11, "D": 6, "L": 10, "GF": 37, "GA": 38, "Pts": 39},
    {"League": "Spanish La Liga", "Team": "Sevilla",          "MP": 27, "W": 9,  "D": 9, "L": 9,  "GF": 35, "GA": 38, "Pts": 36},
    {"League": "Spanish La Liga", "Team": "Betis",            "MP": 27, "W": 9,  "D": 7, "L": 11, "GF": 37, "GA": 43, "Pts": 34},
    {"League": "Spanish La Liga", "Team": "Mallorca",         "MP": 27, "W": 8,  "D": 9, "L": 10, "GF": 26, "GA": 35, "Pts": 33},
    {"League": "Spanish La Liga", "Team": "Celta Vigo",       "MP": 27, "W": 9,  "D": 5, "L": 13, "GF": 34, "GA": 44, "Pts": 32},
    {"League": "Spanish La Liga", "Team": "Leganes",          "MP": 27, "W": 7,  "D": 8, "L": 12, "GF": 22, "GA": 35, "Pts": 29},
    {"League": "Spanish La Liga", "Team": "Getafe",           "MP": 27, "W": 7,  "D": 8, "L": 12, "GF": 24, "GA": 36, "Pts": 29},
    {"League": "Spanish La Liga", "Team": "Rayo Vallecano",   "MP": 27, "W": 6,  "D": 8, "L": 13, "GF": 23, "GA": 37, "Pts": 26},
    {"League": "Spanish La Liga", "Team": "Espanyol",         "MP": 27, "W": 5,  "D": 9, "L": 13, "GF": 24, "GA": 49, "Pts": 24},
    {"League": "Spanish La Liga", "Team": "Alaves",           "MP": 27, "W": 5,  "D": 8, "L": 14, "GF": 21, "GA": 43, "Pts": 23},
    {"League": "Spanish La Liga", "Team": "Valencia",         "MP": 27, "W": 4,  "D": 10, "L": 13, "GF": 22, "GA": 45, "Pts": 22},
    {"League": "Spanish La Liga", "Team": "Valladolid",       "MP": 27, "W": 3,  "D": 7, "L": 17, "GF": 19, "GA": 57, "Pts": 16},
    {"League": "Spanish La Liga", "Team": "Las Palmas",       "MP": 27, "W": 2,  "D": 9, "L": 16, "GF": 19, "GA": 49, "Pts": 15},
    # ── German Bundesliga ───────────────────────────────────────────────────
    {"League": "German Bundesliga", "Team": "Bayern Munich",       "MP": 25, "W": 19, "D": 3, "L": 3,  "GF": 72, "GA": 29, "Pts": 60},
    {"League": "German Bundesliga", "Team": "Eintracht Frankfurt",  "MP": 25, "W": 16, "D": 4, "L": 5,  "GF": 55, "GA": 34, "Pts": 52},
    {"League": "German Bundesliga", "Team": "Bayer Leverkusen",    "MP": 25, "W": 14, "D": 5, "L": 6,  "GF": 59, "GA": 37, "Pts": 47},
    {"League": "German Bundesliga", "Team": "RB Leipzig",          "MP": 25, "W": 14, "D": 4, "L": 7,  "GF": 55, "GA": 41, "Pts": 46},
    {"League": "German Bundesliga", "Team": "Freiburg",            "MP": 25, "W": 11, "D": 7, "L": 7,  "GF": 43, "GA": 37, "Pts": 40},
    {"League": "German Bundesliga", "Team": "Borussia Dortmund",   "MP": 25, "W": 11, "D": 5, "L": 9,  "GF": 50, "GA": 44, "Pts": 38},
    {"League": "German Bundesliga", "Team": "Mainz",               "MP": 25, "W": 10, "D": 7, "L": 8,  "GF": 35, "GA": 35, "Pts": 37},
    {"League": "German Bundesliga", "Team": "Wolfsburg",           "MP": 25, "W": 11, "D": 3, "L": 11, "GF": 38, "GA": 39, "Pts": 36},
    {"League": "German Bundesliga", "Team": "Augsburg",            "MP": 25, "W": 9,  "D": 7, "L": 9,  "GF": 37, "GA": 37, "Pts": 34},
    {"League": "German Bundesliga", "Team": "Borussia M'gladbach", "MP": 25, "W": 10, "D": 3, "L": 12, "GF": 34, "GA": 44, "Pts": 33},
    {"League": "German Bundesliga", "Team": "Werder Bremen",       "MP": 25, "W": 8,  "D": 8, "L": 9,  "GF": 35, "GA": 39, "Pts": 32},
    {"League": "German Bundesliga", "Team": "Stuttgart",           "MP": 25, "W": 8,  "D": 7, "L": 10, "GF": 40, "GA": 43, "Pts": 31},
    {"League": "German Bundesliga", "Team": "Hoffenheim",          "MP": 25, "W": 7,  "D": 7, "L": 11, "GF": 30, "GA": 42, "Pts": 28},
    {"League": "German Bundesliga", "Team": "Heidenheim",          "MP": 25, "W": 6,  "D": 8, "L": 11, "GF": 30, "GA": 45, "Pts": 26},
    {"League": "German Bundesliga", "Team": "Union Berlin",        "MP": 25, "W": 5,  "D": 7, "L": 13, "GF": 27, "GA": 47, "Pts": 22},
    {"League": "German Bundesliga", "Team": "St. Pauli",           "MP": 25, "W": 5,  "D": 5, "L": 15, "GF": 22, "GA": 47, "Pts": 20},
    {"League": "German Bundesliga", "Team": "Bochum",              "MP": 25, "W": 2,  "D": 4, "L": 19, "GF": 19, "GA": 64, "Pts": 10},
    {"League": "German Bundesliga", "Team": "Holstein Kiel",       "MP": 25, "W": 2,  "D": 4, "L": 19, "GF": 22, "GA": 67, "Pts": 10},
    # ── Italian Serie A ─────────────────────────────────────────────────────
    {"League": "Italian Serie A", "Team": "Napoli",          "MP": 27, "W": 18, "D": 4, "L": 5,  "GF": 51, "GA": 24, "Pts": 58},
    {"League": "Italian Serie A", "Team": "Inter Milan",     "MP": 26, "W": 17, "D": 5, "L": 4,  "GF": 58, "GA": 26, "Pts": 56},
    {"League": "Italian Serie A", "Team": "Lazio",           "MP": 27, "W": 15, "D": 6, "L": 6,  "GF": 50, "GA": 33, "Pts": 51},
    {"League": "Italian Serie A", "Team": "Atalanta",        "MP": 26, "W": 15, "D": 5, "L": 6,  "GF": 56, "GA": 32, "Pts": 50},
    {"League": "Italian Serie A", "Team": "Juventus",        "MP": 27, "W": 12, "D": 9, "L": 6,  "GF": 43, "GA": 30, "Pts": 45},
    {"League": "Italian Serie A", "Team": "Fiorentina",      "MP": 26, "W": 12, "D": 7, "L": 7,  "GF": 44, "GA": 31, "Pts": 43},
    {"League": "Italian Serie A", "Team": "AC Milan",        "MP": 27, "W": 11, "D": 7, "L": 9,  "GF": 42, "GA": 37, "Pts": 40},
    {"League": "Italian Serie A", "Team": "Bologna",         "MP": 27, "W": 10, "D": 7, "L": 10, "GF": 39, "GA": 38, "Pts": 37},
    {"League": "Italian Serie A", "Team": "Roma",            "MP": 27, "W": 10, "D": 5, "L": 12, "GF": 34, "GA": 39, "Pts": 35},
    {"League": "Italian Serie A", "Team": "Torino",          "MP": 27, "W": 8,  "D": 9, "L": 10, "GF": 30, "GA": 35, "Pts": 33},
    {"League": "Italian Serie A", "Team": "Udinese",         "MP": 27, "W": 9,  "D": 5, "L": 13, "GF": 27, "GA": 36, "Pts": 32},
    {"League": "Italian Serie A", "Team": "Genoa",           "MP": 27, "W": 7,  "D": 10, "L": 10, "GF": 27, "GA": 38, "Pts": 31},
    {"League": "Italian Serie A", "Team": "Como",            "MP": 27, "W": 7,  "D": 8, "L": 12, "GF": 31, "GA": 47, "Pts": 29},
    {"League": "Italian Serie A", "Team": "Cagliari",        "MP": 27, "W": 6,  "D": 9, "L": 12, "GF": 30, "GA": 47, "Pts": 27},
    {"League": "Italian Serie A", "Team": "Hellas Verona",   "MP": 27, "W": 6,  "D": 9, "L": 12, "GF": 26, "GA": 40, "Pts": 27},
    {"League": "Italian Serie A", "Team": "Parma",           "MP": 27, "W": 6,  "D": 8, "L": 13, "GF": 29, "GA": 46, "Pts": 26},
    {"League": "Italian Serie A", "Team": "Lecce",           "MP": 27, "W": 5,  "D": 10, "L": 12, "GF": 23, "GA": 39, "Pts": 25},
    {"League": "Italian Serie A", "Team": "Empoli",          "MP": 27, "W": 5,  "D": 8, "L": 14, "GF": 16, "GA": 44, "Pts": 23},
    {"League": "Italian Serie A", "Team": "Venezia",         "MP": 27, "W": 4,  "D": 5, "L": 18, "GF": 21, "GA": 52, "Pts": 17},
    {"League": "Italian Serie A", "Team": "Monza",           "MP": 27, "W": 2,  "D": 8, "L": 17, "GF": 18, "GA": 47, "Pts": 14},
    # ── French Ligue 1 ──────────────────────────────────────────────────────
    {"League": "French Ligue 1", "Team": "Paris Saint-Germain", "MP": 26, "W": 19, "D": 4, "L": 3,  "GF": 60, "GA": 20, "Pts": 61},
    {"League": "French Ligue 1", "Team": "Marseille",           "MP": 26, "W": 15, "D": 5, "L": 6,  "GF": 47, "GA": 25, "Pts": 50},
    {"League": "French Ligue 1", "Team": "Monaco",              "MP": 26, "W": 14, "D": 5, "L": 7,  "GF": 53, "GA": 37, "Pts": 47},
    {"League": "French Ligue 1", "Team": "Lille",               "MP": 26, "W": 13, "D": 6, "L": 7,  "GF": 43, "GA": 30, "Pts": 45},
    {"League": "French Ligue 1", "Team": "Lyon",                "MP": 26, "W": 13, "D": 5, "L": 8,  "GF": 42, "GA": 37, "Pts": 44},
    {"League": "French Ligue 1", "Team": "Nice",                "MP": 26, "W": 12, "D": 5, "L": 9,  "GF": 37, "GA": 32, "Pts": 41},
    {"League": "French Ligue 1", "Team": "Lens",                "MP": 26, "W": 10, "D": 8, "L": 8,  "GF": 33, "GA": 31, "Pts": 38},
    {"League": "French Ligue 1", "Team": "Rennes",              "MP": 26, "W": 10, "D": 5, "L": 11, "GF": 33, "GA": 39, "Pts": 35},
    {"League": "French Ligue 1", "Team": "Nantes",              "MP": 26, "W": 9,  "D": 5, "L": 12, "GF": 28, "GA": 35, "Pts": 32},
    {"League": "French Ligue 1", "Team": "Strasbourg",          "MP": 26, "W": 8,  "D": 7, "L": 11, "GF": 34, "GA": 42, "Pts": 31},
    {"League": "French Ligue 1", "Team": "Reims",               "MP": 26, "W": 7,  "D": 8, "L": 11, "GF": 30, "GA": 38, "Pts": 29},
    {"League": "French Ligue 1", "Team": "Toulouse",            "MP": 26, "W": 6,  "D": 9, "L": 11, "GF": 23, "GA": 38, "Pts": 27},
    {"League": "French Ligue 1", "Team": "Brest",               "MP": 26, "W": 7,  "D": 5, "L": 14, "GF": 29, "GA": 42, "Pts": 26},
    {"League": "French Ligue 1", "Team": "Le Havre",            "MP": 26, "W": 6,  "D": 7, "L": 13, "GF": 25, "GA": 41, "Pts": 25},
    {"League": "French Ligue 1", "Team": "Auxerre",             "MP": 26, "W": 6,  "D": 6, "L": 14, "GF": 27, "GA": 47, "Pts": 24},
    {"League": "French Ligue 1", "Team": "Saint-Etienne",       "MP": 26, "W": 4,  "D": 8, "L": 14, "GF": 22, "GA": 47, "Pts": 20},
    {"League": "French Ligue 1", "Team": "Montpellier",         "MP": 26, "W": 2,  "D": 5, "L": 19, "GF": 17, "GA": 59, "Pts": 11},
    {"League": "French Ligue 1", "Team": "Angers",              "MP": 26, "W": 2,  "D": 4, "L": 20, "GF": 13, "GA": 57, "Pts": 10},
    # ── Portuguese Primeira Liga ────────────────────────────────────────────
    {"League": "Portuguese Primeira Liga", "Team": "Sporting CP",       "MP": 24, "W": 18, "D": 4, "L": 2,  "GF": 54, "GA": 15, "Pts": 58},
    {"League": "Portuguese Primeira Liga", "Team": "Benfica",           "MP": 24, "W": 17, "D": 3, "L": 4,  "GF": 57, "GA": 27, "Pts": 54},
    {"League": "Portuguese Primeira Liga", "Team": "Porto",             "MP": 24, "W": 15, "D": 4, "L": 5,  "GF": 49, "GA": 27, "Pts": 49},
    {"League": "Portuguese Primeira Liga", "Team": "Braga",             "MP": 24, "W": 14, "D": 4, "L": 6,  "GF": 43, "GA": 28, "Pts": 46},
    {"League": "Portuguese Primeira Liga", "Team": "Vitoria Guimaraes", "MP": 24, "W": 9,  "D": 8, "L": 7,  "GF": 31, "GA": 29, "Pts": 35},
    {"League": "Portuguese Primeira Liga", "Team": "Santa Clara",       "MP": 24, "W": 9,  "D": 7, "L": 8,  "GF": 28, "GA": 26, "Pts": 34},
    {"League": "Portuguese Primeira Liga", "Team": "Famalicao",         "MP": 24, "W": 7,  "D": 8, "L": 9,  "GF": 23, "GA": 30, "Pts": 29},
    {"League": "Portuguese Primeira Liga", "Team": "Nacional",          "MP": 24, "W": 7,  "D": 6, "L": 11, "GF": 27, "GA": 38, "Pts": 27},
    {"League": "Portuguese Primeira Liga", "Team": "Estoril",           "MP": 24, "W": 7,  "D": 6, "L": 11, "GF": 24, "GA": 36, "Pts": 27},
    {"League": "Portuguese Primeira Liga", "Team": "Casa Pia",          "MP": 24, "W": 6,  "D": 7, "L": 11, "GF": 24, "GA": 36, "Pts": 25},
    {"League": "Portuguese Primeira Liga", "Team": "Moreirense",        "MP": 24, "W": 6,  "D": 5, "L": 13, "GF": 23, "GA": 39, "Pts": 23},
    {"League": "Portuguese Primeira Liga", "Team": "Rio Ave",           "MP": 24, "W": 5,  "D": 7, "L": 12, "GF": 20, "GA": 39, "Pts": 22},
    {"League": "Portuguese Primeira Liga", "Team": "Farense",           "MP": 24, "W": 5,  "D": 6, "L": 13, "GF": 17, "GA": 38, "Pts": 21},
    {"League": "Portuguese Primeira Liga", "Team": "Gil Vicente",       "MP": 24, "W": 4,  "D": 6, "L": 14, "GF": 16, "GA": 38, "Pts": 18},
    {"League": "Portuguese Primeira Liga", "Team": "Estrela Amadora",   "MP": 24, "W": 4,  "D": 5, "L": 15, "GF": 14, "GA": 42, "Pts": 17},
    {"League": "Portuguese Primeira Liga", "Team": "AVS",               "MP": 24, "W": 3,  "D": 6, "L": 15, "GF": 15, "GA": 42, "Pts": 15},
    {"League": "Portuguese Primeira Liga", "Team": "Boavista",          "MP": 24, "W": 4,  "D": 3, "L": 17, "GF": 19, "GA": 48, "Pts": 15},
    {"League": "Portuguese Primeira Liga", "Team": "Arouca",            "MP": 24, "W": 3,  "D": 4, "L": 17, "GF": 16, "GA": 47, "Pts": 13},
    # ── Dutch Eredivisie ────────────────────────────────────────────────────
    {"League": "Dutch Eredivisie", "Team": "Ajax",             "MP": 25, "W": 18, "D": 3, "L": 4,  "GF": 66, "GA": 28, "Pts": 57},
    {"League": "Dutch Eredivisie", "Team": "PSV Eindhoven",    "MP": 25, "W": 17, "D": 4, "L": 4,  "GF": 70, "GA": 23, "Pts": 55},
    {"League": "Dutch Eredivisie", "Team": "AZ Alkmaar",       "MP": 25, "W": 16, "D": 4, "L": 5,  "GF": 56, "GA": 31, "Pts": 52},
    {"League": "Dutch Eredivisie", "Team": "Feyenoord",        "MP": 25, "W": 13, "D": 5, "L": 7,  "GF": 53, "GA": 32, "Pts": 44},
    {"League": "Dutch Eredivisie", "Team": "FC Utrecht",       "MP": 25, "W": 12, "D": 5, "L": 8,  "GF": 40, "GA": 31, "Pts": 41},
    {"League": "Dutch Eredivisie", "Team": "FC Groningen",     "MP": 25, "W": 10, "D": 7, "L": 8,  "GF": 39, "GA": 38, "Pts": 37},
    {"League": "Dutch Eredivisie", "Team": "Twente",           "MP": 25, "W": 10, "D": 5, "L": 10, "GF": 38, "GA": 34, "Pts": 35},
    {"League": "Dutch Eredivisie", "Team": "Go Ahead Eagles",  "MP": 25, "W": 9,  "D": 6, "L": 10, "GF": 38, "GA": 38, "Pts": 33},
    {"League": "Dutch Eredivisie", "Team": "Heerenveen",       "MP": 25, "W": 8,  "D": 6, "L": 11, "GF": 36, "GA": 43, "Pts": 30},
    {"League": "Dutch Eredivisie", "Team": "Almere City",      "MP": 25, "W": 7,  "D": 6, "L": 12, "GF": 31, "GA": 45, "Pts": 27},
    {"League": "Dutch Eredivisie", "Team": "NEC Nijmegen",     "MP": 25, "W": 7,  "D": 4, "L": 14, "GF": 32, "GA": 47, "Pts": 25},
    {"League": "Dutch Eredivisie", "Team": "Fortuna Sittard",  "MP": 25, "W": 6,  "D": 6, "L": 13, "GF": 27, "GA": 44, "Pts": 24},
    {"League": "Dutch Eredivisie", "Team": "Sparta Rotterdam", "MP": 25, "W": 5,  "D": 7, "L": 13, "GF": 29, "GA": 46, "Pts": 22},
    {"League": "Dutch Eredivisie", "Team": "RKC Waalwijk",     "MP": 25, "W": 5,  "D": 4, "L": 16, "GF": 25, "GA": 56, "Pts": 19},
    {"League": "Dutch Eredivisie", "Team": "Willem II",        "MP": 25, "W": 4,  "D": 6, "L": 15, "GF": 27, "GA": 56, "Pts": 18},
    {"League": "Dutch Eredivisie", "Team": "PEC Zwolle",       "MP": 25, "W": 3,  "D": 4, "L": 18, "GF": 22, "GA": 63, "Pts": 13},
    {"League": "Dutch Eredivisie", "Team": "Heracles",         "MP": 25, "W": 3,  "D": 4, "L": 18, "GF": 25, "GA": 65, "Pts": 13},
    {"League": "Dutch Eredivisie", "Team": "NAC Breda",        "MP": 25, "W": 3,  "D": 4, "L": 18, "GF": 21, "GA": 60, "Pts": 13},
    # ── Belgian First Division A ────────────────────────────────────────────
    {"League": "Belgian First Division A", "Team": "Club Brugge",    "MP": 29, "W": 21, "D": 5, "L": 3,  "GF": 71, "GA": 28, "Pts": 68},
    {"League": "Belgian First Division A", "Team": "Anderlecht",     "MP": 29, "W": 18, "D": 5, "L": 6,  "GF": 62, "GA": 37, "Pts": 59},
    {"League": "Belgian First Division A", "Team": "Genk",           "MP": 29, "W": 18, "D": 4, "L": 7,  "GF": 57, "GA": 35, "Pts": 58},
    {"League": "Belgian First Division A", "Team": "Union SG",       "MP": 29, "W": 15, "D": 7, "L": 7,  "GF": 50, "GA": 33, "Pts": 52},
    {"League": "Belgian First Division A", "Team": "Gent",           "MP": 29, "W": 15, "D": 5, "L": 9,  "GF": 52, "GA": 42, "Pts": 50},
    {"League": "Belgian First Division A", "Team": "Westerlo",       "MP": 29, "W": 11, "D": 9, "L": 9,  "GF": 40, "GA": 38, "Pts": 42},
    {"League": "Belgian First Division A", "Team": "Standard Liege", "MP": 29, "W": 11, "D": 7, "L": 11, "GF": 42, "GA": 42, "Pts": 40},
    {"League": "Belgian First Division A", "Team": "Cercle Brugge",  "MP": 29, "W": 10, "D": 9, "L": 10, "GF": 36, "GA": 39, "Pts": 39},
    {"League": "Belgian First Division A", "Team": "Mechelen",       "MP": 29, "W": 10, "D": 5, "L": 14, "GF": 34, "GA": 45, "Pts": 35},
    {"League": "Belgian First Division A", "Team": "Antwerp",        "MP": 29, "W": 9,  "D": 6, "L": 14, "GF": 35, "GA": 44, "Pts": 33},
    {"League": "Belgian First Division A", "Team": "OHL",            "MP": 29, "W": 8,  "D": 6, "L": 15, "GF": 36, "GA": 49, "Pts": 30},
    {"League": "Belgian First Division A", "Team": "Kortrijk",       "MP": 29, "W": 6,  "D": 9, "L": 14, "GF": 26, "GA": 48, "Pts": 27},
    {"League": "Belgian First Division A", "Team": "Charleroi",      "MP": 29, "W": 5,  "D": 9, "L": 15, "GF": 26, "GA": 50, "Pts": 24},
    {"League": "Belgian First Division A", "Team": "Beerschot",      "MP": 29, "W": 5,  "D": 7, "L": 17, "GF": 27, "GA": 57, "Pts": 22},
    {"League": "Belgian First Division A", "Team": "STVV",           "MP": 29, "W": 5,  "D": 4, "L": 20, "GF": 28, "GA": 61, "Pts": 19},
    {"League": "Belgian First Division A", "Team": "Dender",         "MP": 29, "W": 4,  "D": 4, "L": 21, "GF": 20, "GA": 64, "Pts": 16},
    # ── Turkish Super Lig ────────────────────────────────────────────────────
    {"League": "Turkish Super Lig", "Team": "Galatasaray",      "MP": 26, "W": 19, "D": 4, "L": 3,  "GF": 64, "GA": 28, "Pts": 61},
    {"League": "Turkish Super Lig", "Team": "Fenerbahce",       "MP": 26, "W": 18, "D": 4, "L": 4,  "GF": 59, "GA": 26, "Pts": 58},
    {"League": "Turkish Super Lig", "Team": "Besiktas",         "MP": 26, "W": 16, "D": 4, "L": 6,  "GF": 55, "GA": 34, "Pts": 52},
    {"League": "Turkish Super Lig", "Team": "Trabzonspor",      "MP": 26, "W": 13, "D": 5, "L": 8,  "GF": 46, "GA": 35, "Pts": 44},
    {"League": "Turkish Super Lig", "Team": "Basaksehir",       "MP": 26, "W": 12, "D": 5, "L": 9,  "GF": 40, "GA": 32, "Pts": 41},
    {"League": "Turkish Super Lig", "Team": "Sivas Belediyespor","MP": 26, "W": 10, "D": 8, "L": 8,  "GF": 38, "GA": 35, "Pts": 38},
    {"League": "Turkish Super Lig", "Team": "Kasimpasa",        "MP": 26, "W": 10, "D": 5, "L": 11, "GF": 35, "GA": 39, "Pts": 35},
    {"League": "Turkish Super Lig", "Team": "Konyaspor",        "MP": 26, "W": 9,  "D": 7, "L": 10, "GF": 33, "GA": 38, "Pts": 34},
    {"League": "Turkish Super Lig", "Team": "Antalyaspor",      "MP": 26, "W": 9,  "D": 5, "L": 12, "GF": 31, "GA": 43, "Pts": 32},
    {"League": "Turkish Super Lig", "Team": "Alanyaspor",       "MP": 26, "W": 8,  "D": 7, "L": 11, "GF": 30, "GA": 39, "Pts": 31},
    {"League": "Turkish Super Lig", "Team": "Kayserispor",      "MP": 26, "W": 8,  "D": 6, "L": 12, "GF": 27, "GA": 39, "Pts": 30},
    {"League": "Turkish Super Lig", "Team": "Eyupspor",         "MP": 26, "W": 8,  "D": 5, "L": 13, "GF": 30, "GA": 42, "Pts": 29},
    {"League": "Turkish Super Lig", "Team": "Rizespor",         "MP": 26, "W": 6,  "D": 8, "L": 12, "GF": 25, "GA": 41, "Pts": 26},
    {"League": "Turkish Super Lig", "Team": "Gaziantep",        "MP": 26, "W": 6,  "D": 6, "L": 14, "GF": 27, "GA": 47, "Pts": 24},
    {"League": "Turkish Super Lig", "Team": "Hatayspor",        "MP": 26, "W": 6,  "D": 5, "L": 15, "GF": 25, "GA": 52, "Pts": 23},
    {"League": "Turkish Super Lig", "Team": "Bodrumspor",       "MP": 26, "W": 5,  "D": 5, "L": 16, "GF": 22, "GA": 50, "Pts": 20},
    {"League": "Turkish Super Lig", "Team": "Adana Demirspor",  "MP": 26, "W": 4,  "D": 7, "L": 15, "GF": 27, "GA": 50, "Pts": 19},
    {"League": "Turkish Super Lig", "Team": "Samsunspor",       "MP": 26, "W": 4,  "D": 5, "L": 17, "GF": 21, "GA": 55, "Pts": 17},
    # ── Scottish Premiership ─────────────────────────────────────────────────
    {"League": "Scottish Premiership", "Team": "Celtic",       "MP": 27, "W": 22, "D": 2, "L": 3,  "GF": 72, "GA": 21, "Pts": 68},
    {"League": "Scottish Premiership", "Team": "Rangers",      "MP": 27, "W": 17, "D": 5, "L": 5,  "GF": 59, "GA": 30, "Pts": 56},
    {"League": "Scottish Premiership", "Team": "Aberdeen",     "MP": 27, "W": 14, "D": 5, "L": 8,  "GF": 43, "GA": 28, "Pts": 47},
    {"League": "Scottish Premiership", "Team": "Dundee Utd",   "MP": 27, "W": 12, "D": 7, "L": 8,  "GF": 42, "GA": 32, "Pts": 43},
    {"League": "Scottish Premiership", "Team": "Hearts",       "MP": 27, "W": 11, "D": 7, "L": 9,  "GF": 37, "GA": 35, "Pts": 40},
    {"League": "Scottish Premiership", "Team": "Hibernian",    "MP": 27, "W": 10, "D": 6, "L": 11, "GF": 35, "GA": 38, "Pts": 36},
    {"League": "Scottish Premiership", "Team": "Motherwell",   "MP": 27, "W": 10, "D": 5, "L": 12, "GF": 36, "GA": 45, "Pts": 35},
    {"League": "Scottish Premiership", "Team": "Kilmarnock",   "MP": 27, "W": 9,  "D": 5, "L": 13, "GF": 32, "GA": 41, "Pts": 32},
    {"League": "Scottish Premiership", "Team": "St Mirren",    "MP": 27, "W": 7,  "D": 6, "L": 14, "GF": 26, "GA": 40, "Pts": 27},
    {"League": "Scottish Premiership", "Team": "St Johnstone", "MP": 27, "W": 6,  "D": 7, "L": 14, "GF": 23, "GA": 44, "Pts": 25},
    {"League": "Scottish Premiership", "Team": "Ross County",  "MP": 27, "W": 5,  "D": 7, "L": 15, "GF": 22, "GA": 53, "Pts": 22},
    {"League": "Scottish Premiership", "Team": "Dundee FC",    "MP": 27, "W": 4,  "D": 6, "L": 17, "GF": 22, "GA": 52, "Pts": 18},
]

# ---------------------------------------------------------------------------
# Scraping helpers
# ---------------------------------------------------------------------------

def _fetch_standings_from_web(league_name: str, path: str) -> list[dict] | None:
    """Try to scrape a single league standings table from flashscore.com.

    Flashscore renders standings via JavaScript; the initial HTML response
    contains the table rows inside ``<div class="ui-table__row">``.  Returns
    a list of row dicts on success, or *None* if the page cannot be parsed.
    """
    url = FLASHSCORE_BASE + path
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"  [WARN] Could not fetch {league_name}: {exc}", file=sys.stderr)
        return None

    soup = BeautifulSoup(resp.text, "lxml")

    rows = soup.select("div.ui-table__row")
    if not rows:
        rows = soup.select("div.table__row")
    if not rows:
        print(
            f"  [WARN] No standings rows found for {league_name} "
            "(page may require JavaScript).",
            file=sys.stderr,
        )
        return None

    records: list[dict] = []
    for row in rows:
        cells = row.select("span.table__cell--value, div.table__cell")
        if len(cells) < 8:
            continue
        try:
            name_node = row.select_one("span.team__name, a.tableCellParticipant__name")
            if name_node is None:
                continue
            goals_text  = cells[4].get_text(strip=True)
            goals_parts = goals_text.split(":")
            if len(goals_parts) != 2:
                continue
            records.append(
                {
                    "League": league_name,
                    "Team":   name_node.get_text(strip=True),
                    "MP":  int(cells[0].get_text(strip=True)),
                    "W":   int(cells[1].get_text(strip=True)),
                    "D":   int(cells[2].get_text(strip=True)),
                    "L":   int(cells[3].get_text(strip=True)),
                    "GF":  int(goals_parts[0]),
                    "GA":  int(goals_parts[1]),
                    "Pts": int(cells[7].get_text(strip=True)),
                }
            )
        except (ValueError, IndexError, AttributeError):
            continue

    return records if records else None


def fetch_all_standings() -> list[dict]:
    """Try to scrape flashscore.com; fall back to static snapshot on failure."""
    all_records: list[dict] = []

    print("Attempting to fetch live data from flashscore.com …")
    any_live = False
    for league_name, path in LEAGUES.items():
        rows = _fetch_standings_from_web(league_name, path)
        if rows:
            all_records.extend(rows)
            print(f"  ✓ Fetched {len(rows)} teams for {league_name}")
            any_live = True
        else:
            print(f"  ✗ Could not fetch {league_name}")

    if not any_live:
        print(
            "\nFlashscore.com is unreachable in this environment.\n"
            "Using built-in 2024-25 season standings snapshot instead.\n"
        )
        return FALLBACK_DATA

    return all_records

# ---------------------------------------------------------------------------
# Data processing
# ---------------------------------------------------------------------------

def build_master_table(records: list[dict]) -> pd.DataFrame:
    """Build the master DataFrame and compute Winning Percentage.

    Win% = Wins / Matches Played × 100  (rounded to 2 dp)
    League Rank = rank within each league by Win% (highest = 1)
    """
    df = pd.DataFrame(records)

    df["Win%"] = (df["W"] / df["MP"] * 100).round(2)

    df["League Rank"] = (
        df.groupby("League")["Win%"]
        .rank(method="min", ascending=False)
        .astype(int)
    )

    df = df.sort_values(
        ["League", "Win%"],
        ascending=[True, False],
    ).reset_index(drop=True)

    return df


def get_top2_per_league(master: pd.DataFrame) -> pd.DataFrame:
    """Return the top-2 teams per league ranked by Win%."""
    top2 = (
        master.groupby("League", sort=False)
        # include_groups=False (pandas ≥ 2.2): exclude the grouping column
        # from the lambda's DataFrame, avoiding a deprecated FutureWarning.
        .apply(lambda g: g.nlargest(2, "Win%"), include_groups=False)
        .reset_index(level=0)
        .reset_index(drop=True)
    )
    top2 = top2[["League", "Team", "MP", "W", "D", "L", "GF", "GA", "Pts", "Win%"]]
    top2 = top2.sort_values(
        ["League", "Win%"], ascending=[True, False]
    ).reset_index(drop=True)
    return top2

# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def _header(text: str, char: str = "=") -> None:
    border = char * (len(text) + 4)
    print(f"\n{_BOLD}{_CYAN}{border}{_RESET}")
    print(f"{_BOLD}{_CYAN}  {text}  {_RESET}")
    print(f"{_BOLD}{_CYAN}{border}{_RESET}")


def _subheader(text: str) -> None:
    print(f"\n{_BOLD}{_GOLD}── {text} ──{_RESET}")


def _table(df: pd.DataFrame) -> None:
    print(tabulate(df, headers="keys", tablefmt="rounded_outline", showindex=False))

# ---------------------------------------------------------------------------
# View sections
# ---------------------------------------------------------------------------

def view_master_table(master: pd.DataFrame) -> None:
    """Print the complete master table (all leagues, all teams)."""
    cols = ["League", "Team", "MP", "W", "D", "L", "GF", "GA", "Pts", "Win%", "League Rank"]
    _header("FULL MASTER TABLE  –  all leagues, sorted by League → Win%")
    _table(master[cols])


def view_per_league(master: pd.DataFrame) -> None:
    """Print each league's standings as its own clearly-labelled block."""
    _header("PER-LEAGUE STANDINGS")
    cols = ["Team", "MP", "W", "D", "L", "GF", "GA", "Pts", "Win%", "League Rank"]
    for league in sorted(master["League"].unique()):
        _subheader(league)
        subset = master[master["League"] == league][cols].reset_index(drop=True)
        _table(subset)


def view_top2(top2: pd.DataFrame) -> None:
    """Print the top-2 teams per league ranked by Winning Percentage."""
    _header("TOP-2 TEAMS PER LEAGUE  –  ranked by Winning Percentage")
    _table(top2)


def view_overall_top10(master: pd.DataFrame) -> None:
    """Print the global top-10 teams by Win% with 1-based rank numbers."""
    _header("OVERALL TOP-10 TEAMS  –  best Win% across all leagues")
    cols = ["League", "Team", "MP", "W", "D", "L", "Pts", "Win%"]
    top10 = master.nlargest(10, "Win%")[cols].reset_index(drop=True)
    top10.index = top10.index + 1
    top10.index.name = "Rank"
    print(tabulate(top10, headers="keys", tablefmt="rounded_outline"))


def view_summary(master: pd.DataFrame, top2: pd.DataFrame) -> None:
    """Print aggregate statistics and a top-2 quick-reference table."""
    _header("SUMMARY STATISTICS")

    n_leagues  = master["League"].nunique()
    n_teams    = len(master)
    avg_win    = master["Win%"].mean()
    max_win    = master["Win%"].max()
    min_win    = master["Win%"].min()
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
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the full pipeline and display every result section."""

    print(f"{_BOLD}{'=' * 60}{_RESET}")
    print(f"{_BOLD}  ALL-MASTER-LEAGUE  –  Full Results{_RESET}")
    print(f"{_BOLD}{'=' * 60}{_RESET}")
    print(f"\nLeagues in scope: {', '.join(LEAGUES.keys())}\n")

    # ── Step 1: fetch data ─────────────────────────────────────────────────
    records = fetch_all_standings()

    # ── Step 2: build tables ───────────────────────────────────────────────
    master = build_master_table(records)
    top2   = get_top2_per_league(master)

    # ── Step 3: display all results ────────────────────────────────────────
    view_master_table(master)
    view_per_league(master)
    view_top2(top2)
    view_overall_top10(master)
    view_summary(master, top2)

    # ── Step 4: save CSVs ──────────────────────────────────────────────────
    display_cols  = ["League", "Team", "MP", "W", "D", "L", "GF", "GA", "Pts", "Win%", "League Rank"]
    master_path   = "master_table.csv"
    top2_path     = "top2_per_league.csv"
    master[display_cols].to_csv(master_path, index=False)
    top2.to_csv(top2_path, index=False)

    print(f"\n{_GREEN}✓ Results saved:{_RESET}")
    print(f"    {master_path}   (all {len(master)} teams)")
    print(f"    {top2_path}  ({len(top2)} top-2 entries)")


if __name__ == "__main__":
    main()
