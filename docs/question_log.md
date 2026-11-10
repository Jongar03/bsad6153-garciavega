# Running question list

Recorded on 10 November 2026 from `docs/baseline_log.md` and the Milestone 2 discussion. Continue adding questions here for the Milestone 3 golden-question set, including questions the data cannot answer.

## Scope and evidence

The database contains 760 Premier League matches from the 2023 and 2024 seasons, 23 teams, and one league. Season labels are not calendar years: the 2024 season includes matches in 2025. These records describe historical results, not current form or coverage of all five intended leagues.

Results below come from the student's Supabase query results: Questions 1 and 2 were reported in chat; Questions 3–5 were shown in screenshots. Query numbers refer to `db/queries.sql`.

## Questions answered in Milestone 2

| Question | Origin | Answer and limits |
| --- | --- | --- |
| 1. Which teams won the most home matches in the saved 2023 and 2024 seasons? | Baseline: home versus away performance. | Liverpool led with 29 home wins. Newcastle's 24 surprised the student because they had forgotten how well Newcastle performed. Counts combine both seasons and are not win rates. |
| 2. Which teams won the most away matches in the saved 2023 and 2024 seasons? | Baseline: home versus away performance. | Arsenal led with 22 away wins. Counts combine both seasons; teams do not necessarily have the same number of appearances. |
| 3. What happened when Arsenal played Liverpool during those seasons? | Baseline: previous meetings between two teams. | Liverpool 1–1 Arsenal (23 December 2023); Arsenal 3–1 Liverpool (4 February 2024); Arsenal 2–2 Liverpool (27 October 2024); Liverpool 2–2 Arsenal (11 May 2025). Arsenal won once and three games were draws. |
| 4. Which teams scored the most goals in their last five saved matches? | Baseline: goals in the last five games. | Brighton led with 13, followed by Liverpool with 11. Brighton's window was 26 April–25 May 2025. Some teams' last saved matches ended in May 2024, so the date ranges differ. |
| 5. Which teams scored the most goals during May 2025? | Follow-up to Question 4: compare scoring during a shared calendar period. | Brentford and Brighton tied on 10 goals. Brentford played five matches and Brighton played four. The UTC date filter includes 1 May and excludes 1 June; equal time windows do not guarantee equal match counts. |

## Broader and unanswered questions

| Question | Current status | What is needed next? |
| --- | --- | --- |
| Which match should I analyze? | This is the baseline decision. The five queries provide evidence, but do not yet rank upcoming matches. | Upcoming fixtures, a defined analysis date, and agreed ranking criteria. |
| How does each team perform at home versus away? | Partly answered by Questions 1 and 2. Win totals alone do not compare equal opportunities. | Compare games played, win rates, draws, losses, and goals using the existing match records. |
| Was a key player injured? | Unanswered: the modeled data does not contain injury records. | Dated injury and availability reports linked to players and teams, plus a definition of a key player. |
| Does table position matter? | Unanswered; no analysis of position versus later results has been performed. | Reconstruct standings before each match from earlier results, account for competition rules and any point deductions, then define and test the relationship with later outcomes. Final standings must not stand in for pre-match positions. |
| Is the current streak real or just luck? | Unanswered. Historical results can describe streaks, but cannot establish the cause of a streak on their own. | Define the streak and evaluation date, compare against a statistical baseline, consider opponent strength, and quantify uncertainty. Current claims also need newer data. |
| Who usually scores first? | Unanswered: final scores do not reveal goal order. | Goal-event timestamps and scoring-team IDs for each match. |

## Maintaining this list

Add new questions as they arise, along with their origin, whether the data can answer them, and any missing evidence. Keep historical result windows explicit. In Milestone 3, turn selected questions into repeatable checks with expected answers or clearly stated limitations.
