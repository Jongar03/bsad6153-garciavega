"""Validate golden questions, or execute their SQL as app_reader and save answers."""
import argparse
import csv
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ['id', 'question', 'category', 'reference_sql', 'correct_behavior', 'source']
CATEGORIES = {'lookup', 'aggregate', 'trend', 'compare', 'should_decline'}


def read_questions(path):
    with path.open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != FIELDS:
            raise ValueError('CSV headers do not match the required six columns.')
        rows = list(reader)
    if len(rows) < 15:
        raise ValueError('At least 15 questions are required.')
    ids = set()
    for row in rows:
        if None in row or any(row.get(f) is None for f in FIELDS):
            raise ValueError('Malformed CSV row.')
        identity = row['id']
        if identity in ids or not identity.startswith('Q') or not identity[1:].isdigit():
            raise ValueError('Question IDs must be unique Q-prefixed numbers.')
        ids.add(identity)
        if row['category'] not in CATEGORIES or row['source'] not in {'baseline', 'other'}:
            raise ValueError(f'{identity}: invalid category or source.')
        if not row['question'].strip() or not row['correct_behavior'].strip():
            raise ValueError(f'{identity}: missing question or correct behavior.')
        query = row['reference_sql'].strip()
        if row['category'] == 'should_decline':
            if query:
                raise ValueError(f'{identity}: should_decline must have empty SQL.')
        else:
            # Restrict this curated file to a single SELECT/WITH statement.
            # Database role permissions and read-only transactions enforce safety.
            body = query[:-1] if query.endswith(';') else query
            if not body or ';' in body or body.split()[0].upper() not in {'SELECT', 'WITH'}:
                raise ValueError(f'{identity}: expected one SELECT/WITH statement.')
    if sum(r['source'] == 'baseline' for r in rows) < 8:
        raise ValueError('At least eight baseline questions are required.')
    if sum(r['category'] == 'should_decline' for r in rows) < 3:
        raise ValueError('At least three should_decline questions are required.')
    return rows


def fingerprint(rows):
    return hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()


def json_value(value):
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)  # Preserve PostgreSQL numeric precision.
    return str(value)


def compare_results(current, baseline):
    if baseline.get('question_set_sha256') != current['question_set_sha256']:
        raise ValueError('Question set changed; use a baseline from the same question set.')
    if not baseline.get('passed'):
        raise ValueError('The baseline must be a successful reference check.')
    old = {r['id']: r for r in baseline['results']}
    changed, unchanged, failed = [], [], []
    for result in current['results']:
        if result['status'] == 'decline_not_executed':
            continue
        if result['status'] != 'pass':
            failed.append(result['id'])
        elif (result['columns'], result['rows']) != (old[result['id']]['columns'], old[result['id']]['rows']):
            changed.append(result['id'])
        else:
            unchanged.append(result['id'])
    new_scheduled = sorted(set(current['successful_scheduled_run_ids'])
                           - set(baseline['successful_scheduled_run_ids']))
    return {'changed': changed, 'unchanged': unchanged, 'failed': failed,
            'new_successful_scheduled_run_ids': new_scheduled,
            'at_least_two_more_scheduled_syncs': len(new_scheduled) >= 2}


def execute_questions(rows, url):
    import psycopg
    results = []
    with psycopg.connect(url, connect_timeout=10) as conn:
        conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        conn.execute("SET LOCAL statement_timeout = '30s'")
        conn.execute("SET LOCAL TIME ZONE 'UTC'")
        user, snapshot_at = conn.execute('SELECT current_user, clock_timestamp()').fetchone()
        if user != 'app_reader':
            raise ValueError('APP_DATABASE_URL must connect as app_reader; refusing another role.')
        scheduled = [str(r[0]) for r in conn.execute("""SELECT run_id FROM public.sync_runs
            WHERE status = 'success' AND trigger = 'schedule'
              AND NOT is_dry_run AND finished_at IS NOT NULL ORDER BY run_id""")]
        for question in rows:
            identity = question['id']
            if question['category'] == 'should_decline':
                results.append({'id': identity, 'status': 'decline_not_executed'})
                print(f'{identity}: DECLINE expectation recorded (no SQL; no chatbot tested).')
                continue
            try:
                # Nested transaction is a savepoint: one bad query won't prevent others.
                with conn.transaction():
                    cursor = conn.execute(question['reference_sql'])
                    columns = [c.name for c in cursor.description]
                    answer = cursor.fetchmany(10001)
                    if not answer or not any(any(v is not None for v in row) for row in answer):
                        raise ValueError('empty_result')
                    if len(answer) > 10000:
                        raise ValueError('result_limit_exceeded')
                results.append({'id': identity, 'status': 'pass', 'columns': columns,
                                'rows': answer})
                print(f'{identity}: PASS ({len(answer)} result rows)')
            except (psycopg.Error, ValueError) as error:
                # Never save raw connection/server exception text.
                code = str(error) if isinstance(error, ValueError) else type(error).__name__
                results.append({'id': identity, 'status': 'fail', 'error': code})
                print(f'{identity}: FAIL ({code})')
    return {'checked_at_utc': snapshot_at, 'database_user': user,
            'question_set_sha256': fingerprint(rows),
            'successful_scheduled_run_ids': scheduled,
            'passed': all(r['status'] != 'fail' for r in results), 'results': results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--questions', type=Path, default=ROOT / 'evals/golden_questions.csv')
    parser.add_argument('--validate-only', action='store_true', help='Check CSV without reading credentials or connecting')
    parser.add_argument('--output', type=Path, help='New JSON evidence file; existing files are never overwritten')
    parser.add_argument('--compare', type=Path, help='Compare to a previous successful JSON baseline')
    args = parser.parse_args()
    try:
        rows = read_questions(args.questions)
        print(f'CSV valid: {len(rows)} questions; '
              f"{sum(r['source'] == 'baseline' for r in rows)} baseline; "
              f"{sum(r['category'] == 'should_decline' for r in rows)} should-decline.")
        if args.validate_only:
            print('No database connection made. SQL execution remains unverified.')
            return 0
        output = args.output or ROOT / 'evals/results' / (
            'reference_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.json')
        if output.exists():
            raise ValueError('Output already exists; choose a new name to preserve evidence.')
        baseline = None
        if args.compare:
            baseline = json.loads(args.compare.read_text(encoding='utf-8'))
            if baseline.get('question_set_sha256') != fingerprint(rows) or not baseline.get('passed'):
                raise ValueError('Choose a successful baseline for this exact question set.')
        from dotenv import load_dotenv
        load_dotenv(ROOT / '.env')
        url = os.getenv('APP_DATABASE_URL')
        if not url:
            raise ValueError('Set APP_DATABASE_URL; no admin-connection fallback is allowed.')
        result = execute_questions(rows, url)
        # Normalize datetimes, tuples, and numeric values before comparisons.
        result = json.loads(json.dumps(result, default=json_value))
        if baseline:
            result['comparison'] = compare_results(result, baseline)
            print(json.dumps(result['comparison'], indent=2))
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open('x', encoding='utf-8') as handle:
            json.dump(result, handle, indent=2)
            handle.write('\n')
        print(f'Evidence saved: {output}')
        return 0 if result['passed'] else 1
    except ValueError as error:
        # These local validation messages contain no credentials.
        print(f'[FAIL] {error}')
    except Exception as error:
        print(f'[FAIL] {type(error).__name__}; details hidden. Check configuration and file access.')
    return 1


if __name__ == '__main__':
    sys.exit(main())
