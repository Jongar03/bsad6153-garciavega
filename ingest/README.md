# Football data download

## Milestone 3 sync (Part B)

`ingest/sync.py` fetches fixtures, validates them using the existing loader, and
upserts leagues, teams, and matches in one transaction. Existing Milestone 1/2
commands remain available. The default scope is deliberately fixed to league 39,
seasons 2023 and 2024, matching the loaded data; it does not claim current-season
or five-league coverage.

Before each live test, write a prediction of inserted and updated row counts.
For an unchanged source, the expected result is zero inserts and zero updates.
The initial request should retrieve approximately 760 fixtures, but the provider
may have corrected historical records since the original download.

```powershell
.\.venv\Scripts\python.exe ingest/sync.py --dry-run
```

This preview makes real API requests and executes database writes inside a
transaction, then rolls back the data and checkpoint changes. It consumes API
quota but does not save proposed changes. After reviewing the preview:

```powershell
.\.venv\Scripts\python.exe ingest/sync.py
```

### How it works

- Natural source IDs identify existing rows. `ON CONFLICT ... DO UPDATE` updates
  source fields only when `IS DISTINCT FROM` detects a real difference, including
  differences involving NULL. `first_seen_at` is preserved; `last_updated_at`
  advances only on a change. The counts include parent league/team rows as well
  as matches, and the output also separates counts by table.
- First run per league/season: fetch the whole season. Later runs use a database
  checkpoint in `sync_state`. The request starts seven days before the earlier
  of the last successful run date and latest stored fixture date, and ends
  fourteen days after today. This refreshes the historical tail for old seasons
  and recent/upcoming fixtures for an active season. Future fixture dates never
  move the checkpoint beyond the last successful run.
- Every seven days (or with `--full`), reconcile the entire configured seasons.
  Match-date filtering is not a changed-since feed: older corrections, fixtures
  moved outside the overlap, and far-future additions may wait for this full
  reconciliation. Records missing at the source are retained, never silently
  deleted. Automatic expansion to new seasons is not implemented.
- The API documents `from`/`to` but no fixture modification-time filter. Filter
  access still needs validation on this account. An API plan/filter error fails
  visibly rather than silently accepting an empty result or changing strategy.
- Up to five attempts handle 429, 5xx, transport failures, and provider rate-limit
  responses. Delays use 60/120/240/480 seconds and honor longer Retry-After values.
  Requests are at least 6.1 seconds apart. Provider errors and credentials are
  not written to logs. Incomplete pages and malformed records fail the whole run.
- A transaction-scoped advisory lock prevents concurrent copies of this sync.
  All selected seasons are fetched and validated before writing data. Data and
  checkpoints commit together; failure rolls them back. Database or API outage
  has no finite freshness guarantee; the weekly catch-up assumes successful runs.
- `sync_state` is created by the script, with RLS and a SELECT policy/grant for
  app_reader. Only the owner connection writes it. `db/roles.sql` also includes
  its conditional grant.

