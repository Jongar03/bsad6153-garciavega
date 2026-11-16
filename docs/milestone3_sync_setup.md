# Milestone 3 PR 1: activate the schedule

Local workflow preparation is not evidence of a deployed schedule. Track each
step with actual outcomes; never count local or manually dispatched runs as
scheduled runs.

1. Use branch `milestone-3-sync` for Parts A-D. Preserve unrelated local changes.
2. In the GitHub repository, open Settings > Secrets and variables > Actions.
   Add repository secret DATABASE_URL using the entire local DATABASE_URL value
   (not the name or equals sign), and API_FOOTBALL_KEY using its local value.
   DATABASE_URL must use Supabase's Session pooler, not the direct host. Never
   paste credentials into a PR, issue, workflow, screenshot, or chat.
3. Review the branch diff and the AI review log in `docs/milestone3_sync_pr.md`.
   Create PR 1 against main and record its real URL below.
4. GitHub's workflow_dispatch and schedule events require the workflow to exist
   on the default branch. For a brand-new workflow, merge PR 1 to main first,
   then immediately run the manual smoke test (Actions > Football data sync >
   Run workflow > main). The assignment's instruction to dispatch before merging
   is not possible through the standard UI until the workflow exists on main.
   A local success does not substitute for the GitHub manual smoke test.
5. Check the actual Actions run turns green and inspect its nonsecret counts.
   Run scripts/status.py and confirm a matching success row with trigger manual.
6. Confirm subsequent cron runs show event schedule and trigger schedule.
   Keep at least three successful scheduled runs spanning at least 48 hours.
   Do not simulate scheduled evidence by manually passing --trigger schedule.
7. Review Actions email notification settings. If a job fails, inspect its log,
   check the safe sync_runs error, fix the cause, then manually test again.
8. Create branch `milestone-3` for Parts E-H and PR 2 after PR 1 is merged.

## Activation evidence

- PR 1 URL: pending.
- Actions page: https://github.com/Jongar03/bsad6153-garciavega/actions
- Repository secrets configured: not yet verified.
- Workflow merged into main: not yet verified.
- Successful GitHub manual run: pending.
- First successful scheduled run: pending.
- Scheduled runs spanning 48 hours: pending.
