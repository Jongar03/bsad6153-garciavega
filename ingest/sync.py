"""Sync API-Football into PostgreSQL. Default scope: league 39, seasons 2023/2024.

python ingest/sync.py --dry-run  # fetch/validate/compare, roll back all changes
python ingest/sync.py            # commit data and checkpoints together
"""
import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from uuid import uuid4

import psycopg
from psycopg import sql
import requests
from dotenv import load_dotenv

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ingest.fetch import retry_delay
from ingest.load import prepare_rows

ROOT = Path(__file__).resolve().parents[1]
TABLES = {
    "league": ("league_id", "name", "country"),
    "team": ("team_id", "name"),
    "match": ("match_id", "league_id", "home_team_id", "away_team_id",
              "season", "match_date", "status", "home_goals", "away_goals"),
}
STATE_SQL = """
CREATE TABLE IF NOT EXISTS public.sync_state (
    league_id integer NOT NULL,
    season integer NOT NULL,
    last_success_at timestamptz NOT NULL,
    last_full_sync_at timestamptz NOT NULL,
    PRIMARY KEY (league_id, season)
);
ALTER TABLE public.sync_state ENABLE ROW LEVEL SECURITY;
GRANT SELECT ON public.sync_state TO app_reader;
DROP POLICY IF EXISTS app_reader_select ON public.sync_state;
CREATE POLICY app_reader_select ON public.sync_state FOR SELECT TO app_reader USING (true);
"""


class SyncError(Exception):
    """Messages are fixed safe summaries, never raw provider responses."""


class FixtureClient:
    def __init__(self, key):
        self.key = key
        self.session = requests.Session()
        self.last_request = None

    def get(self, params):
        for attempt in range(5):
            if self.last_request is not None:
                time.sleep(max(0, 6.1 - (time.monotonic() - self.last_request)))
            self.last_request = time.monotonic()
            delay = retry_delay(None, attempt)
            try:
                response = self.session.get(
                    "https://v3.football.api-sports.io/fixtures", params=params,
                    headers={"x-apisports-key": self.key}, timeout=(10, 60),
                    allow_redirects=False,
                )
                if response.status_code == 429 or 500 <= response.status_code <= 599:
                    delay = retry_delay(response.headers.get("Retry-After"), attempt)
                elif response.status_code != 200:
                    raise SyncError("API rejected the request; check credentials and plan access.")
                else:
                    try:
                        payload = response.json()
                    except ValueError:
                        raise SyncError("API returned invalid JSON.") from None
                    if not isinstance(payload, dict):
                        raise SyncError("API returned an invalid response wrapper.")
                    errors = payload.get("errors")
                    if errors:
                        if not isinstance(errors, dict) or "rateLimit" not in errors:
                            raise SyncError("API reported an error; check quota and season/filter access.")
                    else:
                        return payload
            except requests.RequestException:
                pass  # Retry transport errors without exposing URLs or headers.
            if attempt < 4:
                print(f"Temporary API failure; retry {attempt + 1}/4 in {delay:.0f}s.")
                time.sleep(delay)
        raise SyncError("API failed after five attempts.")


def request_plan(league, season, state, latest_date, now, force_full=False):
    params = {"league": league, "season": season, "timezone": "UTC"}
    full = force_full or state is None or now - state[1] >= timedelta(days=7)
    if not full:
        # A future fixture date must never advance the successful-run watermark.
        anchor = state[0].date()
        if latest_date is not None:
            anchor = min(anchor, latest_date)
        params.update({"from": (anchor - timedelta(days=7)).isoformat(),
                       "to": (now.date() + timedelta(days=14)).isoformat()})
    return params, full


