-- Football database: see docs/schema.md for the design and relationships.
-- Source IDs are primary keys, which enforce UNIQUE and NOT NULL.
-- IF NOT EXISTS permits reruns but does not migrate existing tables.
BEGIN;

-- One row per API-Football league.
CREATE TABLE IF NOT EXISTS public.league (
    league_id integer PRIMARY KEY,
    name text NOT NULL,
    country text NOT NULL,
    first_seen_at timestamptz NOT NULL DEFAULT now(),
    last_updated_at timestamptz NOT NULL DEFAULT now()
);

-- One row per API-Football team.
CREATE TABLE IF NOT EXISTS public.team (
    team_id integer PRIMARY KEY,
    name text NOT NULL,
    first_seen_at timestamptz NOT NULL DEFAULT now(),
    last_updated_at timestamptz NOT NULL DEFAULT now()
);

-- One row per match, linked to its league and both teams.
CREATE TABLE IF NOT EXISTS public.match (
    match_id integer PRIMARY KEY,
    league_id integer NOT NULL REFERENCES public.league (league_id),
    home_team_id integer NOT NULL REFERENCES public.team (team_id),
    away_team_id integer NOT NULL REFERENCES public.team (team_id),
    season integer NOT NULL,
    match_date timestamptz NOT NULL,
    status text NOT NULL,
    home_goals integer,
    away_goals integer,
    first_seen_at timestamptz NOT NULL DEFAULT now(),
    last_updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT different_teams CHECK (home_team_id <> away_team_id),
    CONSTRAINT nonnegative_home_goals CHECK (home_goals >= 0),
    CONSTRAINT nonnegative_away_goals CHECK (away_goals >= 0)
);

-- Missing scores remain NULL; zero means a known score of zero goals.
-- Audit defaults apply on insertion. Milestone 3 update logic must explicitly
-- maintain last_updated_at while preserving first_seen_at.
COMMIT;
