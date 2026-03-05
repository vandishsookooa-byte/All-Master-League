# All-Master-League

Reads league standings from **flashscore.com**, builds a master table of all
teams across all leagues, and ranks the **top-2 teams per league** by
*Winning Percentage*.

---

## What it does

1. **Fetches data** – tries to scrape live standings from flashscore.com.  
   If the site is unreachable (e.g. network restrictions) it falls back to a
   bundled snapshot of the **2024-25 season** standings for 10 major leagues.

2. **Builds a master table** – all teams with columns:  
   `League | Team | MP | W | D | L | GF | GA | Pts | Win% | League Rank`

3. **Calculates Winning Percentage**  
   ```
   Win%  =  Wins / Matches Played  ×  100
   ```

4. **Selects the top-2 teams per league** ranked by Win%.

5. **Prints results** and saves two CSV files:
   - `master_table.csv`   – full standings for all leagues
   - `top2_per_league.csv` – top-2 teams per league

---

## Leagues covered

| League | Country |
|--------|---------|
| English Premier League | England |
| Spanish La Liga | Spain |
| German Bundesliga | Germany |
| Italian Serie A | Italy |
| French Ligue 1 | France |
| Portuguese Primeira Liga | Portugal |
| Dutch Eredivisie | Netherlands |
| Belgian First Division A | Belgium |
| Turkish Super Lig | Turkey |
| Scottish Premiership | Scotland |

---

## Quick start

### Option A – single self-contained file (recommended)

```bash
pip install pandas tabulate requests beautifulsoup4 lxml
python all_master_league.py
```

`all_master_league.py` is the **complete, standalone Python program**.  It
contains every line of code needed – scraping helpers, fallback data, data
processing, and display logic – in a single file with no project-local imports.

### Option B – modular pipeline

```bash
# Install dependencies
pip install -r requirements.txt

# Run and view ALL results
python run_and_view.py

# Run the core scraper/data module only
python flashscore_scraper.py
```

### Run tests

```bash
python -m pytest test_all_master_league.py test_run_and_view.py test_flashscore_scraper.py -v
```

### What each script displays

| Section | Description |
|---------|-------------|
| Full master table | Every team in every league sorted by Win% |
| Per-league standings | One block per league with full standings |
| Top-2 per league | Highest two Win% teams per league |
| Overall top-10 | Cross-league leaderboard with rank numbers |
| Summary statistics | League/team counts, avg/max/min Win%, best & worst team |

---

## Sample output (top-2 per league)

```
League                    | Team                 | MP | W  | Win%
--------------------------|----------------------|----|----|---------
Belgian First Division A  | Club Brugge          | 29 | 21 | 72.41
Belgian First Division A  | Anderlecht           | 29 | 18 | 62.07
Dutch Eredivisie          | Ajax                 | 25 | 18 | 72.00
Dutch Eredivisie          | PSV Eindhoven        | 25 | 17 | 68.00
English Premier League    | Liverpool            | 28 | 21 | 75.00
English Premier League    | Arsenal              | 28 | 18 | 64.29
French Ligue 1            | Paris Saint-Germain  | 26 | 19 | 73.08
French Ligue 1            | Marseille            | 26 | 15 | 57.69
German Bundesliga         | Bayern Munich        | 25 | 19 | 76.00
German Bundesliga         | Eintracht Frankfurt  | 25 | 16 | 64.00
Italian Serie A           | Napoli               | 27 | 18 | 66.67
Italian Serie A           | Inter Milan          | 26 | 17 | 65.38
Portuguese Primeira Liga  | Sporting CP          | 24 | 18 | 75.00
Portuguese Primeira Liga  | Benfica              | 24 | 17 | 70.83
Scottish Premiership      | Celtic               | 27 | 22 | 81.48
Scottish Premiership      | Rangers              | 27 | 17 | 62.96
Spanish La Liga           | Barcelona            | 27 | 19 | 70.37
Spanish La Liga           | Real Madrid          | 27 | 18 | 66.67
Turkish Super Lig         | Galatasaray          | 26 | 19 | 73.08
Turkish Super Lig         | Fenerbahce           | 26 | 18 | 69.23
```
