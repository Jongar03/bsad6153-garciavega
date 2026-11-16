# Data quality and coverage check

## Milestone 3: live database measurements, 16 November 2026

Evidence: the student executed the read-only queries in Supabase SQL Editor and
provided screenshots of the results. The assistant transcribed those results;
it did not rerun these queries while preparing this report. Query IDs below map
to `db/quality_checks.sql`. All measurement times are UTC, as shown by Supabase.
Each query is a separate snapshot, not one shared database transaction.

### Row counts — Q01

| Table | Rows | Measured at (UTC) |
| --- | ---: | --- |
| league | 1 | 2026-11-16 21:18:33.164547 |
| team | 23 | 2026-11-16 21:18:33.164547 |
| match | 760 | 2026-11-16 21:18:33.164547 |

These counts cover the football data tables. Operational-table counts were
measured separately with Q06, below.

### Missing values — Q02

All rates below use the 760 matches counted by Q02 at
2026-11-16 21:21:03.211309 UTC.

| Important field | Null count | Null rate | Measured at (UTC) |
| --- | ---: | ---: | --- |
| match_date | 0 | 0% | 2026-11-16 21:21:03.211309 |
| status | 0 | 0% | 2026-11-16 21:21:03.211309 |
| home_goals | 0 | 0.00% | 2026-11-16 21:21:03.211309 |
| away_goals | 0 | 0.00% | 2026-11-16 21:21:03.211309 |

Q02 returns the score percentages directly. Date/status percentages are derived
from their SQL null counts divided by the SQL total. A known zero score must
remain distinct from an unknown (NULL) score.

### Duplicate checks — Q03

| Definition | Duplicate groups | Measured at (UTC) |
| --- | ---: | --- |
| Repeated natural match ID | 0 | 2026-11-16 21:22:46.716856 |
| Same league, season, home team, away team, and kickoff, with different IDs | 0 | 2026-11-16 21:22:46.716856 |

The match primary key prevents repeated IDs. The second check is a heuristic:
it does not detect the same fixture represented with different kickoff times.
These results do not establish the absence of every possible duplicate.

### Invalid values and orphan records — Q04

| Check | Matches flagged | Measured at (UTC) |
| --- | ---: | --- |
| Either score is negative | 0 | 2026-11-16 21:26:10.323511 |
| Home and away team IDs are equal | 0 | 2026-11-16 21:26:10.323511 |
| Status is blank after trimming spaces | 0 | 2026-11-16 21:26:10.323511 |
| Finished status (FT/AET/PEN) with a missing score | 0 | 2026-11-16 21:26:10.323511 |
| Referenced league is missing | 0 | 2026-11-16 21:26:10.323511 |
| Referenced home team is missing | 0 | 2026-11-16 21:26:10.323511 |
| Referenced away team is missing | 0 | 2026-11-16 21:26:10.323511 |

Foreign keys require each match's league and teams to exist. The loader and sync
write parents before matches, inside a transaction; an invalid reference makes
the write fail rather than saving an orphan. CHECK constraints reject negative
scores and identical home/away team IDs. These queries do not audit every
possible status category, season/date inconsistency, or source timestamp error.

### Fairness and time coverage — Q05

| Intended league | Stored matches | Earliest kickoff (UTC) | Latest kickoff (UTC) | Measured at (UTC) |
| --- | ---: | --- | --- | --- |
| Premier League | 760 | 2023-08-11 19:00 | 2025-05-25 15:00 | 2026-11-16 21:27:31.871397 |
| Bundesliga | 0 | NULL | NULL | 2026-11-16 21:27:31.871397 |
| La Liga | 0 | NULL | NULL | 2026-11-16 21:27:31.871397 |
| Ligue 1 | 0 | NULL | NULL | 2026-11-16 21:27:31.871397 |
| Serie A | 0 | NULL | NULL | 2026-11-16 21:27:31.871397 |

At the Q05 measurement time, all 760 stored matches were Premier League matches:
100% of observed coverage, with no match data for four of the five intended
leagues. These proportions are derived from Q05's counts, consistent with Q01.
This is a coverage gap, not proof of measured demographic or prediction bias.

For example, a chatbot asked which team across the five leagues scored the most
could misleadingly select an English team because it has no match records for
the other leagues. Missing coverage does not mean those teams performed worse.
It should explain the scope and decline an all-five-league comparison, or offer
a clearly labeled Premier League-only answer instead.

The latest stored match at this measurement is 25 May 2025. The data therefore
cannot establish current form in November 2026. A recent successful sync means
the configured historical seasons were checked; it does not mean current-season
matches have been collected.

### Operational-table counts — Q06

| Table | Rows | Measured at (UTC) |
| --- | ---: | --- |
| sync_runs | 3 | 2026-11-16 21:34:47.724307 |
| sync_state | 2 | 2026-11-16 21:34:47.724307 |

The history count includes all recorded run types; Q06 does not establish how
many were successful or scheduled. Checkpoint count alone does not identify
the league/season keys. The sync is configured for the 2023 and 2024 seasons.
These operational counts can change as subsequent syncs run.

### Missing or blank parent fields — Q07

| Field | Rows checked | Missing or blank | Rate | Measured at (UTC) |
| --- | ---: | ---: | ---: | --- |
| league.name | 1 | 0 | 0% | 2026-11-16 21:35:34.417061 |
| league.country | 1 | 0 | 0% | 2026-11-16 21:35:34.417061 |
| team.name | 23 | 0 | 0% | 2026-11-16 21:35:34.417061 |

