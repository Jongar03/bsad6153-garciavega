# Milestone 2 submission guide

## Remaining query review

Read this alongside `db/queries.sql` before checking the pull request's review box.

- Queries 1 and 2 join a match's home or away team ID to `team`. `FILTER` counts only wins, `GROUP BY` produces one total per team, and `ORDER BY` puts the largest counts first. `FT` selects finished games; the season filter limits the saved seasons. These are totals, not win rates.
- Query 3 joins `team` twice, naming the copies `home` and `away`. Its two alternatives include Arsenal–Liverpool and Liverpool–Arsenal. It lists each match in date order.
- Query 4 uses `WITH` to name intermediate results. `UNION ALL` gives each match one row for the home team and one for the away team. `ROW_NUMBER` numbers each team's games from newest to oldest, and `game_number <= 5` keeps its latest five. `SUM` adds its goals. The `CASE` returns an unknown total if any selected score is missing, rather than silently reporting a partial total. Different teams may have different date windows.
- Query 5 first selects dates from 1 May 2025 through the end of May in UTC. It combines home and away goals, then counts matches and sums goals for each team. Brentford and Brighton both scored 10, but played five and four games respectively. Alphabetical order breaks the displayed tie; it does not make Brentford a better scorer.

These queries only read data. They contain no inserts, updates, or deletions.

## Five-minute screencast plan

Use your own words. Show the actual screens while explaining them. Keep `.env`, passwords, and connection settings closed. Prepare the rendered diagram on GitHub, Supabase Table Editor, SQL Editor, and PowerShell before recording.

### 0:00–1:15 — Diagram

Show `docs/schema.md` rendered on GitHub.

Suggested explanation: “My database stores Premier League results from the 2023 and 2024 seasons. One league contains many matches. Each match references one home team and one away team, both from the same team table. The source IDs are primary keys, and the match references are foreign keys. I chose singular table names. Every table has first-seen and last-updated timestamps.”

### 1:15–2:00 — Populated tables

Show `league`, `team`, and `match` in Supabase Table Editor. Point out a team's ID and a corresponding match reference.

Suggested explanation: “The loader inserted one league, 23 teams, and 760 matches. It loads leagues and teams first so the references exist before inserting matches. The match total exceeds the required 500.”

### 2:00–3:00 — Run Question 1

Run only Question 1 from `db/queries.sql` in SQL Editor. Show Liverpool's 29 and Newcastle's 24 home wins.

Suggested explanation: “This joins the home team ID to the team name, groups matches by team, and counts home wins. Liverpool leads with 29 across both saved seasons. Newcastle's 24 surprised me because I had forgotten how well it performed. These are historical totals, not current form.”

### 3:00–4:00 — Run Question 5

Run only Question 5. Show the May 2025 results.

Suggested explanation: “This filters match dates to May 2025 and adds home and away goals. Brentford and Brighton tie on 10 goals, but Brighton played four games and Brentford five. This is why I also show the match count.”

### 4:00–5:00 — Demonstrate no duplicates

In PowerShell, run these commands separately, pressing Enter after each:

```powershell
cd "C:\Users\HP-00\Desktop\BSAD"
```

```powershell
python ingest/load.py
```

Show `inserted=0` for all three tables and totals of 1, 23, and 760. Since data is already loaded, this is a repeat-run demonstration.

Suggested explanation: “Primary keys identify existing records. ON CONFLICT DO NOTHING skips those IDs, so running the loader again creates no duplicates. Milestone 3 will add updates. I also kept a question list, including unanswered questions about injuries and who scores first.”

## Final delivery

1. Review the changed files and AI review log; do not claim checks that have not been performed.
2. Create the Milestone 2 pull request. Use the draft description in `docs/milestone2_pr.md` and include the AI review log in the description.
3. Record a 4–6 minute video using the plan above and upload it to the course-approved location. Confirm the instructor can access it.
4. Add the actual video link to the pull request and submit the pull request URL as instructed by the course.

The pull request and recording have not been created by this guide.
