"""Offline checks for failures that a successful live call cannot exercise."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import requests

from ingest.fetch_comtrade import Client, months, retry_delay, valid_trade


def response(status=200, payload=None, headers=None):
    result = Mock(status_code=status, headers=headers or {})
    result.json.return_value = payload if payload is not None else {"data": []}
    return result


class FetchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.client = Client("test-key-only", Path(self.temp.name))
        self.client.session = Mock()
        self.sleep = patch("ingest.fetch.time.sleep").start()

    def tearDown(self):
        patch.stopall()
        self.temp.cleanup()

    def test_429_respects_retry_after_then_saves_raw(self):
        self.client.session.get.side_effect = [response(429, headers={"Retry-After": "7"}), response()]
        self.client.get("/test", {}, "page", authenticated=True)
        self.sleep.assert_any_call(7.0)
        self.assertEqual(self.client.retries, 1)
        self.assertEqual(json.loads((Path(self.temp.name) / "page.json").read_text()), {"data": []})
        self.assertEqual(self.client.session.get.call_args.kwargs["params"]["subscription-key"], "test-key-only")
        self.assertNotIn("test-key-only", (Path(self.temp.name) / "page.json").read_text())

    def test_timeout_and_server_error_recover_without_leaking_exception(self):
        self.client.session.get.side_effect = [requests.Timeout("secret-in-url"), response(503), response()]
        with self.assertLogs("fetch") as captured:
            self.assertEqual(self.client.get("/test", {}, "page"), {"data": []})
        self.assertNotIn("secret-in-url", " ".join(captured.output))
        self.assertEqual(self.client.retries, 2)

    def test_exhausted_retries_are_reported(self):
        self.client.session.get.return_value = response(500)
        self.assertIsNone(self.client.get("/test", {}, "page"))
        self.assertEqual(self.client.requests, 5)
        self.assertEqual(len(self.client.failures), 1)

    def test_auth_failure_stops_immediately(self):
        self.client.session.get.return_value = response(401)
        with self.assertRaises(RuntimeError):
            self.client.get("/test", {}, "page")
        self.assertEqual(self.client.requests, 1)

    def test_invalid_json_retries(self):
        bad = response()
        bad.json.side_effect = ValueError("bad JSON")
        self.client.session.get.side_effect = [bad, response()]
        self.assertEqual(self.client.get("/test", {}, "page"), {"data": []})
        self.assertEqual(self.client.retries, 1)

    def test_permanent_error_skips_without_retry(self):
        self.client.session.get.return_value = response(400)
        self.assertIsNone(self.client.get("/test", {}, "page"))
        self.assertEqual(self.client.requests, 1)
        self.assertEqual(len(self.client.failures), 1)

    def test_month_partitions_cross_year(self):
        self.assertEqual(months("202501", 3), ["202411", "202412", "202501"])

    def test_missing_fields_not_counted_and_retry_header_fallback(self):
        self.assertFalse(valid_trade({"primaryValue": 10}))
        self.assertFalse(valid_trade(None))
        self.assertEqual(retry_delay("bad header", 3), 8)


if __name__ == "__main__":
    unittest.main()
