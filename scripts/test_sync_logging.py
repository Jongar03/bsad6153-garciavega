"""Verify run logging and atomicity using only temporary PostgreSQL tables."""
import argparse
import os
from pathlib import Path
import sys
from unittest.mock import Mock, patch

import psycopg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ingest.sync import logged_sync


def main():
    load_dotenv(ROOT / '.env')
    try:
        with psycopg.connect(os.environ['DATABASE_URL'], connect_timeout=10) as conn:
            ddl = (ROOT / 'db/sync_runs.sql').read_text(encoding='utf-8').split('ALTER TABLE')[0]
            conn.execute(ddl.replace('CREATE TABLE IF NOT EXISTS public.sync_runs', 'CREATE TEMP TABLE sync_runs'))
            conn.execute('CREATE TEMP TABLE probe (value integer)')
            conn.commit()
            args = argparse.Namespace(trigger='manual', dry_run=False, league=39, seasons=[2024], full=False)
            def successful(c, client, league, seasons, full, progress):
                c.execute('INSERT INTO pg_temp.probe VALUES (1)')
                return {'records_fetched': 1, 'records_inserted': 1, 'records_updated': 0}
            def failed(c, client, league, seasons, full, progress):
                c.execute('INSERT INTO pg_temp.probe VALUES (2)')
                progress['records_fetched'] = 7
                raise ValueError('secret-must-not-be-logged')
            with patch('ingest.sync.synchronize', side_effect=successful):
                logged_sync(conn, Mock(key='fake'), args, 'pg_temp')
            with patch('ingest.sync.synchronize', side_effect=failed):
                try:
                    logged_sync(conn, Mock(key='fake'), args, 'pg_temp')
                except ValueError:
                    pass
                else:
                    raise AssertionError('Expected failure')
            args.dry_run = True
            with patch('ingest.sync.synchronize', side_effect=successful):
                logged_sync(conn, Mock(key='fake'), args, 'pg_temp')
            rows = conn.execute('''SELECT status, records_fetched, records_inserted,
                records_updated, error_message, finished_at IS NOT NULL
                FROM pg_temp.sync_runs ORDER BY started_at''').fetchall()
            assert len(rows) == 3
            assert rows[0][:4] == ('success', 1, 1, 0)
            assert rows[1][:4] == ('failed', 7, 0, 0)
            assert rows[2][:4] == ('partial', 1, 0, 0)
            assert all(row[5] for row in rows)
            assert 'secret-must-not-be-logged' not in str(rows)
            assert conn.execute('SELECT count(*) FROM pg_temp.probe').fetchone()[0] == 1
            conn.rollback()
            try:
                conn.execute("UPDATE pg_temp.sync_runs SET status = 'invalid'")
            except psycopg.errors.CheckViolation:
                conn.rollback()
            else:
                raise AssertionError('Status CHECK missing')
        print('PASS: success persisted; failure rolled back data but retained log; dry run rolled back data; secrets omitted; status CHECK enforced.')
        print('All test tables were temporary. No production records or history changed.')
        return 0
    except Exception as error:
        print('FAIL:', type(error).__name__, '(details hidden)')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
