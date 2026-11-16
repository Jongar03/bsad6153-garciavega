-- db/queries.sql: business questions answered with SQL (Week 2).
--
-- At least five queries, each answering a question from your baseline log.
-- Put the question in plain English in a comment above each query.
-- Across the five, use: two JOINs, one GROUP BY, one filter by time,
-- and one query whose answer surprised you (explain why in the comment).
--
-- Question 1: Which teams won the most home matches in the saved 2023 and
-- 2024 seasons? This explores the baseline question about home vs away form.
-- Counts combine both seasons, so teams with more home matches have more
-- opportunities to win. These are win totals, not win rates or current form.
-- Surprising result (observed in Supabase): Newcastle had 24 home wins across
-- the two seasons. This surprised me because I had forgotten how well they
-- performed. Liverpool led the results with 29 home wins.
SELECT
    t.name AS team,
    COUNT(*) FILTER (WHERE m.home_goals > m.away_goals) AS home_wins
FROM public.match AS m
JOIN public.team AS t ON t.team_id = m.home_team_id
WHERE m.season IN (2023, 2024)
  AND m.status = 'FT'
GROUP BY t.team_id, t.name
ORDER BY home_wins DESC, t.name;

-- Question 2: Which teams won the most away matches in the saved 2023 and
-- 2024 seasons? Compare with Question 1 to explore home vs away performance.
-- Counts combine both seasons and measure total wins, not win rates.
SELECT
    t.name AS team,
    COUNT(*) FILTER (WHERE m.away_goals > m.home_goals) AS away_wins
FROM public.match AS m
JOIN public.team AS t ON t.team_id = m.away_team_id
WHERE m.season IN (2023, 2024)
  AND m.status = 'FT'
GROUP BY t.team_id, t.name
ORDER BY away_wins DESC, t.name;

-- Question 3: What happened when Arsenal played Liverpool in the saved
-- 2023 and 2024 seasons? This answers the baseline question about past meetings.
-- Join team twice to display both names, including either home/away arrangement.
SELECT
    m.match_date,
    home.name AS home_team,
    away.name AS away_team,
    m.home_goals,
    m.away_goals
FROM public.match AS m
JOIN public.team AS home ON home.team_id = m.home_team_id
JOIN public.team AS away ON away.team_id = m.away_team_id
WHERE m.season IN (2023, 2024)
  AND m.status = 'FT'
  AND (
      (home.name = 'Arsenal' AND away.name = 'Liverpool')
      OR (home.name = 'Liverpool' AND away.name = 'Arsenal')
  )
ORDER BY m.match_date;

-- Question 4: Which teams scored the most goals in their last five saved
-- matches? This answers the baseline question about goals in the last five games.
-- Each match contributes one row for each team, with that team's own goals.
-- These are historical saved matches, not current form. Teams can have different
-- latest match dates (for example, teams relegated after the earlier season).
-- Show the date range and count so that the comparison's scope is visible.
WITH team_games AS (
    SELECT match_id, match_date, home_team_id AS team_id, home_goals AS goals
    FROM public.match
    WHERE status = 'FT' AND season IN (2023, 2024)
    UNION ALL
    SELECT match_id, match_date, away_team_id AS team_id, away_goals AS goals
    FROM public.match
    WHERE status = 'FT' AND season IN (2023, 2024)
), ranked_games AS (
    SELECT *, ROW_NUMBER() OVER (
        PARTITION BY team_id ORDER BY match_date DESC, match_id DESC
    ) AS game_number
    FROM team_games
)
SELECT
    t.name AS team,
    COUNT(*) AS matches_counted,
    CASE WHEN COUNT(r.goals) = COUNT(*) THEN SUM(r.goals) END AS goals_scored,
    MIN(r.match_date) AS first_match,
    MAX(r.match_date) AS last_match
FROM ranked_games AS r
JOIN public.team AS t ON t.team_id = r.team_id
WHERE r.game_number <= 5
GROUP BY t.team_id, t.name
ORDER BY goals_scored DESC NULLS LAST, t.name;

-- Question 5: Which teams scored the most goals during May 2025?
-- Follow-up to the baseline question about recent scoring: compare a shared
-- calendar period rather than each team's potentially different last five dates.
-- Use UTC boundaries, including May 1 and excluding June 1.
-- Teams may play different numbers of games, so show matches_counted too.
WITH may_matches AS (
    SELECT *
    FROM public.match
    WHERE status = 'FT'
      AND match_date >= TIMESTAMPTZ '2025-05-01 00:00:00+00'
      AND match_date < TIMESTAMPTZ '2025-06-01 00:00:00+00'
), team_goals AS (
    SELECT home_team_id AS team_id, home_goals AS goals FROM may_matches
    UNION ALL
    SELECT away_team_id AS team_id, away_goals AS goals FROM may_matches
)
SELECT
    t.name AS team,
    COUNT(*) AS matches_counted,
    CASE WHEN COUNT(g.goals) = COUNT(*) THEN SUM(g.goals) END AS goals_scored
FROM team_goals AS g
JOIN public.team AS t ON t.team_id = g.team_id
GROUP BY t.team_id, t.name
ORDER BY goals_scored DESC NULLS LAST, t.name;
