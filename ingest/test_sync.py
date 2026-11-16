"""Offline sync checks; no API requests or database connections."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import requests

from ingest.load import prepare_rows
from ingest.sync import FixtureClient, SyncError, request_plan, validate_payload


def reply(status=200, payload=None, headers=None):
    response = Mock(status_code=status, headers=headers or {})
    response.json.return_value = payload
    return response


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 16, tzinfo=timezone.utc)

    def test_first_run_and_weekly_reconciliation(self):
        params, full = request_plan(39, 2024, None, None, self.now)
        self.assertTrue(full)
        self.assertNotIn('from', params)
        state = (self.now - timedelta(days=1), self.now - timedelta(days=7))
        self.assertTrue(request_plan(39, 2024, state, None, self.now)[1])

    def test_future_fixture_cannot_skip_recent_matches(self):
        state = (self.now - timedelta(days=1), self.now - timedelta(days=1))
        params, full = request_plan(39, 2026, state, (self.now + timedelta(days=100)).date(), self.now)
        self.assertFalse(full)
        self.assertEqual(params['from'], '2026-11-08')

    def test_historical_tail_is_rechecked(self):
        state = (self.now, self.now)
        params, full = request_plan(39, 2024, state, datetime(2025, 5, 25).date(), self.now)
        self.assertEqual(params['from'], '2025-05-18')
        self.assertFalse(full)

    def test_incremental_empty_batch_is_valid_but_loader_still_requires_500(self):
        with tempfile.TemporaryDirectory() as folder:
            Path(folder, 'fixtures_empty.json').write_text(json.dumps({'response': []}))
            self.assertEqual(prepare_rows(Path(folder), 0), ([], [], []))
            with self.assertRaises(ValueError):
                prepare_rows(Path(folder))

    def test_incomplete_and_wrong_scope_responses_fail(self):
        payload = {'response': [], 'results': 0, 'paging': {'current': 1, 'total': 2}}
        with self.assertRaises(SyncError):
            validate_payload(payload, 39, 2024)
        payload.update(response=[{'league': {'id': 140, 'season': 2024}}], results=1,
                       paging={'current': 1, 'total': 1})
        with self.assertRaises(SyncError):
            validate_payload(payload, 39, 2024)

    @patch('ingest.sync.time.sleep')
    def test_transient_failures_retry_and_honor_retry_after(self, sleep):
        client = FixtureClient('fake-key')
        client.session = Mock()
        client.session.get.side_effect = [reply(429, headers={'Retry-After': '120'}),
                                          requests.Timeout('secret'), reply(503), reply(payload={'response': []})]
        self.assertEqual(client.get({}), {'response': []})
        sleep.assert_any_call(120.0)
        self.assertEqual(client.session.get.call_count, 4)
        self.assertFalse(client.session.get.call_args.kwargs['allow_redirects'])

    @patch('ingest.sync.time.sleep')
    def test_bounded_retries_and_safe_permanent_error(self, sleep):
        client = FixtureClient('fake-key')
        client.session = Mock()
        client.session.get.return_value = reply(500)
        with self.assertRaisesRegex(SyncError, 'five attempts'):
            client.get({})
        self.assertEqual(client.session.get.call_count, 5)
        client.session.get.return_value = reply(payload={'errors': {'token': 'secret'}})
        with self.assertRaises(SyncError) as result:
            client.get({})
        self.assertNotIn('secret', str(result.exception))


if __name__ == '__main__':
    unittest.main()
