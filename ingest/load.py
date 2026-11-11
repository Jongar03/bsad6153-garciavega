"""Load saved API-Football fixtures. Run from the project folder:

    python ingest/load.py --dry-run  # inspect data without connecting
    python ingest/load.py            # insert data into Supabase

Defaults to the latest complete football download. Use --raw-dir to select
a specific download. Existing IDs are skipped, not updated (Milestone 2).
"""

import argparse
from datetime import datetime
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# SQL text stays constant; data values are passed separately via %s placeholders.
INSERT_LEAGUE = """
    INSERT INTO public.league (league_id, name, country)
    VALUES (%s, %s, %s) ON CONFLICT (league_id) DO NOTHING
"""
INSERT_TEAM = """
    INSERT INTO public.team (team_id, name)
    VALUES (%s, %s) ON CONFLICT (team_id) DO NOTHING
"""
INSERT_MATCH = """
    INSERT INTO public.match
        (match_id, league_id, home_team_id, away_team_id, season,
         match_date, status, home_goals, away_goals)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (match_id) DO NOTHING
"""
COUNT_ROWS = """
    SELECT (SELECT count(*) FROM public.league),
           (SELECT count(*) FROM public.team),
           (SELECT count(*) FROM public.match)
"""


def latest_download():
    for folder in sorted((ROOT / "data" / "raw").glob("football_*"), reverse=True):
        summary = folder / "summary.json"
        if summary.is_file():
            info = json.loads(summary.read_text(encoding="utf-8"))
            if info.get("complete") is True and list(folder.glob("fixtures_*.json")):
                return folder
    raise ValueError("No complete football download found in data/raw.")


def integer(value):
    if type(value) is not int:
        raise ValueError("Expected a whole number.")
    return value


def required_text(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Expected nonempty text.")
    return value


def goal(value):
    if value is None:
        return None
    if integer(value) < 0:
        raise ValueError("Goals cannot be negative.")
    return value


def prepare_rows(folder):
    leagues, teams, matches = {}, {}, {}
    files = sorted(folder.glob("fixtures_*.json"))
    if not files:
        raise ValueError("No fixture JSON files found in the selected folder.")
    for path in files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        # Failed retry responses contain no usable fixtures.
        if payload.get("errors"):
            continue
        records = payload.get("response")
        if not isinstance(records, list):
            raise ValueError(f"Missing fixture list in {path.name}.")
        for index, record in enumerate(records, start=1):
            try:
                fixture, league = record["fixture"], record["league"]
                home, away = record["teams"]["home"], record["teams"]["away"]
                league_id = integer(league["id"])
                home_id, away_id = integer(home["id"]), integer(away["id"])
                if home_id == away_id:
                    raise ValueError("A team cannot play itself.")
                kickoff = datetime.fromisoformat(fixture["date"].replace("Z", "+00:00"))
                if kickoff.utcoffset() is None:
                    raise ValueError("Kickoff must include a time zone.")
                leagues[league_id] = (league_id, required_text(league["name"]),
                                      required_text(league["country"]))
                for team in (home, away):
                    teams[team["id"]] = (team["id"], required_text(team["name"]))
                match_id = integer(fixture["id"])
                row = (match_id, league_id, home_id, away_id,
                       integer(league["season"]), kickoff,
                       required_text(fixture["status"]["short"]),
                       goal(record["goals"]["home"]), goal(record["goals"]["away"]))
                if match_id in matches and matches[match_id] != row:
                    raise ValueError("Conflicting snapshots of the same match.")
                matches[match_id] = row
            except (KeyError, TypeError, ValueError, AttributeError) as error:
                raise ValueError(f"Invalid fixture in {path.name}, row {index}.") from error
    if len(matches) < 500:
        raise ValueError(f"Found {len(matches)} unique matches; this assignment requires at least 500.")
    return list(leagues.values()), list(teams.values()), list(matches.values())


def load_rows(conn, rows):
    before = conn.execute(COUNT_ROWS).fetchone()
    inserted = []
    # Parents first, then children. The caller commits all tables together.
    with conn.cursor() as cursor:
        for statement, batch in zip((INSERT_LEAGUE, INSERT_TEAM, INSERT_MATCH), rows):
            cursor.executemany(statement, batch)
            inserted.append(cursor.rowcount)
    after = conn.execute(COUNT_ROWS).fetchone()
    return before, after, inserted


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, help="Folder containing fixture JSON files")
    parser.add_argument("--dry-run", action="store_true", help="Validate files without database access")
    args = parser.parse_args()
    try:
        folder = args.raw_dir if args.raw_dir is not None else latest_download()
        rows = prepare_rows(folder)
    except (OSError, ValueError) as error:
        print(f"[FAIL] Could not prepare data: {error}")
        return 1
    print(f"Source: {folder.name}")
    print(f"Prepared: {len(rows[0])} leagues, {len(rows[1])} teams, {len(rows[2])} matches.")
    if args.dry_run:
        print("[ok] Local validation passed. No database connection was made.")
        return 0

    import psycopg
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("[FAIL] Set DATABASE_URL in your project's .env file.")
        return 1
    try:
        # One transaction: either all inserts succeed or none are saved.
        with psycopg.connect(url, connect_timeout=10) as conn:
            before, after, inserted = load_rows(conn, rows)
    except psycopg.Error as error:
        # Never print server error text, connection strings, or passwords.
        print(f"[FAIL] Database load failed ({type(error).__name__}). No inserts from this run were committed.")
        print("Check the connection with scripts/check_db.py and confirm db/schema.sql was run.")
        return 1
    for label, old, new, added in zip(("league", "team", "match"), before, after, inserted):
        print(f"{label}: before={old}, after={new}, inserted={added}")
    print("[ok] Load committed. Run again: inserted should be 0 for every table.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
