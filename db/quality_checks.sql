-- Milestone 3: read-only checks run by the student in Supabase on 2026-11-16.
-- Query IDs correspond to docs/data_quality.md. Reruns produce fresh measurements.

-- Q01: Football data-table row counts.
SELECT CURRENT_TIMESTAMP AS checked_at,
       'league' AS table_name, COUNT(*) AS row_count
FROM public.league
UNION ALL
SELECT CURRENT_TIMESTAMP, 'team', COUNT(*) FROM public.team
UNION ALL
SELECT CURRENT_TIMESTAMP, 'match', COUNT(*) FROM public.match
ORDER BY table_name;

-- Q02: Null counts and score null rates.
SELECT
    CURRENT_TIMESTAMP AS checked_at,
    COUNT(*) AS total_matches,
    COUNT(*) FILTER (WHERE match_date IS NULL) AS missing_dates,
    COUNT(*) FILTER (WHERE status IS NULL) AS missing_status,
    COUNT(*) FILTER (WHERE home_goals IS NULL) AS missing_home_goals,
    COUNT(*) FILTER (WHERE away_goals IS NULL) AS missing_away_goals,
    ROUND(100.0 * COUNT(*) FILTER (WHERE home_goals IS NULL)
        / NULLIF(COUNT(*), 0), 2) AS home_goals_null_percent,
    ROUND(100.0 * COUNT(*) FILTER (WHERE away_goals IS NULL)
        / NULLIF(COUNT(*), 0), 2) AS away_goals_null_percent
FROM public.match;

-- Q03: Natural-ID duplicates and a same-fixture/different-ID heuristic.
SELECT CURRENT_TIMESTAMP AS checked_at,
       'Repeated match ID' AS check_name, COUNT(*) AS duplicate_groups
FROM (
    SELECT match_id FROM public.match
    GROUP BY match_id HAVING COUNT(*) > 1
) AS duplicates
UNION ALL
SELECT CURRENT_TIMESTAMP, 'Same fixture with different IDs', COUNT(*)
FROM (
    SELECT league_id, season, home_team_id, away_team_id, match_date
    FROM public.match
    GROUP BY league_id, season, home_team_id, away_team_id, match_date
    HAVING COUNT(DISTINCT match_id) > 1
) AS duplicates;

-- Q04: Invalid values, incomplete finished scores, and orphan references.
SELECT
    CURRENT_TIMESTAMP AS checked_at,
    COUNT(*) FILTER (WHERE m.home_goals < 0 OR m.away_goals < 0) AS negative_scores,
    COUNT(*) FILTER (WHERE m.home_team_id = m.away_team_id) AS team_playing_itself,
    COUNT(*) FILTER (WHERE btrim(m.status) = '') AS blank_status,
    COUNT(*) FILTER (
        WHERE m.status IN ('FT', 'AET', 'PEN')
          AND (m.home_goals IS NULL OR m.away_goals IS NULL)
    ) AS finished_matches_missing_scores,
    COUNT(*) FILTER (WHERE l.league_id IS NULL) AS missing_league,
    COUNT(*) FILTER (WHERE home.team_id IS NULL) AS missing_home_team,
    COUNT(*) FILTER (WHERE away.team_id IS NULL) AS missing_away_team
FROM public.match AS m
LEFT JOIN public.league AS l ON m.league_id = l.league_id
LEFT JOIN public.team AS home ON m.home_team_id = home.team_id
LEFT JOIN public.team AS away ON m.away_team_id = away.team_id;

-- Q05: Coverage of intended leagues, including leagues with no matches.
WITH target_leagues (league_id, league_name) AS (
    VALUES (39, 'Premier League'), (140, 'La Liga'),
           (78, 'Bundesliga'), (135, 'Serie A'), (61, 'Ligue 1')
)
SELECT CURRENT_TIMESTAMP AS checked_at,
       t.league_name, COUNT(m.match_id) AS match_count,
       MIN(m.match_date) AS earliest_match, MAX(m.match_date) AS latest_match
FROM target_leagues AS t
LEFT JOIN public.match AS m ON m.league_id = t.league_id
GROUP BY t.league_id, t.league_name
ORDER BY match_count DESC, t.league_name;

-- Q06: Operational-table row counts.
SELECT CURRENT_TIMESTAMP AS checked_at,
       'sync_runs' AS table_name, COUNT(*) AS row_count
FROM public.sync_runs
UNION ALL
SELECT CURRENT_TIMESTAMP, 'sync_state', COUNT(*)
FROM public.sync_state
ORDER BY table_name;

-- Q07: Missing or blank important parent fields.
SELECT CURRENT_TIMESTAMP AS checked_at,
       'league.name' AS field, COUNT(*) AS total_rows,
       COUNT(*) FILTER (WHERE name IS NULL OR btrim(name) = '') AS missing_or_blank
FROM public.league
UNION ALL
SELECT CURRENT_TIMESTAMP, 'league.country', COUNT(*),
       COUNT(*) FILTER (WHERE country IS NULL OR btrim(country) = '')
FROM public.league
UNION ALL
SELECT CURRENT_TIMESTAMP, 'team.name', COUNT(*),
       COUNT(*) FILTER (WHERE name IS NULL OR btrim(name) = '')
FROM public.team;

-- Q08: Same-name/different-ID candidates, ignoring case and outer whitespace.
-- A shared name is a review candidate, not proof of duplicate identity.
SELECT CURRENT_TIMESTAMP AS checked_at,
       'Same league name and country, different IDs' AS check_name,
       COUNT(*) AS duplicate_groups
FROM (
    SELECT lower(btrim(name)), lower(btrim(country))
    FROM public.league
    GROUP BY lower(btrim(name)), lower(btrim(country))
    HAVING COUNT(DISTINCT league_id) > 1
) AS duplicates
UNION ALL
SELECT CURRENT_TIMESTAMP, 'Same team name, different IDs', COUNT(*)
FROM (
    SELECT lower(btrim(name))
    FROM public.team
    GROUP BY lower(btrim(name))
    HAVING COUNT(DISTINCT team_id) > 1
) AS duplicates;

-- Q09: Observed status categories and date ranges by season.
SELECT CURRENT_TIMESTAMP AS checked_at,
       season, status, COUNT(*) AS match_count,
       MIN(match_date) AS earliest_match, MAX(match_date) AS latest_match
FROM public.match
GROUP BY season, status
ORDER BY season, status;
