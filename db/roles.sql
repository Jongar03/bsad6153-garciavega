-- Run as owner. Set the password privately, never in this file.
BEGIN;
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_reader') THEN
        CREATE ROLE app_reader LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE
            NOREPLICATION NOBYPASSRLS;
    END IF;
END
$$;
GRANT USAGE ON SCHEMA public TO app_reader;
GRANT SELECT ON public.league, public.team, public.match TO app_reader;
ALTER TABLE public.league ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.team ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.match ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS app_reader_select ON public.league;
CREATE POLICY app_reader_select ON public.league FOR SELECT TO app_reader USING (true);
DROP POLICY IF EXISTS app_reader_select ON public.team;
CREATE POLICY app_reader_select ON public.team FOR SELECT TO app_reader USING (true);
DROP POLICY IF EXISTS app_reader_select ON public.match;
CREATE POLICY app_reader_select ON public.match FOR SELECT TO app_reader USING (true);
-- Grant access when the sync's metadata tables have been created.
DO $$
BEGIN
    IF to_regclass('public.sync_runs') IS NOT NULL THEN
        GRANT SELECT ON public.sync_runs TO app_reader;
    END IF;
    IF to_regclass('public.sync_state') IS NOT NULL THEN
        GRANT SELECT ON public.sync_state TO app_reader;
    END IF;
END
$$;
COMMIT;

-- db/roles.sql: who may do what in your database (Week 2, extended in Week 6).
--
-- NEVER PUT A PASSWORD IN THIS FILE. It is committed to GitHub.
-- Create each role here without a password, then set the password separately
-- in the Supabase SQL editor (and nowhere in your repository):
--
--     alter role app_reader with password '...long random password...';
--
-- Then put the role's connection string in .env as APP_DATABASE_URL.
--
-- Week 2: a read-only role for the website, chatbot, and golden-question checker.
-- create role app_reader login;
-- grant usage on schema public to app_reader;
-- grant select on <your data tables> to app_reader;
--
-- Week 3: add sync_runs to the grant above when you create it.
--
-- Week 6: the agent's own role (see the Week 6 page for the exact grants).
-- create role agent_writer login;
-- grant usage on schema public to agent_writer;
-- grant select on <your data tables>, sync_runs, agent_runs, agent_proposals to agent_writer;
-- grant insert on agent_runs, agent_proposals to agent_writer;
-- grant update on agent_runs to agent_writer;
--
-- Week 6: the one write your website may do, which covers only the review columns.
-- grant select on agent_runs, agent_proposals to app_reader;
-- grant update (status, reviewed_at, reviewer_note) on agent_proposals to app_reader;
