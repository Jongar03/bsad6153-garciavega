CREATE TABLE IF NOT EXISTS public.sync_runs (
    run_id uuid PRIMARY KEY,
    started_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    finished_at timestamptz,
    status text NOT NULL CHECK (status IN ('success', 'partial', 'failed')),
    records_fetched integer NOT NULL DEFAULT 0 CHECK (records_fetched >= 0),
    records_inserted integer NOT NULL DEFAULT 0 CHECK (records_inserted >= 0),
    records_updated integer NOT NULL DEFAULT 0 CHECK (records_updated >= 0),
    error_message text,
    trigger text NOT NULL CHECK (trigger IN ('schedule', 'manual')),
    is_dry_run boolean NOT NULL DEFAULT false,
    CHECK (finished_at IS NULL OR finished_at >= started_at)
);
ALTER TABLE public.sync_runs ENABLE ROW LEVEL SECURITY;
GRANT SELECT ON public.sync_runs TO app_reader;
DROP POLICY IF EXISTS app_reader_select ON public.sync_runs;
CREATE POLICY app_reader_select ON public.sync_runs
    FOR SELECT TO app_reader USING (true);
