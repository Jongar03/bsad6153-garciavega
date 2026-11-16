# Sync test evidence

## Part D pre-schedule incremental check — 2026-11-16

Prediction recorded before execution by the assistant: now that a committed
checkpoint exists, the request should use date filters and fetch fewer than
760 fixtures, with 0 inserted and 0 updated if historical data is unchanged.
Command: `.venv\Scripts\python.exe -u ingest/sync.py --trigger manual`.
Result: passed. Run `7a57b6ac-ea76-46f0-82d4-69079270fd99` committed successfully
with records_fetched=33, records_inserted=0, records_updated=0, trigger=manual.
The date-filter requests began at 2024-05-12 for season 2023 and 2025-05-18 for
season 2024. Both ended at 2026-11-30. Compared with the initial 760 fixtures,
the incremental run fetched only 33 and made no spurious changes. This validates
date-filter access on the current account. It is not a scheduled run.

## Part C logging validation — 2026-11-16

The 11 offline tests passed after logging was added. Before the temporary-table
test, assertions specified: success commits one probe row; a later failure
commits no probe row but preserves fetched=7 and a failure log; a preview
commits no probe row and records partial with zero committed inserts/updates.
`scripts/test_sync_logging.py` passed all these assertions, confirmed error
details were sanitized, and confirmed the status CHECK rejects invalid values.
These were disposable test tables, not actual API sync runs.

### First committed sync prediction (recorded before execution)

Based on the student's earlier prediction and the matching live preview, the
assistant expects fetched=760, inserted=0, updated=0, status=success,
trigger=manual. The run should commit its checkpoints and one sync_runs row.
Command: `.venv\Scripts\python.exe -u ingest/sync.py --trigger manual`.
Result: matched the prediction. The first committed sync succeeded:

| Field | Recorded value |
| --- | --- |
| run_id | `397e43c4-8763-476e-8e96-705bffb3eca7` |
| started_at (UTC) | 2026-11-16 01:38:51.739952+00:00 |
| finished_at (UTC) | 2026-11-16 01:40:33.364954+00:00 |
| status | success |
| records_fetched | 760 |
| records_inserted | 0 |
| records_updated | 0 |
| error_message | NULL |
| trigger | manual |
| is_dry_run | false |

`scripts/status.py` then connected as app_reader and read the same row. It
reported one successful run in the past seven days, zero inserted/updated rows,
zero completed failures, and zero unfinished runs. The last successful sync
was the finish timestamp above. `last_sync_with_changes` was NULL because no
run in this new history has changed football data. This manual run does not
count toward the three required scheduled runs.

## Part B live preview — 2026-11-16

Before execution, the student predicted **0 inserted records and 0 updated
records**, assuming the provider had not corrected the existing historical data.

Command: `.venv\Scripts\python.exe ingest/sync.py --dry-run`.
This fetches live API data and rolls back all proposed data/checkpoint writes.
Outcome: passed. The initial sandboxed invocation could not complete; rerunning
with approved network access succeeded. Both seasons were fetched in full.

```text
records_fetched: 760
records_inserted: 0
records_updated: 0
league: inserted=0, updated=0
team: inserted=0, updated=0
match: inserted=0, updated=0
[ok] Dry run rolled back; counts are proposed changes.
```

The result matched the student's prediction. All stored source fields matched
the fetched records after normalization. This does not prove that every field
in the API response is unchanged, only those mapped into our tables. No data or
checkpoint changes were committed. Incremental date-filter access still needs
a separate test after a successful committed checkpoint exists.

This preview is not a scheduled run. Part C's sync_runs logging has not yet
been implemented, so this preview has no persistent sync_runs row and does not
replace the required Part G evidence.