Official source checked during implementation:
[API-Football fixtures reference](https://www.api-football.com/documentation_v3).

### Validation and remaining work

Offline tests:
`python -m unittest ingest.test_sync ingest.test_football_fetch -v`.
Database behavior tests: `python scripts/test_sync_db.py`, using only temporary
tables and rolling back. These passed during implementation. A live preview on
2026-11-16 fetched 760 fixtures and proposed 0 inserts and 0 updates, matching
the student's prediction; all changes rolled back. The first committed sync
then succeeded with the same counts and a saved manual history row. The next
incremental run validated date-filter access: 33 fetched, 0 inserted, 0 updated. See
`docs/sync_tests.md` for the evidence.

### Part C: run history and status

Every invocation that can initialize the database log creates a UUID row in
`sync_runs` before fetching. It records start/finish timestamps, a constrained
status (`success`, `partial`, `failed`), fetched fixtures, committed inserted and
updated rows across all three data tables, a safe error summary, and the trigger
(`manual` by default; `--trigger schedule` for GitHub's scheduled event).

The initial row uses `status=failed`, `finished_at=NULL`, and an explicit
"completion not yet recorded" message. A NULL finish means running or abruptly
interrupted, not a confirmed completed failure. This preserves evidence even
if the process is killed. A hard kill cannot record its exact finish time;
the status script separately counts unfinished runs. Caught errors record a
finish time, preserve successfully validated fetched counts, and report zero
committed changes. Database connection/setup failure cannot write a database
log and instead exits nonzero. A lost database connection can also prevent
finalizing a previously created row.

Success is written in the same transaction as the data and checkpoint, avoiding
a success row for uncommitted changes. Previews now retain a history row with
`is_dry_run=true`, `status=partial`, and zero committed changes, while console
counts describe proposed changes. They do not count as successful refreshes.
The earlier Part B preview predates logging and has no history row.

`db/sync_runs.sql` creates the table, RLS policy, and SELECT grant for app_reader;
the sync applies it automatically. `db/roles.sql` includes the matching grant.
The owner connection alone writes the history in this application.

```powershell
.\.venv\Scripts\python.exe scripts/status.py
```

This connects as app_reader and runs `db/status.sql`, showing the last successful
refresh, last refresh with actual changes, inserts/updates and successes/failures
over the previous seven days, and unfinished runs. It also shows the latest ten
history rows. A NULL last-change time means no change has been recorded by the
sync history; it does not mean the database has never been loaded. Counts are
write events, not distinct records (one record can change on multiple runs).
Timestamps are timezone-aware. Scheduled automation remains Part D.

Run from the project folder:

```powershell
.venv\Scripts\python.exe ingest/fetch.py
```

The project already includes requests and python-dotenv. Put your API-Football key in `.env` as `API_FOOTBALL_KEY=your-key`. Never put a real key in source code. The football-data.org competition list is public, so this script does not send it a key.

## What each part does

1. `main()` reads settings and your key, and makes a new timestamped folder inside `data/raw/`.
2. `Client.get()` sends requests. Only requests to API-Football receive your key, in `x-apisports-key`.
3. It waits at least 6.1 seconds between requests. A temporary error (429, 5xx, timeout or connection failure) gets up to four retries after the first attempt. It waits 60, 120, 240, then 480 seconds, or longer if the service asks via `Retry-After`. Permanent errors are logged and skipped. API-Football errors inside an otherwise successful reply are also checked.
4. `collect()` first downloads football-data.org competitions, then API-Football matches for Premier League (league 39), one season at a time. It stops after collecting at least 500 different matches, or after trying all selected seasons. Whole season responses are kept, so the result can exceed 500.
5. `valid_fixture()` checks that a match has an ID, date, league ID, league name and country. Missing required fields are counted and skipped. Optional values such as unknown scores may remain null. Duplicate IDs count only once.
6. `save()` stores the returned JSON without removing any records. Error JSON replies are saved too. A separate `summary.json` reports record counts, invalid records, duplicate records, failed requests, and retries. `fetch.log` records progress.

## Pagination and scope

These URLs are two services, not two record types. This implementation chooses **fixtures (matches)** as the main records and **competitions** as related information.

The API-Football `/fixtures` request supports league and season filters, but has no documented page parameter. Consequently this script loops through seasons rather than inventing page numbers or cursors. It verifies that each season reply reports one page; an unexpected or missing page count is reported as a failure. Other API-Football requests, such as `/players`, use page numbers; that does not apply to fixtures. football-data.org's competition list also has no documented pagination.

By default the script tries seasons Year-2, Year-3, Year-4, matching the documented Free-plan window (2024, 2023, 2022 in 2026). Choose an explicit scope with:

```powershell
.venv\Scripts\python.exe ingest/fetch.py --league 39 --seasons 2024 2023 2022 --target 500
.venv\Scripts\python.exe -m unittest ingest.test_football_fetch -v
```

The target must be at least 500. A smaller competition or unavailable seasons may not yield enough records. The script then exits with status 1 and reports an incomplete run. It also reports incomplete if required fields, requests, or a competition candidate are missing. It never claims to have downloaded records it did not receive.

## How the services relate

Matches contain an API-Football league ID. football-data.org has its own competition IDs. Do not join these IDs directly. `relationship_candidates.json` records competitions whose name and country match exactly (ignoring case). These are **unconfirmed candidates**, not a provider-guaranteed cross-reference. Review them before joining data in a database. The full public competition list is saved, including competitions unrelated to the downloaded matches. A successful download does not mean those relationships have been independently verified.

## Limits and official sources

- [API-Football reference](https://www.api-football.com/documentation_v3): authentication, fixtures filters, IDs and response structure.
- [API-Football league download guide](https://www.api-football.com/news/post/how-to-get-all-data-from-a-league-with-api-football): league 39 example, season access, and endpoint-specific pagination.
- [API-Football quota guide](https://www.api-football.com/news/post/how-to-optimize-api-sports-calls-and-quota-usage): Free plan allows 100 requests/day and 10/minute. Allowance is shared with other uses of your key; reruns consume more requests.
- [football-data.org quickstart](https://www.football-data.org/documentation/quickstart): competition list and response fields.
- [football-data.org policies](https://docs.football-data.org/general/v4/policies.html): unauthenticated clients can access areas and competition lists, up to 100 requests per 24 hours. Match/team requests require separate access; this script does not fetch those.

`data/raw/` was already in `.gitignore` and remains excluded. Each run has its own folder. Request headers and API keys are not logged. JSON formatting is indented for readability, but response contents are preserved.

