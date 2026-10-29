# Data dictionary

Checked on 29 October 2026. Evidence is limited to `ingest/fetch.py`, football files under `data/sample/` and `data/raw/`, and the official documentation and terms linked below. Counts describe the saved files, not every record the providers might supply. Documentation and terms were re-read for this revision. “Not documented by the API” means no explicit rule was found in the official pages reviewed; “The terms do not address this” means no explicit provision was found for that particular point, not that permission is granted. Assessments and the owner’s description of local access are labeled separately.

## 1. Source

The current script uses **two** football providers, not just API-Football:

| Provider | Endpoint actually used | Authentication | Official references |
| --- | --- | --- | --- |
| API-Football | `GET https://v3.football.api-sports.io/fixtures?league=39&season=2024` and the same request with `season=2023` | The script reads `API_FOOTBALL_KEY` and sends it in the `x-apisports-key` header. | [Dashboard](https://dashboard.api-football.com/), [documentation](https://www.api-football.com/documentation-v3), [search-readable documentation](https://www.api-football.com/documentation_v3), [terms](https://www.api-football.com/terms) |
| football-data.org | `GET https://api.football-data.org/v4/competitions`, without query parameters | No authentication header is sent for this request. The competition documentation explicitly permits listing competitions without a token; its authenticated example uses `X-Auth-Token`. | [Competition documentation](https://docs.football-data.org/general/v4/competition.html), [terms, under “Terms & Conditions”](https://www.football-data.org/client/register) |

Evidence for the actual football requests is in the script and `data/raw/football_20261029T022046963348Z/`: two fixture responses with 380 records each, `competitions_attempt1.json` with 190 records, and one locally generated `relationship_candidates.json` row. The summary lists 2022 among the requested seasons, but there is no 2022 response: the script stops after reaching its match target. Embedded teams and leagues do not prove that `/teams` or `/leagues` was called.

## 2. What one record means

- **Match:** One `response[]` row describes one football fixture between a home team and an away team; all 760 saved fixtures have status `FT` (finished), although the endpoint also supports unfinished fixtures.
- **Competition:** One `competitions[]` row describes one competition in football-data.org, with its area and available season information.
- **Relationship candidate:** One row proposes that an API-Football league and a football-data.org competition are the same, based only on matching name and country.
- **Embedded league/team:** A `league` or `teams.home`/`teams.away` object describes the league or participating team within a match, not an independently downloaded record.

Response wrappers, summaries and logs describe requests or runs; they are not extra matches or competitions. Sample rows are excerpts and are not added to raw counts.

## 3. Fields

A dotted name means “look inside this object”: `fixture.id` means `id` inside `fixture`. Types below describe saved JSON values: integer = whole number, string = text, boolean = `true`/`false`, and `null` = no value.

For “can it be missing”, the count includes an absent field or parent, JSON `null`, blank text, or an empty array/object. Zero and `false` are **not** empty. Counts include every saved raw row of the stated type, including repeated snapshots; they do not include sample rows. A zero count is an observation, not a promise that the field is always required by the API. None of the 16 fields below is absent or blank in its applicable rows; all counted empty values are explicit `null`.

| Name | Type | Example value from raw data | What it means | Can it be missing? |
| --- | --- | --- | --- | --- |
| Match: `fixture.id` | integer | `1035037` | Match identifier. | 0 / 760 |
| Match: `fixture.date` | string | `2023-08-11T19:00:00+00:00` | Match date and time, including its UTC offset. | 0 / 760 |
| Match: `fixture.referee` | string | `C. Pawson` | Referee name as supplied. | 0 / 760 |
| Match: `fixture.status.short` | string | `FT` | Short match status; this value means finished. | 0 / 760 |
| Match: `fixture.status.extra` | integer or null | `5` (match `1208070`); `null` (`1035037`) | Additional time played in a half, described in the documentation's 3.9.3 changelog. | Yes: 433 / 760 null |
| Match: `league.id` | integer | `39` | API-Football league identifier. | 0 / 760 |
| Match: `league.season` | integer | `2023` | Season label, not necessarily the calendar year of every game. | 0 / 760 |
| Match: `teams.home.id` | integer | `44` | Home team's API-Football identifier. | 0 / 760 |
| Match: `teams.away.id` | integer | `50` | Away team's API-Football identifier. | 0 / 760 |
| Match: `teams.home.winner` | boolean or null | `false` (`1035037`); `null` (`1035039`) | Whether the home team won; in this saved dataset draws have null flags. | Yes: 175 / 760 null |
| Match: `goals.home` | integer | `0` | Home team's goal count. | 0 / 760 |
| Match: `goals.away` | integer | `3` | Away team's goal count. | 0 / 760 |
| Competition: `id` | integer | `2193` | football-data.org competition identifier. | 0 / 190 |
| Competition: `name` | string | `Africa Cup Of Nations - Qualification` | Competition name. | 0 / 190 |
| Competition: `lastUpdated` | string | `2026-07-23T15:18:54Z` | Supplied update timestamp; exactly which changes advance it: **Not documented by the API** in the [competition documentation](https://docs.football-data.org/general/v4/competition.html). | 0 / 190 |
| Candidate: `confirmed` | boolean | `false` | The script marks its proposed match as unconfirmed. | 0 / 1; false is a value |

Football examples come from the 2023 fixture file unless otherwise stated; competition examples come from its first row. Field meanings use these records and the official [fixture documentation](https://www.api-football.com/documentation_v3) and [competition documentation](https://docs.football-data.org/general/v4/competition.html).

## 4. Identifiers and relationships

- **Matches:** `fixture.id` has 760 distinct values in 760 rows. The [fixture documentation](https://www.api-football.com/documentation_v3) says fixture identifiers are unique and do not change; the script uses this field to remove repeat matches within a run.
- **Competitions:** `id` has 190 distinct values in 190 rows. It belongs to football-data.org, so it must not be treated as an API-Football ID. Permanent stability of competition IDs: **Not documented by the API** in the [competition documentation](https://docs.football-data.org/general/v4/competition.html).
- **Embedded links:** Match `1035037` is in API-Football league `39`, season `2023`, with home team `44` (Burnley) and away team `50` (Manchester City). These objects are present inside that match; no separate team catalogue was fetched by this script.
- **Cross-provider link:** The single candidate connects league `39` to competition `2021`: both say `Premier League` and `England`. They appear to be the same competition based on the evidence in our data, but no official cross-provider mapping confirms it in the sources reviewed. Its `confirmed` value remains `false`. A proposed identifier for a candidate is the pair of provider-specific IDs; this is a local design suggestion, not a provider guarantee. Competition `2021` describes a current season starting `2026-08-21`, so it is not a season record for either downloaded match season.

## 5. Update behavior

The following findings distinguish refresh frequency, first publication, and later corrections:

- **Fixture refresh frequency:** “This endpoint is updated every 15 seconds.” The [Fixtures documentation](https://www.api-football.com/documentation_v3) provides this interval; the [terms, Service & data](https://www.api-football.com/terms) say it is indicative rather than guaranteed. The documentation also describes daily checks for fixtures with an undecided date, postponed fixtures and cancelled fixtures.
- **When new fixtures first appear:** The [Leagues documentation](https://www.api-football.com/documentation_v3) says, “For `Cup` competitions, fixtures are automatically added when the two participating teams are known.” It also explains that new seasons are added automatically when available and may lag the official calendar announcement. A fixed publication deadline for new league fixtures: **Not documented by the API**.
- **Correction timing for completed matches:** A deadline for correcting an already completed match: **Not documented by the API** in the [Fixtures documentation](https://www.api-football.com/documentation_v3). Its discussion of results becoming available up to 48 hours after some matches concerns initial result availability, not a correction guarantee.
- **Competition refresh frequency:** **Not documented by the API** in the [football-data.org competition documentation](https://docs.football-data.org/general/v4/competition.html).
- **Competition `lastUpdated`:** The field appears in examples, but exactly which changes advance it is **Not documented by the API** in the [competition documentation](https://docs.football-data.org/general/v4/competition.html).

**Changes between our downloads:** Not yet tested. We only have one download, so we can't tell whether records change. This would require a second download later. Here “one download” means one football collection run containing the two season files and the competition file.

**Proposed detection method, not implemented:** Re-fetch the same league/season scope, compare IDs with the previous successful run, and call an unseen ID “new to our stored copy”; compare all saved fields for matching IDs to detect changes. Repeat this for competition IDs, using `lastUpdated` as a clue rather than the only check; retain both snapshots, and flag a disappearing row for review instead of assuming deletion. This cannot detect fixtures outside the requested league/seasons or changes that occur and disappear between runs.

The current script writes a new timestamped raw folder, saves replies, and removes duplicate match IDs only within the current run. It does not compare with prior folders, schedule future executions, or use an update cursor. Its default seasons are the UTC current year minus two, three and four; its target can stop collection early.

## 6. Surprises

These are measured observations, not guesses about their causes:

1. **Null does not always mean a broken match record.** All 175 drawn matches have null home and away winner flags (175 nulls in each field); match `1035039`, Bournemouth–West Ham, is `1–1` with both flags null. Do not turn null into a loss. The conditions under which `teams.home.winner` and `teams.away.winner` are null: **Not documented by the API** in the [Fixtures documentation](https://www.api-football.com/documentation_v3); examples do not establish a general rule.
2. **A finished game can lack added-time information.** All 760 matches are `FT`, but `fixture.status.extra` is null in 433; match `1035037` is an example, whereas `1208070` has `5`. The changelog documents the field, so its absence from some older examples does not make it undocumented; the [documentation](https://www.api-football.com/documentation_v3) does not explain the cause of these 433 null values, and only the provider could confirm it.
3. **Entire score categories are null.** `score.extratime.home` and `score.penalty.home` are each null in 760 / 760 matches; match `1035037` illustrates both. Preserve null rather than replacing it with zero. The exact conditions under which `score.extratime` and `score.penalty` contain null home/away values: **Not documented by the API** in the [Fixtures documentation](https://www.api-football.com/documentation_v3); the response examples contain nulls but do not explain a general rule.
4. **A competition need not have a current season.** Exactly 1 / 190 has `currentSeason=null`: competition `2161`, `Indian Super League`, also has `numberOfAvailableSeasons=0` and `lastUpdated="2022-07-26T11:21:45Z"`. This does not prove the real competition has stopped.
5. **A “complete” run can exceed its target and skip a listed season.** `summary.json` reports target `500`, actual matches `760`, and seasons `[2024,2023,2022]`, but only two 380-row fixture responses exist. The script checks the target after a whole season, explaining this; “complete” is the script's own test, not proof of worldwide or all-season coverage.

Duplicate checks found zero repeated fixture IDs among the 760 football matches and zero repeated competition IDs among the 190 competitions.

## 7. Data-use ethics check

**What do the terms allow and forbid: storage, display, commercial use and attribution?**

The following checks concern our downloaded data. Short exact quotations are included where possible; longer clauses are explicitly summarized to stay within quotation limits. Each entry links to the reviewed terms.

| Provider and point | Finding and supporting wording |
| --- | --- |
| API-Football — local storage | **The terms do not address this** explicitly for downloaded copies. [Terms](https://www.api-football.com/terms). |
| API-Football — local retention period | **The terms do not address this**. [Terms](https://www.api-football.com/terms). |
| API-Football — commercial rights | No commercial rights in the competitions are granted: “We does not grant any commercial rights on such competitions.” [Service & data](https://www.api-football.com/terms). |
| API-Football — redistribution | Unauthorised resale is prohibited: “The resale of our data without permission is not permitted.” This sentence does not grant permission for other distribution. [Terms of use](https://www.api-football.com/terms). |
| API-Football — display/publication | Clause summary: the service does not supply a publication licence; users must obtain necessary rights-holder permissions. [Service & data](https://www.api-football.com/terms). |
| API-Football — attribution | **The terms do not address this** as an explicit attribution requirement. [Terms](https://www.api-football.com/terms). |
| football-data.org — local storage | **The terms do not address this** as explicit permission to keep downloaded copies. [Terms & Conditions](https://www.football-data.org/client/register). |
| football-data.org — local retention period | **The terms do not address this** as a period for retaining our local files. Clause 4.6 discusses account/data deletion after cancellation, and clause 9.1 restricts continued site/service use; neither specifies a local retention period (clause summaries). [Sections 4.6 and 9.1](https://www.football-data.org/client/register). |
| football-data.org — commercial use | **The terms do not address this** as an explicit general commercial-use permission for downloaded data; paid access alone is not such a grant. [Terms & Conditions](https://www.football-data.org/client/register). |
| football-data.org — redistribution | **The terms do not address this** as a general redistribution licence; do not treat that silence as permission. [Terms & Conditions](https://www.football-data.org/client/register). |
| football-data.org — display | Clause summaries: section 9.1 prohibits continued reference to obtained football data on a site/service after cancellation; section 9.2 requires permission for copyrighted graphics. [Sections 9.1–9.2](https://www.football-data.org/client/register). |
| football-data.org — attribution | Exact sentence: 'You agree to include the following attribution to Football-Data in your app or website: "Football data provided by the Football-Data.org API".' [Section 7.1](https://www.football-data.org/client/register). |

**Does this describe real, identifiable people, and did they expect this use?** Match records include referee names such as `C. Pawson`, attached to a specific date and match, which can help identify a person; the records reviewed are not player profiles. Assessment: appearing in public match data does not mean a referee agreed to every later use, so we should use these names only where needed to explain the match and avoid unsupported personal judgments.

**What is the worst realistic harm if our stored copy leaked or were misread?** Risk assessment, not an observed incident: a leaked copy could be redistributed beyond the permitted use, and stale or misread results could support harmful claims about a named referee or poor decisions based on incorrect scores. This is a practical assessment of possible harm, not a claim that an incident has happened or a measured prediction.

**Who should be allowed to read or change these records?** Recommendation: give read access only to project members who need it, let the ingestion process create raw snapshots, and restrict corrections to designated maintainers while preserving the original evidence. Current setup, as stated by the project owner: “I have not set up any access controls beyond my own computer.” The reader/editor restrictions above are recommendations, not protections already implemented.

### Remaining limits and next steps

- Documentation gaps remain for competition ID stability, competition refresh frequency, what advances competition `lastUpdated`, completed-match correction deadlines, a fixed first-publication deadline for league fixtures, and the general null rules for winner/extra-time/penalty fields.
- The terms are silent on the specific local-storage/retention and other permission points identified in the table; silence is not permission.
- The cross-provider competition link is an evidence-based inference, not an official mapping.
- A second football download is needed to test changes between runs; only the provider could explain the cause of the 433 missing added-time values.
- Consent and harm are assessments; the proposed access restrictions have not been implemented beyond the owner's computer setup.

The change-detection method and access rules above are proposals, not claims about existing functionality or contractual approval.
