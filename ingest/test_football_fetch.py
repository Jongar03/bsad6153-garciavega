"""Offline checks for retry, validation, and season-loop behavior."""
import argparse
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import requests
from ingest.fetch import Client, collect


def response(status=200, payload=None, headers=None):
    result = Mock(status_code=status, headers=headers or {})
    result.json.return_value = payload if payload is not None else {}
    return result


def match(i):
    return {"fixture": {"id": i, "date": "2024-01-01"},
            "league": {"id": 39, "name": "Premier League", "country": "England"}}


class FootballTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.client = Client(Path(self.temp.name))
        self.client.session = Mock()
        self.sleep = patch("ingest.fetch.time.sleep").start()

    def tearDown(self):
        patch.stopall()
        self.temp.cleanup()

    def test_retries_and_keeps_error_json(self):
        self.client.session.get.side_effect = [response(429, headers={"Retry-After": "120"}),
                                               requests.Timeout("secret"), response(503), response()]
        with self.assertLogs("fetch") as logs:
            self.assertEqual(self.client.get("https://example.test", {}, "test"), {})
        self.assertNotIn("secret", str(logs.output))
        self.sleep.assert_any_call(120.0)
        self.assertEqual(self.client.retries, 3)
        self.assertTrue((Path(self.temp.name) / "test_attempt1.json").exists())

    def test_retry_exhaustion_and_permanent_error(self):
        self.client.session.get.return_value = response(500)
        self.assertIsNone(self.client.get("https://example.test", {}, "test"))
        self.assertEqual(self.client.retries, 4)
        self.assertEqual(len(self.client.failures), 1)
        self.client.session.get.return_value = response(403)
        self.client.get("https://example.test", {}, "denied")
        self.assertEqual(self.client.requests, 6)

    def test_seasons_deduplicate_and_stop_at_target(self):
        competitions = {"competitions": [{"id": 2021, "name": "Premier League", "area": {"name": "England"}}]}
        def season(rows):
            return {"response": rows, "paging": {"current": 1, "total": 1}}
        self.client.session.get.side_effect = [response(payload=competitions),
            response(payload=season([match(i) for i in range(380)])),
            response(payload=season([match(i) for i in range(300, 760)] + [{}]))]
        result = collect(self.client, "fake-key", argparse.Namespace(league=39, seasons=[2024, 2023, 2022], target=500))
        self.assertEqual(result["unique_matches"], 760)
        self.assertEqual(result["duplicate_records"], 80)
        self.assertEqual(result["invalid_records"], 1)
        self.assertFalse(result["complete"])
        self.assertEqual(self.client.requests, 3)
        calls = self.client.session.get.call_args_list
        self.assertEqual(calls[0].kwargs["headers"], {})
        self.assertEqual(calls[1].kwargs["headers"], {"x-apisports-key": "fake-key"})
        self.assertNotIn("page", calls[1].kwargs["params"])
        candidates = json.loads((Path(self.temp.name) / "relationship_candidates.json").read_text())
        self.assertFalse(candidates[0]["confirmed"])

    def test_http_200_api_error_is_failure(self):
        self.client.session.get.return_value = response(payload={"errors": {"requests": "quota"}})
        self.assertIsNone(self.client.get("https://example.test", {}, "quota"))
        self.assertEqual(len(self.client.failures), 1)


if __name__ == "__main__":
    unittest.main()
