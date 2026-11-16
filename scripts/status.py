"""Read freshness and seven-day change totals using APP_DATABASE_URL."""
import json
import os
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]


def main():
    load_dotenv(ROOT / '.env')
    url = os.getenv('APP_DATABASE_URL')
    if not url:
        print('[FAIL] APP_DATABASE_URL is missing.')
        return 1
    try:
        with psycopg.connect(url, connect_timeout=10, row_factory=dict_row) as conn:
            conn.execute('SET TRANSACTION READ ONLY')
            print('Database user:', conn.execute('SELECT current_user AS name').fetchone()['name'])
            summary = conn.execute((ROOT / 'db/status.sql').read_text(encoding='utf-8')).fetchone()
            recent = conn.execute('''SELECT run_id, started_at, finished_at, status,
                records_fetched, records_inserted, records_updated, error_message,
                trigger, is_dry_run FROM public.sync_runs
                ORDER BY started_at DESC LIMIT 10''').fetchall()
        print(json.dumps({'summary': summary, 'recent_runs': recent}, default=str, indent=2))
        return 0
    except psycopg.Error:
        print('[FAIL] Could not read sync history; check connection and Part C setup. Details hidden.')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
