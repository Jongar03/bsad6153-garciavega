r"""Check a direct API-Football key without printing credentials.

Run from the project folder: .venv\Scripts\python.exe scripts/check_football_api.py
"""

from pathlib import Path
import sys

from dotenv import dotenv_values
import requests


ROOT = Path(__file__).resolve().parents[1]
BASE = "https://v3.football.api-sports.io"
LEAGUES = {
    ("England", "Premier League"),
    ("Spain", "La Liga"),
    ("Germany", "Bundesliga"),
    ("Italy", "Serie A"),
    ("France", "Ligue 1"),
}


def main():
    key = (dotenv_values(ROOT / ".env").get("API_FOOTBALL_KEY") or "").strip()
    if not key:
        print("Add your direct API-Football key to API_FOOTBALL_KEY in .env first.")
        return 1

    with requests.Session() as session:
        session.headers.update({"x-apisports-key": key})
        responses = {}
        for endpoint in ("status", "leagues"):
            try:
                response = session.get(
                    f"{BASE}/{endpoint}", timeout=(10, 30), allow_redirects=False
                )
            except requests.RequestException:
                print(f"/{endpoint}: network request failed; details hidden.")
                return 1
            print(f"/{endpoint}: HTTP {response.status_code}")
            if response.status_code != 200:
                return 1
            try:
                payload = response.json()
            except ValueError:
                print("Invalid JSON response.")
                return 1
            if not isinstance(payload, dict) or payload.get("errors"):
                print("API reported an error; check your dashboard and plan limits.")
                return 1
            responses[endpoint] = payload.get("response")

    status = responses["status"]
    if not isinstance(status, dict):
        print("Unexpected account response.")
        return 1
    subscription = status.get("subscription") or {}
    if subscription.get("active") is not True:
        print("The API subscription is not active.")
        return 1
    print("Authentication succeeded; subscription is active.")

    leagues = responses["leagues"]
    if not isinstance(leagues, list):
        print("Unexpected league catalogue response.")
        return 1
    found = set()
    for item in leagues:
        league = item.get("league") or {}
        country = item.get("country") or {}
        identity = (country.get("name"), league.get("name"))
        if identity in LEAGUES:
            found.add(identity)
            print(f"Found: {identity[0]} - {identity[1]}")
    if found != LEAGUES:
        print("Not all five target leagues were found in the catalogue.")
        return 1
    print("Connection test passed for the account and five-league catalogue.")
    print("Season access, match statistics, and odds still need separate checks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
