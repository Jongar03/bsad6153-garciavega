# Sync test evidence

## Part G: student-run break-it tests — 2026-11-16

Evidence below was transcribed from the student's PowerShell output and
Supabase query-result screenshots. The assistant did not rerun these tests or
query the database while documenting them. All database timestamps are UTC.

### Test 1: back-to-back rerun

**Prediction, agreed by the student before execution:** the second run should
insert 0 records and update 0 records if the source has not changed.

**Procedure:** from the project folder, run the following command, wait for
`[ok] Sync committed.`, then run the same command again:

```powershell
.\.venv\Scripts\python.exe -u ingest/sync.py --trigger manual
```

Both executions used date-overlap requests for league 39: season 2023 from
2024-05-12 and season 2024 from 2025-05-18, both through 2026-11-30.
Both printed `[ok] Sync committed.` and the following counts:

| Table | First-run inserted | First-run updated | Second-run inserted | Second-run updated |
| --- | ---: | ---: | ---: | ---: |
| league | 0 | 0 | 0 | 0 |
| team | 0 | 0 | 0 | 0 |
| match | 0 | 0 | 0 | 0 |

**Saved sync_runs evidence:**

| Field | First run | Second run |
| --- | --- | --- |
| run_id | `e7a9b1a4-a72b-4c9d-841d-6898e0baf066` | `bb451328-51a7-4ede-8a40-ffbb8315e79a` |
| started_at (UTC) | 2026-11-16 22:11:38.2231+00 | 2026-11-16 22:12:24.904623+00 |
| finished_at (UTC) | 2026-11-16 22:12:02.663407+00 | 2026-11-16 22:12:51.809579+00 |
| status | success | success |
| records_fetched | 33 | 33 |
| records_inserted | 0 | 0 |
| records_updated | 0 | 0 |
| error_message | NULL | NULL |
| trigger | manual | manual |

The student verified these rows in Supabase with:

```sql
SELECT run_id, started_at, finished_at, status, records_fetched,
       records_inserted, records_updated, error_message, trigger
FROM public.sync_runs
WHERE run_id IN (
    'e7a9b1a4-a72b-4c9d-841d-6898e0baf066',
    'bb451328-51a7-4ede-8a40-ffbb8315e79a'
)
ORDER BY started_at;
```

**Conclusion:** the result matched the prediction. The repeat run inserted no
duplicates and made no spurious updates for the fetched overlap. This test does
not establish whether source records outside that overlap changed; those are
covered by full reconciliation. Neither execution counts as a scheduled run.

### Test 2: temporarily invalid API credentials

**Prediction, agreed by the student before execution:** the sync should fail
visibly with a nonzero exit code, record a failed sync_runs row, and commit no
football-data inserts or updates.

**Procedure:** temporarily override the API key only in the PowerShell process.
The finally block restores the previous value or removes the override when it
was originally absent. Neither `.env` nor GitHub Actions secrets is edited.

```powershell
$previousFootballKey = $env:API_FOOTBALL_KEY

try {
    $env:API_FOOTBALL_KEY = "invalid-key-for-assignment-test"
    .\.venv\Scripts\python.exe -u ingest/sync.py --trigger manual
    Write-Host "Sync exit code: $LASTEXITCODE"
}
finally {
    if ($null -eq $previousFootballKey) {
        Remove-Item Env:\API_FOOTBALL_KEY -ErrorAction SilentlyContinue
    }
    else {
        $env:API_FOOTBALL_KEY = $previousFootballKey
    }
    Remove-Variable previousFootballKey
}
```

The literal key above is intentionally fake, not a real credential.

**Observed console result:**

```text
run_id: 0190f15e-37da-4a24-916f-650e4671238d
[FAIL] API rejected the request; check credentials and plan access.
Sync exit code: 1
```

The rejection occurred on the first season's request. The student then queried:

```sql
SELECT run_id, started_at, finished_at, status, records_fetched,
       records_inserted, records_updated, error_message, trigger
FROM public.sync_runs
WHERE run_id = '0190f15e-37da-4a24-916f-650e4671238d';
```

**Saved sync_runs evidence:**

