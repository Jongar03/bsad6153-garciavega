# Data quality and coverage check

Checked locally on 6 November 2026 using the two `fixtures_39_*_attempt1.json` files in `data/raw/football_20261031T232117466176Z/`. Other snapshots and sample excerpts were excluded to avoid counting the same matches repeatedly. This check covers saved fixture records, not every record available from the providers.

## Winner flags

| Season label | Matches | Draws | Null home winner flags | Null away winner flags |
| --- | ---: | ---: | ---: | ---: |
| 2023 | 380 | 82 | 82 | 82 |
| 2024 | 380 | 93 | 93 | 93 |
| Total | 760 | 175 | 175 | 175 |

Draws were identified by equal home and away goal totals. In this snapshot, all 175 draws have null winner flags for both sides. Null must not be converted into a loss: doing so would penalize teams with more draws. For finished matches, derive win/draw/loss from validated goal totals; retain an unknown outcome when scores or status are unavailable. These observations do not establish the provider's general null rules for every match status.

## Fairness check: representation across intended leagues

The baseline log describes a project spanning Europe's five major football leagues. A coverage comparison of the saved match records found:

| Intended league | Saved matches | Share |
| --- | ---: | ---: |
| Premier League | 760 | 100% |
| La Liga | 0 | 0% |
| Bundesliga | 0 | 0% |
| Serie A | 0 | 0% |
| Ligue 1 | 0 | 0% |

This is a representation/coverage check, not a demographic fairness audit or a measurement of prediction accuracy. Competition listings and separate team exports do not supply missing match histories. No prediction results were evaluated, so equal accuracy across leagues cannot be claimed.

## Implication and safeguards

An agent that assumes five-league coverage could favor Premier League teams or make unsupported comparisons for teams without match histories. Missing coverage must not be treated as poor team performance. Limit recommendations to the verified league and season scope until comparable match data are collected for the other leagues. Require human review of cross-league recommendations and repeat coverage and outcome-label checks after ingestion. Historical seasons alone do not establish current form.

## Mirror paragraph

In my `docs/data_quality.md`, I found that all 175 drawn matches in my 760-match dataset have null winner flags. An agent treating null as a loss would unfairly downgrade teams with more draws. My fairness check also compared coverage across Europe's five major leagues: the Premier League had 760 matches, while the other four had none. An unaware agent could favor English teams or make unsupported cross-league recommendations. Before allowing those recommendations, I would require correct draw handling, comparable league coverage, human review, and a repeated coverage check. This identifies a representation gap, not proven prediction bias.