def validate_payload(payload, league, season):
    rows = payload.get("response")
    paging = payload.get("paging")
    if (not isinstance(rows, list) or not isinstance(paging, dict)
            or paging.get("current") != 1 or paging.get("total") != 1
            or payload.get("results") != len(rows) or payload.get("errors")):
        raise SyncError("Incomplete or invalid fixture response; nothing committed.")
    for row in rows:
        if (not isinstance(row, dict) or not isinstance(row.get("league"), dict)
                or row["league"].get("id") != league
                or row["league"].get("season") != season):
            raise SyncError("Fixture outside the requested league/season.")
    return len(rows)


def upsert_sql(table, schema="public"):
    columns = TABLES[table]
    key, fields = columns[0], columns[1:]
    return sql.SQL("""
        INSERT INTO {}.{} AS target ({}) VALUES ({})
        ON CONFLICT ({}) DO UPDATE SET {}, last_updated_at = clock_timestamp()
        WHERE ({}) IS DISTINCT FROM ({})
        RETURNING (xmax = 0) AS inserted
    """).format(
        sql.Identifier(schema), sql.Identifier(table),
        sql.SQL(", ").join(map(sql.Identifier, columns)),
        sql.SQL(", ").join(sql.Placeholder() for _ in columns), sql.Identifier(key),
        sql.SQL(", ").join(sql.SQL("{} = EXCLUDED.{}").format(sql.Identifier(f), sql.Identifier(f)) for f in fields),
        sql.SQL(", ").join(sql.SQL("target.{}").format(sql.Identifier(f)) for f in fields),
        sql.SQL(", ").join(sql.SQL("EXCLUDED.{}").format(sql.Identifier(f)) for f in fields),
    )


def upsert_rows(conn, rows, schema="public"):
    counts = {}
    for table, batch in zip(TABLES, rows):
        inserted = updated = 0
        statement = upsert_sql(table, schema)
        for row in batch:
            result = conn.execute(statement, row).fetchone()
            if result is not None:
                inserted += int(result[0])
                updated += int(not result[0])
        counts[table] = {"inserted": inserted, "updated": updated}
    return counts


def synchronize(conn, client, league, seasons, force_full=False, progress=None):
    # Transaction-scoped lock prevents this script's concurrent runs from racing.
    if not conn.execute("SELECT pg_try_advisory_xact_lock(6153, 3)").fetchone()[0]:
        raise SyncError("Another sync is running; try again later.")
    conn.execute(STATE_SQL)
    now = datetime.now(timezone.utc)
    fetched, plans = 0, []
    with tempfile.TemporaryDirectory(prefix="football_sync_") as directory:
        for season in seasons:
            state = conn.execute("""SELECT last_success_at, last_full_sync_at
                FROM public.sync_state WHERE league_id = %s AND season = %s""",
                (league, season)).fetchone()
            latest = conn.execute("""SELECT max(match_date AT TIME ZONE 'UTC')::date
                FROM public.match WHERE league_id = %s AND season = %s""",
                (league, season)).fetchone()[0]
            params, full = request_plan(league, season, state, latest, now, force_full)
            print("Request:", json.dumps(params), "mode:", "full" if full else "overlap")
            payload = client.get(params)
            count = validate_payload(payload, league, season)
            if full and count == 0:
                raise SyncError("Full season response is empty; verify season access.")
            fetched += count
            if progress is not None:
                progress['records_fetched'] = fetched
            Path(directory, f"fixtures_{season}.json").write_text(json.dumps(payload), encoding="utf-8")
            plans.append((season, full))
        # Small incremental batches (including zero rows) are valid.
        rows = prepare_rows(Path(directory), minimum_matches=0)
    counts = upsert_rows(conn, rows)
    for season, full in plans:
        conn.execute("""INSERT INTO public.sync_state
            (league_id, season, last_success_at, last_full_sync_at)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (league_id, season) DO UPDATE
            SET last_success_at = EXCLUDED.last_success_at,
                last_full_sync_at = CASE WHEN %s THEN EXCLUDED.last_full_sync_at
                    ELSE sync_state.last_full_sync_at END""",
            (league, season, now, now, full))
    return {"records_fetched": fetched, "records_inserted": sum(c["inserted"] for c in counts.values()),
            "records_updated": sum(c["updated"] for c in counts.values()), "tables": counts}