| Field | Value |
| --- | --- |
| run_id | `0190f15e-37da-4a24-916f-650e4671238d` |
| started_at (UTC) | 2026-11-16 22:16:33.071729+00 |
| finished_at (UTC) | 2026-11-16 22:16:35.628464+00 |
| status | failed |
| records_fetched | 0 |
| records_inserted | 0 |
| records_updated | 0 |
| error_message | API rejected the request; check credentials and plan access. |
| trigger | manual |

**Conclusion:** the result matched the prediction. The failure was visible via
exit code 1 and persisted in the run log with no credentials in the displayed
error. No data writes were reported. This tests rejection of invalid API
credentials, not a mid-write interruption or successful recovery run afterward.

### Required golden-question baseline and follow-up

The student ran the following on 2026-11-16 and supplied its console output:

```powershell
.\.venv\Scripts\python.exe evals/check_reference.py --output evals/results/baseline.json
```

CSV validation reported 15 questions, 9 baseline sources, and 4 should-decline
cases. All 11 answerable reference queries passed; Q07, Q08, Q09, and Q15 were
recorded as decline expectations without SQL or an actual chatbot test. The
checker verifies the connected role is app_reader before executing references.
The output confirmed that evidence was saved to `evals/results/baseline.json`.
The exact baseline evaluation timestamp is stored in that JSON file.

| Reference | Result rows reported |
| --- | ---: |
| Q01 | 23 |
| Q02 | 23 |
| Q03 | 4 |
| Q04 | 23 |
| Q05 | 20 |
| Q06 | 46 |
| Q10 | 2 |
| Q11 | 1 |
| Q12 | 10 |
| Q13 | 2 |
| Q14 | 1 |

**Follow-up completed on 2026-11-17:** the student ran:

```powershell
.\.venv\Scripts\python.exe evals/check_reference.py --compare evals/results/baseline.json --output evals/results/followup.json
```

The assistant inspected both saved JSON files locally to document the following
results; no database queries were rerun during this documentation update.

| Evidence | Baseline | Follow-up |
| --- | --- | --- |
| File | evals/results/baseline.json | evals/results/followup.json |
| checked_at_utc | 2026-11-16T21:52:33.927872+00:00 | 2026-11-17T15:12:36.841688+00:00 |
| database_user | app_reader | app_reader |
| passed | true | true |
| Successful scheduled run IDs visible | 0 | 2 |

The follow-up reports two new successful scheduled sync IDs:

- `0a855e23-cbaf-4640-b078-a688eb44091a`
- `a5225741-bfa3-40ed-9d99-81894eb282bc`

`at_least_two_more_scheduled_syncs` is true. These are database sync UUIDs,
not GitHub Actions run numbers. The student also supplied an Actions screenshot
showing successful scheduled workflow runs #2 and #3. The comparison uses the
same question set and retains the original baseline unchanged.

All 11 answerable queries still passed with the same result-row counts shown
above. Q01-Q06 and Q10-Q13 returned unchanged answers. Q07-Q09 and Q15 remained
decline expectations with no SQL execution or chatbot refusal test. No queries
failed. Only Q14 (sync freshness and seven-day history) changed:

| Q14 field | Baseline | Follow-up |
| --- | --- | --- |
| last_successful_sync (UTC) | 2026-11-16T17:10:03.808210+00:00 | 2026-11-17T13:39:56.691355+00:00 |
| last_sync_with_changes | NULL | NULL |
| successful_runs_last_7_days | 3 | 7 |
| inserted_last_7_days | 0 | 0 |
| updated_last_7_days | 0 | 0 |
| failed_runs_last_7_days | 0 | 1 |
| unfinished_runs | 0 | 0 |

**Interpretation:** the successful-run count rose by four: the two manual
rerun-test successes and two scheduled successes. The single recorded failure
matches the deliberate invalid-key test. The latest successful-refresh time
advanced, demonstrating that Q14 reads live operational history rather than a
fixed answer. This is not evidence of changed football scores: committed
insert/update totals stayed zero, and all ten football reference answers stayed
unchanged. That is consistent with rechecking historical seasons without new
mapped-field corrections. It does not prove that unfetched source records never
change or that current-season data is present. NULL last_sync_with_changes means
this history contains no successful sync with data changes, not that the initial
database was never loaded.

**Part G evidence is now complete:** two documented break-it tests plus the
required reference comparison after two additional successful scheduled syncs.
The separate Part D requirement of at least three successful scheduled runs
spanning at least 48 hours remains pending; this comparison does not satisfy it.

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
