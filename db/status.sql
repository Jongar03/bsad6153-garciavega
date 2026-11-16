-- Successful refresh is different from a refresh that actually changed rows.
-- Dry runs do not count as successful data updates.
SELECT
    max(finished_at) FILTER (WHERE status = 'success' AND NOT is_dry_run)
        AS last_successful_sync,
    max(finished_at) FILTER (WHERE status = 'success' AND NOT is_dry_run
        AND records_inserted + records_updated > 0) AS last_sync_with_changes,
    count(*) FILTER (WHERE finished_at >= now() - interval '7 days'
        AND status = 'success' AND NOT is_dry_run) AS successful_runs_last_7_days,
    coalesce(sum(records_inserted) FILTER (WHERE finished_at >= now() - interval '7 days'
        AND status = 'success' AND NOT is_dry_run), 0) AS inserted_last_7_days,
    coalesce(sum(records_updated) FILTER (WHERE finished_at >= now() - interval '7 days'
        AND status = 'success' AND NOT is_dry_run), 0) AS updated_last_7_days,
    count(*) FILTER (WHERE started_at >= now() - interval '7 days'
        AND status = 'failed' AND finished_at IS NOT NULL AND NOT is_dry_run)
        AS failed_runs_last_7_days,
    count(*) FILTER (WHERE finished_at IS NULL) AS unfinished_runs
FROM public.sync_runs;
