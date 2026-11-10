# Suggested title

Milestone 2: load football results into PostgreSQL and answer business questions

## What this pull request does

Adds a three-table football schema with source primary keys, foreign keys, constraints, and audit timestamps. Loads saved JSON into `league`, `team`, and `match` with parameterized inserts and duplicate prevention, and adds five business queries plus a running question list.

## Validation

- Student confirmed the database connection and created the three tables in Supabase.
- First load inserted 1 league, 23 teams, and 760 matches.
- Second load inserted 0 rows in each table and preserved all totals.
- Student ran all five queries in Supabase and shared the results.
- The assistant's local dry run prepared the same 1 / 23 / 760 records without connecting to Supabase.
- A fresh-database rerun, complete repository-history secret review, and video recording have not been performed as part of final submission preparation.

## Checklist

- [ ] I read every change in this pull request before submitting it.
- [ ] No secrets anywhere: not in code, not in `.env.example`, not in screenshots, not in Git history.
- [ ] I ran it from a clean start, and it works on top of my previous milestone.
- [x] Documentation for this milestone is updated (`docs/`).
- [ ] Screencast link: pending recording.

## AI review log

# Milestone 2 AI review log

Draft for the pull request's AI review log. Based on the work and verification recorded in our conversation. Review this wording before submission; it does not claim that every code change has already been read. The pull request checklist and screencast remain to be completed.

## 1. Database design and schema

### Direct: what I asked the AI to do

I asked the AI to explain Milestone 2 in simple steps and wait until each step was finished before moving on. I asked it to check my Milestone 1 files and help design tables for the football data before writing SQL.

### Read: what I checked in its output

I opened the generated schema in Notepad and followed a guided walkthrough of its three table definitions. We covered primary keys, foreign keys, required fields, data types, nullable scores, nonnegative goals, and the rule that a team cannot play itself. We also covered the audit timestamp defaults, the fact that `last_updated_at` does not automatically change on updates, SQL comments, and `BEGIN`/`COMMIT`. This records a guided review, not an independent audit of every change in the pull request.

### Verify: the evidence that it works

I ran `python scripts/check_db.py` and received `[ok] Connected using DATABASE_URL`. I ran the schema in Supabase, selected its option to enable Row Level Security, received `Success. No rows returned`, and confirmed that `league`, `team`, and `match` appeared in the Table Editor.

### Decide: what I accepted, changed, or rejected, and why

I changed the AI's suggested table name `leagues` to `league` because I preferred singular table names, and accepted matching singular names for `team` and `match`. I accepted separate home-team and away-team references in `match` because each football game has exactly one of each, and accepted the required audit timestamps on all three tables.

## 2. JSON loader

### Direct: what I asked the AI to do

I asked the AI to create `ingest/load.py` to transform the saved football JSON into database rows, load at least 500 matches, and avoid duplicates when run twice.

### Read: what I checked in its output

I opened `ingest/load.py` in Notepad and followed a guided walkthrough. We covered the project path, parameterized inserts using `%s`, `ON CONFLICT DO NOTHING`, before/after counts, selection of the latest complete download, value validation, preparation of unique rows, parent-first insertion, dry-run mode, reading `DATABASE_URL` from `.env`, and transaction rollback on failure. We also covered the error handling that avoids printing credentials. I examined the output from both actual runs; the final output and script-entry lines were summarized. This was a guided explanation of the code, not independent testing of every error path.

### Verify: the evidence that it works

I ran `python ingest/load.py` twice:

| Table | First run: before / after / inserted | Second run: before / after / inserted |
| --- | --- | --- |
| `league` | 0 / 1 / 1 | 1 / 1 / 0 |
| `team` | 0 / 23 / 23 | 23 / 23 / 0 |
| `match` | 0 / 760 / 760 | 760 / 760 / 0 |

Both runs reported that the load committed. I also confirmed that the match rows were visible in Supabase's Table Editor. These checks show successful loading and no duplicates on the second run; they do not prove that every possible error case has been tested.

### Decide: what I accepted, changed, or rejected, and why

I accepted `ON CONFLICT DO NOTHING` for Milestone 2 because the assignment allows it to prevent duplicates. Updating existing records is deferred to Milestone 3. I accepted using the saved Premier League data rather than claiming that the database already contains all five intended leagues.

## 3. Business queries and question list

### Direct: what I asked the AI to do

I asked to work through Part D one question at a time. We used my baseline questions about home and away performance, previous meetings, and recent goals, and added a May 2025 scoring comparison using a common date window. I also asked the AI to save a running list of answered and unanswered questions.

### Read: what I checked in its output

I reviewed the plain-English explanation accompanying each query, ran the SQL in Supabase, and shared the results. We discussed JOINs, grouping, the time filter, the difference between season labels and calendar years, and the different date ranges in each team's last five saved matches. A full line-by-line review of the more complex queries remains pending.

### Verify: the evidence that it works

- Query 1: Liverpool led with 29 home wins; Newcastle had 24.
- Query 2: Arsenal led with 22 away wins.
- Query 3: Arsenal and Liverpool had four meetings: 1–1, 3–1 to Arsenal, 2–2, and 2–2.
- Query 4: Brighton led with 13 goals in its last five saved matches.
- Query 5: Brentford and Brighton tied on 10 goals in May 2025, from five and four games respectively.

I reported the first two results in chat and provided screenshots for the remaining three. The SQL includes multiple JOINs, GROUP BY, an explicit match-date filter, and the surprising-result comment.

### Decide: what I accepted, changed, or rejected, and why

I chose Newcastle's result as the surprising finding: its 24 home wins surprised me because I had forgotten how well it performed. I accepted keeping both the last-five-games query and the May 2025 query because they answer different comparisons. We retained limitations in the question list rather than claiming the existing data can answer injury, goal-order, or current-form questions.

## Before submitting

- Read all changed files and finish the code reviews noted above; update this log to describe what was actually checked.
- Complete the pull request template's checklist only after each check is performed, including secret checks and the clean-start run.
- Record and link the 4–6 minute screencast.
- Copy the reviewed log into the Milestone 2 pull request description, or include a link to this file if the instructor permits it.


## Scope and limitations

The data covers Premier League matches from the 2023 and 2024 seasons, not all five intended leagues or current form. Milestone 2 skips existing IDs; it does not update changed records. The student enabled RLS through Supabase when running the schema; the local schema file does not reproduce that dashboard setting.
