# Milestone 3: sync football data and schedule updates

The previous loader skipped existing records, so corrected source data never
reached the database. This change upserts new/changed fixtures, preserves
timestamps on unchanged rows, stores transactional checkpoints and sync history,
and adds a twice-daily GitHub Actions workflow with a manual trigger.

The read-only app_reader role can read data/history through RLS policies. Secrets
are read from local .env or Actions secrets, never embedded in SQL or workflow
files. The status script reports refresh freshness and seven-day write totals.

## Validation

- Student verified app_reader login, INSERT/DELETE permission denial, and Data
  API disabled in Supabase.
- Assistant ran 11 offline tests plus disposable PostgreSQL tests for upserts,
  timestamps, rollback, persistent failure logging, and status constraints.
- Live preview and first committed manual sync fetched 760 fixtures with zero
  inserts and updates, matching the prediction. app_reader read the saved run.
- GitHub workflow execution and scheduled-run evidence: pending activation.

## AI review log

### Direct

The student requested guided implementation of assignment Parts A-D, confirmed
each Supabase setup step, and predicted zero inserts/updates before the preview.

### Read

The student reviewed and ran the role setup and safe write-denial examples with
the assistant. Full review of sync upserts, checkpoint logic, logging, and the
workflow is still required; do not mark it complete until the student does it.

### Verify

Student-run checks: scripts/check_db.py --app reported app_reader; safe INSERT
and DELETE tests returned permission denied. Assistant-run checks and actual
sync results are recorded in docs/sync_tests.md. Cloud checks remain pending.

### Decide

The attempted CREATE POLICY encountered an existing policy. Inspection showed
all three policies already existed, so they were retained. The API lacks a
documented changed-since fixture filter; implementation uses date overlap plus
weekly full reconciliation. This is an assistant design decision that the
student still needs to review and explain in their own words.

## Before submission

- [ ] Student reviewed every change and completed the AI review log in their own words.
- [ ] Secret checks complete, including Git history.
- [ ] Actions secrets configured; workflow on main; GitHub manual run succeeded.
- [ ] Link to PR 2 and required scheduled-run evidence added when available.
