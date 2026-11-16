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

### Part H: lineage — documented 16 November 2026

The operational path is:

```text
API-Football fixtures for league 39 / seasons 2023 and 2024
  -> sync.py fetches full seasons or overlapping date ranges and checks responses
  -> temporary JSON -> load.py prepare_rows validates and normalizes records
  -> league/team parents -> match children (conditional upserts)
  -> data + sync_state checkpoints + success history commit together
  -> app_reader reads data and sync_runs for reference answers and freshness
```

League/team objects embedded in fixtures are deduplicated by source ID; names
and country are checked for nonempty text. Match IDs, league/team references,
season, short status, date, and scores are mapped to the relational columns.
Date strings become timezone-aware timestamps, preserving the instant. NULL
scores remain NULL. Identical matches collapse by ID; conflicting snapshots,
invalid required fields, negative scores, and same-team matches fail validation.
League/team dictionaries retain the last encountered values for repeated IDs;
this is not a source conflict-resolution guarantee.

Parents are written before children; foreign keys reject missing references.
Conditional upserts preserve first_seen_at and change last_updated_at only when
stored source fields differ. Unmapped fields (including injuries, goal events,
referees, and winner flags) are not loaded. Source disappearance does not delete
stored rows. Temporary sync JSON is removed after processing; it is not a
permanent raw archive. The older football-data.org competition download is not
part of this operational sync. Full field lineage is in docs/data_dictionary.md.

Checkpoints advance only with committed data. A failed transaction saves no
football changes, while its separate sync_runs history records the safe failure.
Preview data changes roll back; their history is marked dry-run/partial. A hard
interruption can leave finished_at NULL, and database unavailability can prevent
logging altogether. Quality-query snapshots in this report are independent of
these sync transactions and should retain their original measurement times.

### Part H: freshness guarantee and limitations

The workflow targets 00:23 and 12:23 UTC daily. If runs start on time and succeed,
API-visible changes inside the date overlap should normally reach the database
within about 12 hours plus run duration. The overlap starts seven days before
the earlier of the last successful run date and latest stored match date, and
ends fourteen days after the run date. Older corrections wait for the full
reconciliation that becomes due seven days after the preceding successful full
run. A conservative healthy-schedule planning bound is seven days plus one
12-hour interval and execution time for those older corrections.

**There is no finite worst-case freshness guarantee during failures.** Missed
or delayed schedules, unavailable API/database service, exhausted quota, or bad
credentials can cause indefinite staleness. The 40-minute workflow timeout
limits one attempt, not total downtime. Source publication delays are outside
this pipeline's control, and changes outside the configured leagues/seasons
are not collected. These timing targets are not proof of scheduled-run evidence.

Freshness has two meanings: when we last checked the source and which match
dates we actually cover. Q05 measured the latest match as 2025-05-25 15:00 UTC
at 2026-11-16 21:27:31.871397 UTC. A successful November sync therefore does not
support November current-form claims. Use scripts/status.py to show the latest
successful refresh and latest refresh with actual changes separately; do not
use an unchanged row's old last_updated_at as the sole freshness indicator.

### Part H: change log — 16 November 2026

- Q01-Q09 measured all five tables, important missing values, duplicates by the
  stated definitions, invalid values, orphans, and historical coverage. The
  dated results above are evidence; they are not timeless guarantees.
- The coverage gap remains: Q05 found Premier League matches only, and Q09
  found FT as the only status across the saved seasons. No league expansion or
  current-season collection occurred simply because scheduling was added.
- The first full live sync fetched 760 fixtures; incremental runs fetched 33.
  Both the student rerun tests reported zero inserts and zero updates, matching
  the prediction. This shows no mapped-field changes in those fetched batches,
  not that the source never changes. Run IDs and timestamps are in
  docs/sync_tests.md.
- The invalid-key test failed with exit code 1 and recorded zero committed
  changes and a sanitized message. No actual source correction, disappearing
  record, or scheduled-run-specific data quirk has yet been established.
- The first golden-reference check passed all 11 answerable queries and saved
  a baseline; four decline cases describe expected behavior, not tested chatbot
  responses. The later scheduled-sync comparison is still pending.

### Part H: ownership and alerting

The student repository owner (Jongar03) maintains this pipeline. In a company,
assign operational responsibility to data engineering/on-call, coverage and
definition review to a football-data steward, and freshness display/refusal
behavior to the application owner.

GitHub Actions failures should notify the pipeline owner. Notification email
settings/delivery have not been verified; no automated missing-run alert or
separate paging service is installed. Proposed operating policy: investigate a
failed run immediately or a successful-refresh age exceeding 24 hours. This is
a recommendation for ownership, not a claim that an alert already exists.

Response steps: inspect the Actions log and safe sync_runs error, check quota,
credentials and database availability, fix the cause, run a manual recovery,
and verify its saved result. Use full reconciliation if the missed period could
hide older corrections, retain failure history, and inform downstream users
when freshness or coverage limits make answers unreliable.

### Remaining verification

This section records the supplied Q01-Q09 measurements, including operational
counts, parent-field missing-value and duplicate-name checks, and observed
status/season date ranges. Broader source-level identity and timestamp checks
could extend it. Part H documentation is now provided above; verification of
three successful scheduled runs spanning at least 48 hours, the follow-up
reference comparison after two additional scheduled successes, and the final
student review/screencast remain pending. The historical raw-file
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
