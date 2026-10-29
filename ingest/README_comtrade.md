# ingest/

## Fetch the Week 1 data

Set `COMTRADE_API_KEY` in the project `.env` file, then run from the project folder:

```powershell
.venv\Scripts\python.exe ingest/fetch.py --write-sample
```

The default queries 24 calendar months ending with the previous month. For a reproducible window:

```powershell
.venv\Scripts\python.exe ingest/fetch.py --end 202609 --months 24
.venv\Scripts\python.exe -m unittest ingest.test_fetch -v
```

Each run creates a separate `data/raw/<UTC timestamp>/` folder containing untouched JSON response payloads, `fetch.log`, and `summary.json`. The optional `--write-sample` flag replaces `data/sample/comtrade_sample.json` with five trade records and seven related product definitions. Raw downloads are ignored by Git; the small sample is intended for version control.

### API behavior checked on October 28, 2026

- Authentication: the [documented subscription-key query parameter](https://uncomtrade.org/docs/un-comtrade-api/) reads `COMTRADE_API_KEY` from `.env`. Request URLs and exception bodies are never logged, because they can contain this key.
- Pagination: partition by month (`period=YYYYMM`), using the authenticated `/data/v1/get/C/M/HS` endpoint. No invented offset/cursor parameters. Each query requests up to 100,000 rows; a response reaching that cap is flagged as potentially truncated and the run fails validation rather than silently accepting it.
- Scope: U.S. reporter 842, imports (`M`), all partners (partner filter omitted), and total second partner/customs/transport dimensions. Product codes: 841810, 841821, 841829 (refrigerators/combinations), 845011, 845012, 845019 (household washing machines), and 842211 (household dishwashers). These are selected finished-appliance subcategories, not every product in the broader headings. World totals and individual partners must not be summed together.
- Related resource: the independent [HS product catalogue](https://comtradeapi.un.org/files/v1/app/reference/HS.json). Trade `cmdCode` joins to catalogue `id`. Preserve each trade record's `classificationCode`; the combined catalogue alone does not establish equivalence between HS editions.
- Limits: the [basic plan](https://uncomtrade.org/docs/subscriptions/) advertises 500 calls/day and 100,000 records/call. The client leaves at least 1.1 seconds between requests. It retries 429 and 5xx responses and transport errors up to five total attempts, respecting numeric or HTTP-date `Retry-After` values and otherwise using exponential backoff. Daily quota is shared with other runs; repeated runs can exhaust it.
- Failures: timeouts use a 10-second connection and 60-second read limit. Missing identity/value fields are counted and skipped from validation, while raw responses remain intact. An unrecovered partition, malformed catalogue, invalid record, possible truncation, or fewer than 500 valid unique trade records produces a nonzero exit code. Empty months are explicitly reported; [publication has no fixed schedule](https://uncomtrade.org/docs/data-availability/).
- Public use: attribute UN Comtrade. The sample is limited, and the planned free analytical dashboard follows the [redistribution exemptions](https://uncomtrade.org/docs/re-dissemination-of-data/). Raw downloads are not published.

The script downloads evidence only; it does not create database tables or perform Week 3 database synchronization.

Code that moves data from your API into your database. You build it with your AI agent, one piece per week:

| Week | File | What it does |
|---|---|---|
| 1 | `fetch.py` | Calls your API: authentication, pagination, rate limits, retries. Saves raw JSON to `data/raw/`. |
| 2 | `load.py` | Turns the raw JSON into rows in your tables, using parameterized queries. Running it twice must not create duplicates. |
| 3 | `sync.py` | Combines fetch and load into one incremental, idempotent sync that GitHub Actions runs on a schedule and records in `sync_runs`. |

Only the sync connects as the database owner (`DATABASE_URL`). Everything else uses a limited role.
