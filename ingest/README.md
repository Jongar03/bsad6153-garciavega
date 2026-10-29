# Football data download

Run from the project folder:

```powershell
.venv\Scripts\python.exe ingest/fetch.py
```

The project already includes requests and python-dotenv. Put your API-Football key in `.env` as `API_FOOTBALL_KEY=your-key`. Never put a real key in source code. The football-data.org competition list is public, so this script does not send it a key.

## What each part does

1. `main()` reads settings and your key, and makes a new timestamped folder inside `data/raw/`.
2. `Client.get()` sends requests. Only requests to API-Football receive your key, in `x-apisports-key`.
3. It waits at least 6.1 seconds between requests. A temporary error (429, 5xx, timeout or connection failure) gets up to four retries after the first attempt. It waits 60, 120, 240, then 480 seconds, or longer if the service asks via `Retry-After`. Permanent errors are logged and skipped. API-Football errors inside an otherwise successful reply are also checked.
4. `collect()` first downloads football-data.org competitions, then API-Football matches for Premier League (league 39), one season at a time. It stops after collecting at least 500 different matches, or after trying all selected seasons. Whole season responses are kept, so the result can exceed 500.
5. `valid_fixture()` checks that a match has an ID, date, league ID, league name and country. Missing required fields are counted and skipped. Optional values such as unknown scores may remain null. Duplicate IDs count only once.
6. `save()` stores the returned JSON without removing any records. Error JSON replies are saved too. A separate `summary.json` reports record counts, invalid records, duplicate records, failed requests, and retries. `fetch.log` records progress.

## Pagination and scope

These URLs are two services, not two record types. This implementation chooses **fixtures (matches)** as the main records and **competitions** as related information.

The API-Football `/fixtures` request supports league and season filters, but has no documented page parameter. Consequently this script loops through seasons rather than inventing page numbers or cursors. It verifies that each season reply reports one page; an unexpected or missing page count is reported as a failure. Other API-Football requests, such as `/players`, use page numbers; that does not apply to fixtures. football-data.org's competition list also has no documented pagination.

By default the script tries seasons Year-2, Year-3, Year-4, matching the documented Free-plan window (2024, 2023, 2022 in 2026). Choose an explicit scope with:

```powershell
.venv\Scripts\python.exe ingest/fetch.py --league 39 --seasons 2024 2023 2022 --target 500
.venv\Scripts\python.exe -m unittest ingest.test_football_fetch -v
```

The target must be at least 500. A smaller competition or unavailable seasons may not yield enough records. The script then exits with status 1 and reports an incomplete run. It also reports incomplete if required fields, requests, or a competition candidate are missing. It never claims to have downloaded records it did not receive.

## How the services relate

Matches contain an API-Football league ID. football-data.org has its own competition IDs. Do not join these IDs directly. `relationship_candidates.json` records competitions whose name and country match exactly (ignoring case). These are **unconfirmed candidates**, not a provider-guaranteed cross-reference. Review them before joining data in a database. The full public competition list is saved, including competitions unrelated to the downloaded matches. A successful download does not mean those relationships have been independently verified.

## Limits and official sources

- [API-Football reference](https://www.api-football.com/documentation_v3): authentication, fixtures filters, IDs and response structure.
- [API-Football league download guide](https://www.api-football.com/news/post/how-to-get-all-data-from-a-league-with-api-football): league 39 example, season access, and endpoint-specific pagination.
- [API-Football quota guide](https://www.api-football.com/news/post/how-to-optimize-api-sports-calls-and-quota-usage): Free plan allows 100 requests/day and 10/minute. Allowance is shared with other uses of your key; reruns consume more requests.
- [football-data.org quickstart](https://www.football-data.org/documentation/quickstart): competition list and response fields.
- [football-data.org policies](https://docs.football-data.org/general/v4/policies.html): unauthenticated clients can access areas and competition lists, up to 100 requests per 24 hours. Match/team requests require separate access; this script does not fetch those.

`data/raw/` was already in `.gitignore` and remains excluded. Each run has its own folder. Request headers and API keys are not logged. JSON formatting is indented for readability, but response contents are preserved.

The previous appliance-import fetcher and its guide are preserved as `fetch_comtrade.py` and `README_comtrade.md`. Its existing tests now import the preserved module. The football fetcher does not modify the appliance samples or database.
