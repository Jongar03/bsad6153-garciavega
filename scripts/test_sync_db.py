"""Test upserts on disposable PostgreSQL TEMP tables, never production rows."""
from datetime import datetime, timezone
from pathlib import Path
import os
import sys

import psycopg
from psycopg import sql
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ingest.sync import upsert_rows


def main():
    load_dotenv(Path(__file__).resolve().parents[1] / '.env')
    try:
        with psycopg.connect(os.environ['DATABASE_URL'], connect_timeout=10) as conn:
            for table in ('league', 'team', 'match'):
                conn.execute(sql.SQL('CREATE TEMP TABLE {} (LIKE public.{} INCLUDING ALL) ON COMMIT DROP')
                             .format(sql.Identifier(table), sql.Identifier(table)))
            rows = ([(39, 'Test league', 'Test country')], [(1, 'Home'), (2, 'Away')],
                    [(1, 39, 1, 2, 2024, datetime(2024, 1, 1, tzinfo=timezone.utc), 'FT', None, 0)])
            first = upsert_rows(conn, rows, 'pg_temp')
            assert sum(v['inserted'] for v in first.values()) == 4
            before = conn.execute('SELECT first_seen_at, last_updated_at FROM pg_temp.match').fetchone()
            again = upsert_rows(conn, rows, 'pg_temp')
            assert all(v == {'inserted': 0, 'updated': 0} for v in again.values())
            assert conn.execute('SELECT first_seen_at, last_updated_at FROM pg_temp.match').fetchone() == before
            rows[2][0] = (*rows[2][0][:-2], 2, 0)
            changed = upsert_rows(conn, rows, 'pg_temp')
            assert changed['match'] == {'inserted': 0, 'updated': 1}
            after = conn.execute('SELECT first_seen_at, last_updated_at FROM pg_temp.match').fetchone()
            assert after[0] == before[0] and after[1] > before[1]
            conn.execute('SAVEPOINT broken_run')
            try:
                conn.execute("UPDATE pg_temp.team SET name = 'should roll back' WHERE team_id = 1")
                conn.execute('UPDATE pg_temp.match SET home_goals = -1')
                raise AssertionError('Expected score constraint failure')
            except psycopg.errors.CheckViolation:
                conn.execute('ROLLBACK TO SAVEPOINT broken_run')
            assert conn.execute('SELECT name FROM pg_temp.team WHERE team_id = 1').fetchone()[0] == 'Home'
            conn.rollback()
        print('PASS: insert=4; rerun insert=0/update=0; correction update=1; timestamps correct; rollback restored data.')
        print('Only disposable temporary tables were used. No production rows changed.')
        return 0
    except Exception as error:
        print('FAIL:', type(error).__name__, '(details hidden)')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
