# evals/

How you prove your system gives correct answers.

| Week | File | What it does |
|---|---|---|
| 3 | `golden_questions.csv` | 15+ questions with columns `id, question, category, reference_sql, correct_behavior, source` |
| 3 | `check_reference.py` | Runs every reference query as `app_reader` and confirms each one succeeds |
| 5 | `run_evals.py` | Asks your chatbot every golden question; records answer, tool calls, tokens, cost, time, and the reference result |
| 5&ndash;7 | `results/weekN.csv` | One results file per evaluation run, graded by you |

Reference answers are SQL, not fixed values, because your data keeps syncing.

## Milestone 3 question set

`golden_questions.csv` contains 15 questions: 9 labeled baseline and 6 other.
There are 11 reference SQL queries and 4 should_decline cases with empty SQL.
The fixed scope on historical football questions is league 39 and seasons
2023/2024; season 2024 means the 2024-25 season, not the calendar year 2024.
No fixed historical answer values are embedded in the expectations.

### Source mapping

The student supplied `docs/question_log.md` in chat. Its recorded questions,
not newly invented provenance, support these source labels:

| IDs | Running-list source |
| --- | --- |
| Q01-Q05 | Milestone 2 answered questions 1-5, also in db/queries.sql |
| Q06 | Broader question: home versus away performance |
| Q07 | Broader question: key-player injuries |
| Q08 | Broader question: who usually scores first |
| Q09 | Broader question: current streak, skill or luck |
| Q10-Q15 | New coverage, freshness, historical trend/comparison, and decline questions |

Q07-Q09 adapt the original topics to concrete teams while preserving the missing
evidence being tested. Q15 addresses the measured five-league coverage gap.
Injury, goal-order, current-form, and causal claims cannot be inferred from
historical final scores alone.

### Validate locally (no database connection)

```powershell
.\.venv\Scripts\python.exe evals/check_reference.py --validate-only
.\.venv\Scripts\python.exe -m unittest evals.test_check_reference -v
```

This checks CSV structure and requirements, not whether SQL executes successfully.
The source mapping above still requires human review; the script cannot prove
that a baseline label is authentic.

### Save the first live reference answers

Run from the BSAD folder, with APP_DATABASE_URL configured locally:

```powershell
.\.venv\Scripts\python.exe evals/check_reference.py --output evals/results/baseline.json
```

The checker loads only APP_DATABASE_URL, verifies `current_user = app_reader`,
and executes the queries in a read-only, repeatable-read transaction. A query
failure is isolated with a savepoint so the remaining questions can still be
checked. It requires a nonempty result, rejects wholly NULL answers and results
over 10,000 rows, sets a 30-second statement timeout, and exits nonzero on failure.
The CSV is curated project code, not arbitrary user SQL; the basic single-query
validation is not a general SQL security parser. Role permissions and read-only
execution are the safety boundaries.

The JSON saves columns and actual answer rows, the database role, UTC snapshot
time, a fingerprint of the question set, and successful scheduled-run IDs visible
in that snapshot. No credentials or raw database error messages are saved.
Existing output files are never overwritten. Use a new filename if a failed
first attempt needs to be rerun, and use that successful file for comparison.

Should-decline cases are recorded without executing SQL. This checker does not
test an actual chatbot's refusal behavior; that comes in later milestones.

### Compare after at least two more successful scheduled syncs

```powershell
.\.venv\Scripts\python.exe evals/check_reference.py --compare evals/results/baseline.json --output evals/results/followup.json
```

The comparison reports changed, unchanged, and failed reference queries. It
requires the same question-set fingerprint and a successful baseline. It also
reports whether at least two new successful scheduled run IDs are present;
manual runs and dry runs do not count. A successful query check with insufficient
new scheduled runs is not yet the required Part G follow-up evidence.

Q14's freshness answer can change as new runs finish even when football results
remain unchanged. Distinguish that metadata change from an actual change to
match scores or team records. Historical football answers may stay unchanged
because the source still reports the same historical data. Record the actual
comparison and explanation in docs/sync_tests.md.

### Current evidence status

On 2026-11-16, local CSV validation passed (15 questions, 9 baseline, 4 decline)
and all six offline checker tests passed. No database connection was made.
Live execution as app_reader,
the first saved answer baseline, and the post-schedule comparison are pending.
Do not describe offline validation as successful database execution.
