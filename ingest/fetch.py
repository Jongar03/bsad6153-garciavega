"""Download API-Football fixtures and football-data.org competitions."""
import argparse
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import json
import logging
import os
from pathlib import Path
import time

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
LOG = logging.getLogger("fetch")


def save(path, payload):
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def retry_delay(value, attempt):
    delay = 60 * 2 ** attempt
    if value:
        try:
            return max(delay, float(value))
        except ValueError:
            try:
                return max(delay, (parsedate_to_datetime(value) - datetime.now(timezone.utc)).total_seconds())
            except (ValueError, TypeError, OverflowError):
                pass
    return delay


class Client:
    """Space requests apart, save replies, and retry temporary failures."""
    def __init__(self, directory):
        self.directory = directory
        self.session = requests.Session()
        self.last_request = None
        self.requests = self.retries = 0
        self.failures = []

    def fail(self, label, reason):
        self.failures.append({"request": label, "reason": reason})
        LOG.error("%s: %s; skipped", label, reason)

    def get(self, url, params, label, headers=None):
        for attempt in range(5):
            if self.last_request is not None:
                time.sleep(max(0, 6.1 - (time.monotonic() - self.last_request)))
            self.last_request = time.monotonic()
            self.requests += 1
            delay = retry_delay(None, attempt)
            try:
                response = self.session.get(url, params=params, headers=headers or {}, timeout=(10, 60))
                status = response.status_code
                try:
                    payload = response.json()
                except ValueError:
                    payload = None
                else:
                    # Save JSON replies, including errors; never save request headers.
                    save(self.directory / f"{label}_attempt{attempt + 1}.json", payload)
                if status == 429 or 500 <= status <= 599:
                    reason = f"HTTP {status}"
                    delay = retry_delay(response.headers.get("Retry-After"), attempt)
                elif status != 200:
                    self.fail(label, f"HTTP {status}")
                    return None
                elif payload is None:
                    reason = "invalid JSON"
                elif isinstance(payload, dict) and payload.get("errors"):
                    # API-Football can report an error inside an HTTP 200 reply.
                    if isinstance(payload["errors"], dict) and "rateLimit" in payload["errors"]:
                        reason = "API rate limit"
                    else:
                        self.fail(label, "API error; see raw response for subscription/quota details")
                        return None
                else:
                    return payload
            except requests.RequestException as exc:
                reason = type(exc).__name__  # Exception text may contain sensitive details.
            LOG.warning("%s: %s, attempt %s/5", label, reason, attempt + 1)
            if attempt < 4:
                self.retries += 1
                LOG.info("Waiting %.1f seconds before retry", delay)
                time.sleep(delay)
        self.fail(label, reason)
        return None


def valid_fixture(row):
    if not isinstance(row, dict):
        return False
    fixture, league = row.get("fixture"), row.get("league")
    return (isinstance(fixture, dict) and type(fixture.get("id")) is int
            and bool(fixture.get("date")) and isinstance(league, dict)
            and type(league.get("id")) is int and isinstance(league.get("name"), str)
            and bool(league["name"]) and isinstance(league.get("country"), str)
            and bool(league["country"]))


def collect(client, key, args):
    seen, leagues, competitions = set(), {}, []
    invalid = duplicates = 0
    payload = client.get("https://api.football-data.org/v4/competitions", {}, "competitions")
    rows = payload.get("competitions") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        if payload is not None:
            client.fail("competitions", "missing competitions list")
    else:
        for row in rows:
            if (isinstance(row, dict) and type(row.get("id")) is int
                    and isinstance(row.get("name"), str) and row["name"]
                    and isinstance(row.get("area"), dict)
                    and isinstance(row["area"].get("name"), str) and row["area"]["name"]):
                competitions.append(row)
            else:
                invalid += 1
                LOG.warning("Skipping competition with missing identity/name/area")
    for season in dict.fromkeys(args.seasons):
        label = f"fixtures_{args.league}_{season}"
        payload = client.get("https://v3.football.api-sports.io/fixtures",
                             {"league": args.league, "season": season}, label,
                             {"x-apisports-key": key})
        if payload is None:
            continue
        rows = payload.get("response") if isinstance(payload, dict) else None
        if not isinstance(rows, list):
            client.fail(label, "missing response list")
            continue
        # /fixtures has no documented page parameter. Never invent one.
        paging = payload.get("paging")
        if not isinstance(paging, dict) or paging.get("current") != 1 or paging.get("total") != 1:
            client.fail(label, "unexpected/missing paging; cannot establish complete season")
            continue
        for row in rows:
            if not valid_fixture(row):
                invalid += 1
                LOG.warning("%s: skipping match with missing required fields", label)
                continue
            identity = row["fixture"]["id"]
            if identity in seen:
                duplicates += 1
                continue
            seen.add(identity)
            leagues[row["league"]["id"]] = row["league"]
        LOG.info("%s: %s unique matches collected", label, len(seen))
        if len(seen) >= args.target:
            break
    # IDs from different providers are unrelated. These are reviewable candidates.
    candidates = []
    for league in leagues.values():
        for competition in competitions:
            if (league["name"].casefold() == competition["name"].casefold()
                    and league["country"].casefold() == competition["area"]["name"].casefold()):
                candidates.append({"api_football_league_id": league["id"],
                                   "football_data_competition_id": competition["id"],
                                   "name": league["name"], "country": league["country"],
                                   "confirmed": False, "method": "exact name and country match"})
    save(client.directory / "relationship_candidates.json", candidates)
    return {"unique_matches": len(seen), "competition_records": len(competitions),
            "relationship_candidates": len(candidates), "invalid_records": invalid,
            "duplicate_records": duplicates,
            "complete": len(seen) >= args.target and bool(candidates) and not client.failures and invalid == 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=int, default=500)
    parser.add_argument("--league", type=int, default=39, help="API-Football league ID (39: Premier League)")
    year = datetime.now(timezone.utc).year
    parser.add_argument("--seasons", type=int, nargs="+", default=[year - 2, year - 3, year - 4])
    args = parser.parse_args()
    if args.target < 500 or args.league < 1 or any(s < 1900 or s > year for s in args.seasons):
        parser.error("target must be at least 500; league must be positive; seasons must be between 1900 and this year")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    load_dotenv(ROOT / ".env")
    directory = ROOT / "data/raw" / datetime.now(timezone.utc).strftime("football_%Y%m%dT%H%M%S%fZ")
    directory.mkdir(parents=True)
    handler = logging.FileHandler(directory / "fetch.log", encoding="utf-8")
    LOG.addHandler(handler)
    client = Client(directory)
    summary = {"complete": False, "unique_matches": 0, "competition_records": 0, "invalid_records": 0}
    try:
        key = os.getenv("API_FOOTBALL_KEY", "").strip()
        if not key:
            client.fail("setup", "missing API_FOOTBALL_KEY in .env")
        else:
            summary.update(collect(client, key, args))
    finally:
        summary.update(target=args.target, league=args.league, seasons=args.seasons,
                       requests=client.requests, retries=client.retries,
                       failed_requests=len(client.failures), failures=client.failures)
        save(directory / "summary.json", summary)
        print(json.dumps(summary, indent=2))
        print(f"Saved to {directory}")
        client.session.close()
        LOG.removeHandler(handler)
        handler.close()
    return 0 if summary["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