Q07 tests both SQL NULL and text that is empty after trimming surrounding spaces.
The displayed rates are calculated from its flagged counts divided by rows
checked. They are missing-or-blank rates, not separate measurements of each cause.

### Parent identity review candidates — Q08

| Definition | Duplicate groups | Measured at (UTC) |
| --- | ---: | --- |
| Same league name and country under different IDs | 0 | 2026-11-16 21:36:31.450593 |
| Same team name under different IDs | 0 | 2026-11-16 21:36:31.450593 |

The comparison ignores capitalization and surrounding spaces. No candidates
were found by these rules. Different entities can share a name, and spelling
variants can evade this check, so matching names would require review rather
than automatic merging. Primary keys enforce unique league and team IDs;
Q08 checks names across different IDs, not repeated primary-key values.

### Observed statuses and season date ranges — Q09

| Season label | Status | Matches | Earliest kickoff (UTC) | Latest kickoff (UTC) | Measured at (UTC) |
| --- | --- | ---: | --- | --- | --- |
| 2023 | FT | 380 | 2023-08-11 19:00 | 2024-05-19 15:00 | 2026-11-16 21:37:17.860247 |
| 2024 | FT | 380 | 2024-08-16 19:00 | 2025-05-25 15:00 | 2026-11-16 21:37:17.860247 |

FT (finished) was the only observed status in this measurement. The ranges are
consistent with the historical 2023-24 and 2024-25 seasons; a season label denotes
its starting year, so crossing a calendar-year boundary is not itself an error.
This grouped summary does not independently verify every kickoff against the
source schedule or test every possible timezone error. No status recoding or
date correction was justified by these results.

### Cleaning, rejection, and preservation decisions

- No new data cleaning or deletion was performed for this report. The measured
  checks did not flag rows requiring repair; that does not prove all data is
  error-free.
- Preserve missing scores as NULL if they arrive in later syncs. Do not invent
  zeros or infer a loss from an absent winner flag.
- Keep source IDs as identities. The loader skips existing IDs; the sync updates
  stored source fields only when values differ. Preserve first_seen_at and avoid
  changing last_updated_at on unchanged rows.
- Existing ingestion validation rejects malformed required fields, invalid
  scores, same-team matches, and timestamps without time zones. Conflicting
  snapshots of the same match fail validation. These are implementation rules,
  not counts of rejected rows measured by the queries above.
- Retain historical matches and disclose their date range. Do not fabricate
  records for missing leagues or delete historical data to make coverage appear
  more current. Records absent from a later API response are retained pending
  an explicit deletion policy.

### Remaining checks and documentation

This section records the supplied Q01-Q09 measurements, including operational
counts, parent-field missing-value and duplicate-name checks, and observed
status/season date ranges. Broader source-level identity and timestamp checks
could extend it. Part H lineage, freshness guarantees, change log, and ownership
documentation remain to be completed. The historical raw-file
analysis below is preserved separately and was not remeasured by these SQL queries.

## Earlier raw-file analysis — 6 November 2026

Checked locally on 6 November 2026 using the two `fixtures_39_*_attempt1.json` files in `data/raw/football_20261031T232117466176Z/`. Other snapshots and sample excerpts were excluded to avoid counting the same matches repeatedly. This check covers saved fixture records, not every record available from the providers.

## Winner flags

| Season label | Matches | Draws | Null home winner flags | Null away winner flags |
| --- | ---: | ---: | ---: | ---: |
| 2023 | 380 | 82 | 82 | 82 |
| 2024 | 380 | 93 | 93 | 93 |
| Total | 760 | 175 | 175 | 175 |

Draws were identified by equal home and away goal totals. In this snapshot, all 175 draws have null winner flags for both sides. Null must not be converted into a loss: doing so would penalize teams with more draws. For finished matches, derive win/draw/loss from validated goal totals; retain an unknown outcome when scores or status are unavailable. These observations do not establish the provider's general null rules for every match status.

## Fairness check: representation across intended leagues

The baseline log describes a project spanning Europe's five major football leagues. A coverage comparison of the saved match records found:

| Intended league | Saved matches | Share |
| --- | ---: | ---: |
| Premier League | 760 | 100% |
| La Liga | 0 | 0% |
| Bundesliga | 0 | 0% |
| Serie A | 0 | 0% |
| Ligue 1 | 0 | 0% |

This is a representation/coverage check, not a demographic fairness audit or a measurement of prediction accuracy. Competition listings and separate team exports do not supply missing match histories. No prediction results were evaluated, so equal accuracy across leagues cannot be claimed.

## Implication and safeguards

An agent that assumes five-league coverage could favor Premier League teams or make unsupported comparisons for teams without match histories. Missing coverage must not be treated as poor team performance. Limit recommendations to the verified league and season scope until comparable match data are collected for the other leagues. Require human review of cross-league recommendations and repeat coverage and outcome-label checks after ingestion. Historical seasons alone do not establish current form.

## Mirror paragraph

In my `docs/data_quality.md`, I found that all 175 drawn matches in my 760-match dataset have null winner flags. An agent treating null as a loss would unfairly downgrade teams with more draws. My fairness check also compared coverage across Europe's five major leagues: the Premier League had 760 matches, while the other four had none. An unaware agent could favor English teams or make unsupported cross-league recommendations. Before allowing those recommendations, I would require correct draw handling, comparable league coverage, human review, and a repeated coverage check. This identifies a representation gap, not proven prediction bias.