def finish_run(conn, run_id, status, counts, error=None, schema='public'):
    conn.execute(sql.SQL('''UPDATE {}.sync_runs SET finished_at = clock_timestamp(),
        status = %s, records_fetched = %s, records_inserted = %s,
        records_updated = %s, error_message = %s WHERE run_id = %s
        AND finished_at IS NULL''').format(sql.Identifier(schema)),
        (status, counts.get('records_fetched', 0), counts.get('records_inserted', 0),
         counts.get('records_updated', 0), error, run_id))


def logged_sync(conn, client, args, schema='public'):
    """Persist the start first; commit successful data and its result atomically."""
    run_id = uuid4()
    progress = {'records_fetched': 0}
    conn.execute(sql.SQL('''INSERT INTO {}.sync_runs
        (run_id, status, trigger, is_dry_run, error_message)
        VALUES (%s, 'failed', %s, %s, %s)''').format(sql.Identifier(schema)),
        (run_id, args.trigger, args.dry_run, 'Run started; completion not yet recorded.'))
    conn.commit()
    print('run_id:', run_id, flush=True)
    try:
        if not client.key:
            raise SyncError('API_FOOTBALL_KEY is missing.')
        conn.execute("SET LOCAL statement_timeout = '60s'")
        result = synchronize(conn, client, args.league, list(dict.fromkeys(args.seasons)), args.full, progress)
        if args.dry_run:
            conn.rollback()
            finish_run(conn, run_id, 'partial', {'records_fetched': result['records_fetched']},
                       'Dry-run preview; all data and checkpoint writes rolled back.', schema)
        else:
            finish_run(conn, run_id, 'success', result, schema=schema)
        conn.commit()
        return result
    except BaseException as error:
        conn.rollback()
        # Never persist raw psycopg/requests exceptions, which can contain secrets.
        message = str(error) if isinstance(error, SyncError) else (
            'Run interrupted.' if isinstance(error, (KeyboardInterrupt, SystemExit))
            else 'Sync failed; transaction rolled back. Sensitive error details omitted.')
        finish_run(conn, run_id, 'failed', progress, message, schema)
        conn.commit()
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--league", type=int, default=39)
    parser.add_argument("--seasons", type=int, nargs="+", default=[2023, 2024])
    parser.add_argument("--full", action="store_true", help="Reconcile entire configured seasons")
    parser.add_argument("--dry-run", action="store_true", help="Fetch and test writes, then roll back")
    parser.add_argument('--trigger', choices=('schedule', 'manual'), default='manual')
    args = parser.parse_args()
    if args.league < 1 or any(s < 1900 or s > datetime.now(timezone.utc).year for s in args.seasons):
        parser.error("Choose a positive league ID and valid seasons.")
    load_dotenv(ROOT / ".env")
    url, key = os.getenv("DATABASE_URL"), os.getenv("API_FOOTBALL_KEY")
    if not url:
        print("[FAIL] DATABASE_URL must be set; no database log can be written.")
        return 1
    client = FixtureClient(key)
    try:
        with psycopg.connect(url, connect_timeout=10) as conn:
            conn.execute((ROOT / 'db/sync_runs.sql').read_text(encoding='utf-8'))
            conn.commit()
            result = logged_sync(conn, client, args)
        print(json.dumps(result, indent=2))
        print("[ok] Dry run rolled back; counts are proposed changes." if args.dry_run else "[ok] Sync committed.")
        return 0
    except SyncError as error:
        print(f"[FAIL] {error}")
    except (psycopg.Error, ValueError, OSError, KeyError, TypeError):
        print("[FAIL] Database, validation, or local I/O error; no changes committed. Details hidden.")
    finally:
        client.session.close()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
